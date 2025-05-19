# control_negocio/app/models/producto.py

from app.db.database import get_connection

class Producto:
    @staticmethod
    def crear(nombre, categoria, precio_compra, precio_venta, stock):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO productos (nombre, categoria, precio_compra, precio_venta, stock)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, categoria, precio_compra, precio_venta, stock))
        conn.commit()
        conn.close()

    @staticmethod
    def listar_todos():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM productos")
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def buscar_por_nombre(nombre):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM productos WHERE nombre LIKE ?", (f"%{nombre}%",))
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def eliminar(id_producto):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM productos WHERE id = ?", (id_producto,))
        conn.commit()
        conn.close()
