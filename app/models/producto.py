# control_negocio/app/models/producto.py
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Any

from app.db.database import get_connection
from app.config.constantes import IVA_RATE, MONETARY_DECIMALS

# ---------------------------------
# Helpers numéricos / sanitización
# ---------------------------------
_Q = Decimal(10) ** -MONETARY_DECIMALS  # p.ej. 0.01 si trabajas con 2 decimales


def _D(x: Any) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x if x is not None else 0))


def _round_money(x: Any) -> float:
    return float(_D(x).quantize(_Q, rounding=ROUND_HALF_UP))


def _norm_txt(x: Optional[str]) -> str:
    return (x or "").strip()


def _norm_date(x: Optional[str]) -> Optional[str]:
    """
    Acepta None o 'YYYY-MM-DD'. No convierte formatos; solo valida básico.
    """
    if not x:
        return None
    try:
        datetime.strptime(x, "%Y-%m-%d")
        return x
    except ValueError:
        # Si llega en formato inválido, lo almacena tal cual para no romper flujos legacy,
        # pero idealmente valida antes en la UI.
        return x


def _norm_iva(x: Any) -> float:
    """
    Normaliza IVA guardado en producto:
    - Si None → usa IVA_RATE de config.
    - Si 19 → se convierte a 0.19 (tasa).
    - Si 0.19 → se deja tal cual.
    """
    if x is None or x == "":
        return float(IVA_RATE if IVA_RATE <= 1 else IVA_RATE / 100.0)
    try:
        val = float(x)
    except Exception:
        return float(IVA_RATE if IVA_RATE <= 1 else IVA_RATE / 100.0)
    return float(val / 100.0) if val > 1 else float(val)


class Producto:
    # ---------------------------
    # ALTAS / EDICIONES / BORRADO
    # ---------------------------
    @staticmethod
    def crear(
        nombre: str,
        categoria: Optional[str],
        precio_compra: Any,
        precio_venta: Any,
        stock: Any,
        codigo_interno: Optional[str],
        codigo_externo: Optional[str],
        iva: Any,
        ubicacion: Optional[str],
        fecha_vencimiento: Optional[str],
    ) -> None:
        """
        Inserta un producto. Normaliza IVA, redondea montos y sanitiza textos.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO productos (
                    nombre, categoria, precio_compra, precio_venta, stock,
                    codigo_interno, codigo_externo, iva, ubicacion, fecha_vencimiento
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _norm_txt(nombre),
                    _norm_txt(categoria),
                    _round_money(precio_compra),
                    _round_money(precio_venta),
                    int(stock or 0),
                    _norm_txt(codigo_interno),
                    _norm_txt(codigo_externo),
                    _norm_iva(iva),
                    _norm_txt(ubicacion),
                    _norm_date(fecha_vencimiento),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def editar(
        id_producto: int,
        nombre: str,
        categoria: Optional[str],
        precio_compra: Any,
        precio_venta: Any,
        stock: Any,
        codigo_interno: Optional[str],
        codigo_externo: Optional[str],
        iva: Any,
        ubicacion: Optional[str],
        fecha_vencimiento: Optional[str],
    ) -> None:
        """
        Actualiza campos del producto. Mantiene compatibilidad con tu UI.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE productos SET
                    nombre = ?, categoria = ?, precio_compra = ?, precio_venta = ?, stock = ?,
                    codigo_interno = ?, codigo_externo = ?, iva = ?, ubicacion = ?, fecha_vencimiento = ?
                WHERE id = ?
                """,
                (
                    _norm_txt(nombre),
                    _norm_txt(categoria),
                    _round_money(precio_compra),
                    _round_money(precio_venta),
                    int(stock or 0),
                    _norm_txt(codigo_interno),
                    _norm_txt(codigo_externo),
                    _norm_iva(iva),
                    _norm_txt(ubicacion),
                    _norm_date(fecha_vencimiento),
                    int(id_producto),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def eliminar(id_producto: int) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM productos WHERE id = ?", (int(id_producto),))
            conn.commit()
        finally:
            conn.close()

    # ---------------------------
    # CONSULTAS
    # ---------------------------
    @staticmethod
    def listar_todos():
        """
        Devuelve todos los productos. Ordena por nombre para mejor UX.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    id, nombre, categoria, precio_compra, precio_venta, stock,
                    codigo_interno, codigo_externo, iva, ubicacion, fecha_vencimiento
                FROM productos
                ORDER BY nombre ASC
                """
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def buscar_por_nombre(nombre: str):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    id, nombre, categoria, precio_compra, precio_venta, stock,
                    codigo_interno, codigo_externo, iva, ubicacion, fecha_vencimiento
                FROM productos
                WHERE nombre LIKE ?
                ORDER BY nombre ASC
                """,
                (f"%{_norm_txt(nombre)}%",),
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def buscar_por_codigo(codigo: str):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    id, nombre, categoria, precio_compra, precio_venta, stock,
                    codigo_interno, codigo_externo, iva, ubicacion, fecha_vencimiento
                FROM productos
                WHERE codigo_interno LIKE ?
                ORDER BY codigo_interno ASC
                """,
                (f"%{_norm_txt(codigo)}%",),
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def buscar_por_categoria(categoria: str):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    id, nombre, categoria, precio_compra, precio_venta, stock,
                    codigo_interno, codigo_externo, iva, ubicacion, fecha_vencimiento
                FROM productos
                WHERE categoria LIKE ?
                ORDER BY nombre ASC
                """,
                (f"%{_norm_txt(categoria)}%",),
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def buscar_por_vencimiento(fecha_limite: str):
        """
        Filtra por fecha de vencimiento <= fecha_limite (YYYY-MM-DD).
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    id, nombre, categoria, precio_compra, precio_venta, stock,
                    codigo_interno, codigo_externo, iva, ubicacion, fecha_vencimiento
                FROM productos
                WHERE fecha_vencimiento IS NOT NULL
                  AND fecha_vencimiento <= ?
                ORDER BY fecha_vencimiento ASC, nombre ASC
                """,
                (_norm_date(fecha_limite),),
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def obtener_por_id(id_producto: int):
        """
        Helper útil para vistas/servicios que necesiten cargar un producto puntual.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    id, nombre, categoria, precio_compra, precio_venta, stock,
                    codigo_interno, codigo_externo, iva, ubicacion, fecha_vencimiento
                FROM productos
                WHERE id = ?
                """,
                (int(id_producto),),
            )
            return cur.fetchone()
        finally:
            conn.close()

    # ---------------------------
    # STOCK (helpers opcionales)
    # ---------------------------
    @staticmethod
    def ajustar_stock_por_nombre(nombre: str, delta: int) -> None:
        """
        Ajusta stock sumando delta (puede ser negativo).
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE productos SET stock = stock + ? WHERE nombre = ?",
                (int(delta), _norm_txt(nombre)),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def ajustar_stock_por_codigo(codigo_interno: str, delta: int) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE productos SET stock = stock + ? WHERE codigo_interno = ?",
                (int(delta), _norm_txt(codigo_interno)),
            )
            conn.commit()
        finally:
            conn.close()
