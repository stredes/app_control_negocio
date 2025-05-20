# control_negocio/app/models/ingreso_inventario.py

from app.db.database import get_connection
from datetime import datetime

class IngresoInventario:
    @staticmethod
    def registrar(producto_codigo, cantidad, ubicacion, metodo="manual"):
        conn = get_connection()
        cur = conn.cursor()

        # Actualizar stock del producto
        cur.execute("""
            UPDATE productos SET stock = stock + ?
            WHERE codigo_interno = ?
        """, (cantidad, producto_codigo))

        # Registrar movimiento de entrada
        cur.execute("""
            INSERT INTO movimientos_inventario (codigo_producto, tipo, cantidad, ubicacion, metodo, fecha)
            VALUES (?, 'entrada', ?, ?, ?, ?)
        """, (producto_codigo, cantidad, ubicacion, metodo, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        conn.close()

    @staticmethod
    def listar_entradas():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM movimientos_inventario WHERE tipo = 'entrada' ORDER BY fecha DESC")
        entradas = cur.fetchall()
        conn.close()
        return entradas
