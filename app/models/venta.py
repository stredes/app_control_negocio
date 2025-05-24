from app.db.database import get_connection
from datetime import datetime

class Venta:
    @staticmethod
    def registrar(cliente, producto, cantidad, precio_unitario, iva):
        """
        Registra una venta, descuenta del stock del producto y asigna la fecha actual.
        Calcula el total automáticamente.
        """
        conn = get_connection()
        cur = conn.cursor()

        # Verificar stock disponible
        cur.execute("SELECT stock FROM productos WHERE nombre = ?", (producto,))
        fila = cur.fetchone()
        if not fila:
            conn.close()
            raise ValueError(f"Producto '{producto}' no existe.")
        stock_actual = fila[0]
        if cantidad > stock_actual:
            conn.close()
            raise ValueError(f"Stock insuficiente ({stock_actual}) para '{producto}'.")

        # Calcular totales
        subtotal = precio_unitario * cantidad
        total = round(subtotal * (1 + iva/100), 2)
        fecha = datetime.now().strftime("%Y-%m-%d")

        # Insertar orden de venta con fecha
        cur.execute(
            """
            INSERT INTO ordenes_venta (
                cliente, producto, cantidad,
                precio_unitario, iva, total, fecha
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (cliente, producto, cantidad, precio_unitario, iva, total, fecha)
        )

        # Descontar stock del producto
        cur.execute(
            """
            UPDATE productos
            SET stock = stock - ?
            WHERE nombre = ?
            """,
            (cantidad, producto)
        )

        conn.commit()
        conn.close()

    @staticmethod
    def listar_todas():
        """
        Retorna todas las ventas registradas, ordenadas de más reciente a más antigua.
        Incluye el campo fecha.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, cliente, producto, cantidad,
                   precio_unitario, iva, total, fecha
            FROM ordenes_venta
            ORDER BY id DESC
            """
        )
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def ultima_venta_producto(nombre_producto):
        """
        Devuelve la última venta registrada para un producto específico, con fecha.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, cliente, producto, cantidad,
                   precio_unitario, iva, total, fecha
            FROM ordenes_venta
            WHERE producto = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (nombre_producto,)
        )
        resultado = cur.fetchone()
        conn.close()
        return resultado

    @staticmethod
    def eliminar(id_venta):
        """
        Elimina una venta y repone el stock del producto vendido.
        """
        conn = get_connection()
        cur = conn.cursor()

        # Obtener datos de la venta
        cur.execute("SELECT producto, cantidad FROM ordenes_venta WHERE id = ?", (id_venta,))
        fila = cur.fetchone()
        if not fila:
            conn.close()
            raise ValueError(f"Venta con ID {id_venta} no encontrada.")
        producto, cantidad = fila

        # Borrar la venta
        cur.execute("DELETE FROM ordenes_venta WHERE id = ?", (id_venta,))

        # Reponer stock en productos
        cur.execute(
            """
            UPDATE productos
            SET stock = stock + ?
            WHERE nombre = ?
            """,
            (cantidad, producto)
        )

        conn.commit()
        conn.close()