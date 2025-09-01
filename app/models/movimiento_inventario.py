# control_negocio/app/models/movimiento_inventario.py
from __future__ import annotations

from typing import List, Tuple, Optional
from app.db.database import get_connection

Row = Tuple[int, str, str, int, Optional[str], Optional[str], str]


class MovimientoInventario:
    """
    Registro de movimientos de inventario (entradas y salidas).
    """

    _SELECT_BASE = """
        SELECT
            id,
            codigo_producto,
            tipo,
            cantidad,
            ubicacion,
            metodo,
            fecha
        FROM movimientos_inventario
    """

    # ---------------------------
    # Altas
    # ---------------------------
    @staticmethod
    def registrar(
        codigo_producto: str,
        tipo: str,
        cantidad: int,
        ubicacion: Optional[str] = None,
        metodo: Optional[str] = "manual",
        fecha: Optional[str] = None,  # ISO "YYYY-MM-DD HH:MM:SS"
    ) -> int:
        """
        Inserta un movimiento en el inventario.
        - tipo: 'entrada' | 'salida'
        - cantidad: positiva (no se permiten negativas aquí)
        """
        if tipo not in ("entrada", "salida"):
            raise ValueError("tipo debe ser 'entrada' o 'salida'")
        if cantidad <= 0:
            raise ValueError("cantidad debe ser > 0")

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO movimientos_inventario
                    (codigo_producto, tipo, cantidad, ubicacion, metodo, fecha)
                VALUES (?, ?, ?, ?, ?, COALESCE(?, datetime('now')))
                """,
                (codigo_producto.strip(), tipo, int(cantidad),
                 (ubicacion or "").strip() or None,
                 (metodo or "").strip() or None,
                 fecha),
            )
            new_id = cur.lastrowid
            conn.commit()
            return int(new_id)
        finally:
            conn.close()

    # ---------------------------
    # Consultas
    # ---------------------------
    @staticmethod
    def listar_todo() -> List[Row]:
        """Lista todos los movimientos, más recientes primero."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(MovimientoInventario._SELECT_BASE + " ORDER BY date(fecha) DESC, id DESC")
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def listar_paginado(limit: int = 50, offset: int = 0) -> List[Row]:
        """Listado paginado para grandes volúmenes."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                MovimientoInventario._SELECT_BASE
                + " ORDER BY date(fecha) DESC, id DESC LIMIT ? OFFSET ?",
                (int(limit), int(offset)),
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def filtrar_por_codigo(codigo: str) -> List[Row]:
        """Filtra por código de producto (case-insensitive)."""
        patron = f"%{(codigo or '').strip()}%"
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                MovimientoInventario._SELECT_BASE
                + " WHERE LOWER(codigo_producto) LIKE LOWER(?)"
                + " ORDER BY date(fecha) DESC, id DESC",
                (patron,),
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def filtrar_por_tipo(tipo: str) -> List[Row]:
        """Filtra por tipo de movimiento: 'entrada' o 'salida'."""
        if tipo not in ("entrada", "salida"):
            raise ValueError("tipo debe ser 'entrada' o 'salida'")
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                MovimientoInventario._SELECT_BASE
                + " WHERE tipo = ? ORDER BY date(fecha) DESC, id DESC",
                (tipo,),
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def filtrar_por_rango_fechas(desde: str, hasta: str) -> List[Row]:
        """
        Filtra movimientos entre 2 fechas (incluye extremos).
        - Fechas en formato ISO 'YYYY-MM-DD'
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                MovimientoInventario._SELECT_BASE
                + " WHERE date(fecha) BETWEEN date(?) AND date(?)"
                + " ORDER BY date(fecha) DESC, id DESC",
                (desde, hasta),
            )
            return cur.fetchall()
        finally:
            conn.close()
