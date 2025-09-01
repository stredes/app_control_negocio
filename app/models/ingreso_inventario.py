# control_negocio/app/models/ingreso_inventario.py
from __future__ import annotations

from datetime import datetime
from typing import List, Tuple, Any

from app.db.database import get_connection


class IngresoInventario:
    """
    Registro de entradas de inventario.
    - Actualiza stock del producto.
    - Guarda movimiento en tabla movimientos_inventario.
    """

    @staticmethod
    def registrar(producto_codigo: str, cantidad: int, ubicacion: str, metodo: str = "manual") -> None:
        """
        Registra un ingreso de inventario:
        - Verifica que la cantidad sea válida (>0).
        - Aumenta el stock del producto con `codigo_interno = producto_codigo`.
        - Inserta un movimiento en movimientos_inventario.
        """
        if not producto_codigo or not isinstance(producto_codigo, str):
            raise ValueError("Código de producto inválido.")
        if cantidad <= 0:
            raise ValueError("Cantidad debe ser mayor a 0.")

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            # Verificar existencia del producto
            cur.execute("SELECT stock FROM productos WHERE codigo_interno = ?", (producto_codigo,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Producto con código interno '{producto_codigo}' no existe.")

            # Actualizar stock
            cur.execute(
                """
                UPDATE productos
                SET stock = stock + ?
                WHERE codigo_interno = ?
                """,
                (cantidad, producto_codigo),
            )

            # Registrar movimiento
            cur.execute(
                """
                INSERT INTO movimientos_inventario (
                    codigo_producto, tipo, cantidad, ubicacion, metodo, fecha
                ) VALUES (?, 'entrada', ?, ?, ?, ?)
                """,
                (
                    producto_codigo,
                    cantidad,
                    ubicacion.strip() if ubicacion else None,
                    metodo.strip(),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def listar_entradas() -> List[Tuple[Any, ...]]:
        """
        Retorna todos los movimientos de entrada de inventario, ordenados del más reciente al más antiguo.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, codigo_producto, cantidad, ubicacion, metodo, fecha
                FROM movimientos_inventario
                WHERE tipo = 'entrada'
                ORDER BY datetime(fecha) DESC
                """
            )
            return cur.fetchall()
        finally:
            conn.close()
