# control_negocio/app/models/inventario.py
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Tuple, Optional, Any

from app.db.database import get_connection
# Si ya tienes IVA por producto como valor en tabla, lo mantenemos; estas constantes son para defaults.
from app.config.constantes import IVA_RATE  # opcional si quieres un default de IVA


Row = Tuple[Any, ...]


class Inventario:
    """
    Consultas y utilidades de inventario.
    Devuelve filas con las columnas esenciales del producto.
    """

    _SELECT_BASE = """
        SELECT
            id,
            nombre,
            categoria,
            codigo_interno,
            precio_compra,
            precio_venta,
            stock,
            iva,
            ubicacion,
            fecha_vencimiento
        FROM productos
    """

    # ---------------------------
    # Lecturas básicas
    # ---------------------------
    @staticmethod
    def listar_todo() -> List[Row]:
        """Lista todos los productos ordenados por nombre (insensible a mayúsculas)."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(Inventario._SELECT_BASE + " ORDER BY LOWER(nombre) ASC")
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def buscar_por_nombre(nombre: str) -> List[Row]:
        """Filtra por nombre (LIKE, case-insensitive)."""
        patron = f"%{(nombre or '').strip()}%"
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                Inventario._SELECT_BASE
                + " WHERE LOWER(nombre) LIKE LOWER(?) ORDER BY LOWER(nombre) ASC",
                (patron,),
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def buscar_por_codigo_interno(codigo: str) -> List[Row]:
        """Filtra por código interno (LIKE, case-insensitive)."""
        patron = f"%{(codigo or '').strip()}%"
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                Inventario._SELECT_BASE
                + " WHERE LOWER(codigo_interno) LIKE LOWER(?) ORDER BY LOWER(codigo_interno) ASC",
                (patron,),
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def buscar_por_categoria(categoria: str) -> List[Row]:
        """Filtra por categoría (LIKE, case-insensitive)."""
        patron = f"%{(categoria or '').strip()}%"
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                Inventario._SELECT_BASE
                + " WHERE LOWER(categoria) LIKE LOWER(?) ORDER BY LOWER(nombre) ASC",
                (patron,),
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def buscar_por_vencimiento(fecha_limite: str) -> List[Row]:
        """
        Productos con fecha_vencimiento <= fecha_limite (YYYY-MM-DD).
        Ignora NULLs (productos sin vencimiento).
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                Inventario._SELECT_BASE
                + " WHERE fecha_vencimiento IS NOT NULL AND date(fecha_vencimiento) <= date(?)"
                + " ORDER BY date(fecha_vencimiento) ASC, LOWER(nombre) ASC",
                (fecha_limite,),
            )
            return cur.fetchall()
        finally:
            conn.close()

    # ---------------------------
    # Utilidades de negocio
    # ---------------------------
    @staticmethod
    def por_vencer(dias: int = 30) -> List[Row]:
        """
        Productos que vencen dentro de 'dias' a partir de hoy (incluye hoy).
        Útil para mermas, alertas y rotación FEFO.
        """
        hoy = date.today()
        limite = (hoy + timedelta(days=int(dias))).isoformat()
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                Inventario._SELECT_BASE
                + " WHERE fecha_vencimiento IS NOT NULL"
                  " AND date(fecha_vencimiento) BETWEEN date(?) AND date(?)"
                + " ORDER BY date(fecha_vencimiento) ASC, LOWER(nombre) ASC",
                (hoy.isoformat(), limite),
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def bajo_stock(umbral: int = 5) -> List[Row]:
        """Productos con stock ≤ umbral."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                Inventario._SELECT_BASE
                + " WHERE stock <= ? ORDER BY stock ASC, LOWER(nombre) ASC",
                (int(umbral),),
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def sin_stock() -> List[Row]:
        """Productos agotados (stock = 0)."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                Inventario._SELECT_BASE
                + " WHERE stock = 0 ORDER BY LOWER(nombre) ASC"
            )
            return cur.fetchall()
        finally:
            conn.close()

    # ---------------------------
    # Mutaciones simples
    # ---------------------------
    @staticmethod
    def actualizar_ubicacion(id_producto: int, nueva_ubicacion: Optional[str]) -> None:
        """Actualiza la ubicación del producto."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE productos SET ubicacion = ? WHERE id = ?",
                ((nueva_ubicacion or "").strip() or None, int(id_producto)),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def actualizar_iva(id_producto: int, iva: Optional[float] = None) -> None:
        """
        Actualiza el IVA del producto. Si no se entrega 'iva', usa el default del sistema.
        Nota: el IVA aquí es 'tasa' por producto (p.ej., 0.19). Mantiene tu esquema actual.
        """
        tasa = float(IVA_RATE if iva is None else iva)
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE productos SET iva = ? WHERE id = ?",
                (tasa, int(id_producto)),
            )
            conn.commit()
        finally:
            conn.close()

    # ---------------------------
    # Paginación (para tablas grandes)
    # ---------------------------
    @staticmethod
    def listar_paginado(limit: int = 50, offset: int = 0) -> List[Row]:
        """Listado paginado para mejorar rendimiento en catálogos grandes."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                Inventario._SELECT_BASE
                + " ORDER BY LOWER(nombre) ASC LIMIT ? OFFSET ?",
                (int(limit), int(offset)),
            )
            return cur.fetchall()
        finally:
            conn.close()
