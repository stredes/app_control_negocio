# control_negocio/app/models/compra.py

from app.db.database import get_connection

class Compra:
    @staticmethod
    def registrar(proveedor, producto, cantidad, precio_unitario):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO compras (proveedor, producto, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?)
        """, (proveedor, producto, cantidad, precio_unitario))

        # Actualizar stock del producto
        cur.execute("""
            UPDATE productos SET stock = stock + ?
            WHERE nombre = ?
        """, (cantidad, producto))

        conn.commit()
        conn.close()

    @staticmethod
    def listar_todas():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM compras ORDER BY id DESC")
        resultados = cur.fetchall()
        conn.close()
        return resultados
