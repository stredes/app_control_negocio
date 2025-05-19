# control_negocio/app/models/inventario.py

from app.db.database import get_connection

class Inventario:
    @staticmethod
    def listar_todo():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, categoria, precio_compra, precio_venta, stock
            FROM productos
            ORDER BY nombre ASC
        """)
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def buscar_por_nombre(nombre):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, categoria, precio_compra, precio_venta, stock
            FROM productos
            WHERE nombre LIKE ?
            ORDER BY nombre ASC
        """, (f"%{nombre}%",))
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def productos_bajo_stock(limite=5):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, categoria, stock
            FROM productos
            WHERE stock <= ?
        """, (limite,))
        resultados = cur.fetchall()
        conn.close()
        return resultados
