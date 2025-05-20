from app.db.database import get_connection
from datetime import datetime

class Venta:
    @staticmethod
    def registrar(cliente, producto, cantidad, precio_unitario, iva):
        conn = get_connection()
        cur = conn.cursor()

        # Verificar stock
        cur.execute("SELECT stock FROM productos WHERE nombre = ?", (producto,))
        resultado = cur.fetchone()
        if not resultado or resultado[0] < cantidad:
            raise Exception("Stock insuficiente para realizar la venta.")

        # Calcular total
        subtotal = precio_unitario * cantidad
        total = subtotal + (subtotal * iva / 100)
        fecha = datetime.now().strftime("%Y-%m-%d")

        # Registrar la venta
        cur.execute("""
            INSERT INTO ordenes_venta (cliente, producto, cantidad, precio_unitario, iva, total, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cliente, producto, cantidad, precio_unitario, iva, total, fecha))

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
        cur.execute("SELECT * FROM ordenes_venta ORDER BY id DESC")
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def ultima_venta(producto):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM ordenes_venta
            WHERE producto = ?
            ORDER BY fecha DESC LIMIT 1
        """, (producto,))
        resultado = cur.fetchone()
        conn.close()
        return resultado
