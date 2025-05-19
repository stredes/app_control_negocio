# control_negocio/app/models/venta.py

from app.db.database import get_connection

class Venta:
    @staticmethod
    def registrar(cliente, producto, cantidad, precio_unitario):
        conn = get_connection()
        cur = conn.cursor()

        # Validar stock
        cur.execute("SELECT stock FROM productos WHERE nombre = ?", (producto,))
        resultado = cur.fetchone()
        if not resultado or resultado[0] < cantidad:
            raise Exception("Stock insuficiente para realizar la venta.")

        # Insertar venta
        cur.execute("""
            INSERT INTO ventas (cliente, producto, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?)
        """, (cliente, producto, cantidad, precio_unitario))

        # Descontar stock
        cur.execute("""
            UPDATE productos SET stock = stock - ?
            WHERE nombre = ?
        """, (cantidad, producto))

        conn.commit()
        conn.close()

    @staticmethod
    def listar_todas():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM ventas ORDER BY id DESC")
        resultados = cur.fetchall()
        conn.close()
        return resultados
