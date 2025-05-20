from app.db.database import get_connection
from datetime import date

class Compra:
    @staticmethod
    def registrar(proveedor, producto, cantidad, precio_unitario, iva=0.19):
        """
        Registra una compra y actualiza el stock del producto.
        Calcula el total automáticamente.
        """
        total = round((precio_unitario * cantidad) * (1 + iva), 2)
        fecha_actual = str(date.today())

        conn = get_connection()
        cur = conn.cursor()

        # Registrar compra
        cur.execute("""
            INSERT INTO compras (proveedor, producto, cantidad, precio_unitario, iva, total)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (proveedor, producto, cantidad, precio_unitario, iva, total))

        # Actualizar stock
        cur.execute("""
            UPDATE productos SET stock = stock + ?
            WHERE nombre = ?
        """, (cantidad, producto))

        conn.commit()
        conn.close()

    @staticmethod
    def listar_todas():
        """
        Retorna todas las compras registradas.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM compras ORDER BY id DESC")
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def ultima_compra_producto(nombre_producto):
        """
        Devuelve la última compra registrada para un producto específico.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM compras
            WHERE producto = ?
            ORDER BY id DESC LIMIT 1
        """, (nombre_producto,))
        resultado = cur.fetchone()
        conn.close()
        return resultado
