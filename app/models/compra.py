from app.db.database import get_connection
from datetime import date

class Compra:
    @staticmethod
    def registrar(proveedor, producto, cantidad, precio_unitario, iva=0.19):
        total = round((precio_unitario * cantidad) * (1 + iva), 2)
        fecha_actual = date.today().isoformat()

        conn = get_connection()
        cur = conn.cursor()

        # Registrar compra
        cur.execute("""
            INSERT INTO compras (
                proveedor, producto, cantidad,
                precio_unitario, iva, total, fecha
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (proveedor, producto, cantidad,
              precio_unitario, iva, total, fecha_actual))

        # Actualizar stock
        cur.execute("""
            UPDATE productos
            SET stock = stock + ?
            WHERE nombre = ?
        """, (cantidad, producto))

        conn.commit()
        conn.close()

    @staticmethod
    def obtener_por_id(id_compra):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM compras WHERE id = ?", (id_compra,))
        compra = cur.fetchone()
        conn.close()
        return compra

    @staticmethod
    def editar(id_compra, proveedor, producto, cantidad, precio_unitario, iva=0.19):
        total = round((precio_unitario * cantidad) * (1 + iva), 2)
        fecha_actual = date.today().isoformat()

        conn = get_connection()
        cur = conn.cursor()

        # Revertir stock viejo
        cur.execute("SELECT cantidad, producto FROM compras WHERE id = ?", (id_compra,))
        viejo = cur.fetchone()
        if viejo:
            antigua_cant, antiguo_prod = viejo
            cur.execute("""
                UPDATE productos
                SET stock = stock - ?
                WHERE nombre = ?
            """, (antigua_cant, antiguo_prod))

        # Actualizar compra
        cur.execute("""
            UPDATE compras SET
                proveedor = ?, producto = ?, cantidad = ?,
                precio_unitario = ?, iva = ?, total = ?, fecha = ?
            WHERE id = ?
        """, (proveedor, producto, cantidad,
              precio_unitario, iva, total, fecha_actual, id_compra))

        # Aplicar nuevo stock
        cur.execute("""
            UPDATE productos
            SET stock = stock + ?
            WHERE nombre = ?
        """, (cantidad, producto))

        conn.commit()
        conn.close()

    @staticmethod
    def eliminar(id_compra):
        conn = get_connection()
        cur = conn.cursor()

        # Devolver stock
        cur.execute("SELECT cantidad, producto FROM compras WHERE id = ?", (id_compra,))
        row = cur.fetchone()
        if row:
            cant, prod = row
            cur.execute("DELETE FROM compras WHERE id = ?", (id_compra,))
            cur.execute("""
                UPDATE productos
                SET stock = stock - ?
                WHERE nombre = ?
            """, (cant, prod))

        conn.commit()
        conn.close()

    @staticmethod
    def listar_todas():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proveedor, producto, cantidad,
                   precio_unitario, iva, total, fecha
            FROM compras
            ORDER BY id DESC
        """)
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def ultima_compra_producto(nombre_producto):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, proveedor, producto, cantidad,
                   precio_unitario, iva, total, fecha
            FROM compras
            WHERE producto = ?
            ORDER BY id DESC
            LIMIT 1
        """, (nombre_producto,))
        resultado = cur.fetchone()
        conn.close()
        return resultado
