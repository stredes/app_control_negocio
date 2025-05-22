# control_negocio/app/models/producto.py

from app.db.database import get_connection

class Producto:
    @staticmethod
    def crear(nombre, categoria, precio_compra, precio_venta, stock,
              codigo_interno, codigo_externo, iva, ubicacion, fecha_vencimiento):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO productos (
                nombre, categoria, precio_compra, precio_venta, stock,
                codigo_interno, codigo_externo, iva, ubicacion, fecha_vencimiento
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, categoria, precio_compra, precio_venta, stock,
              codigo_interno, codigo_externo, iva, ubicacion, fecha_vencimiento))
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
    def buscar_por_codigo(codigo):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM productos WHERE codigo_interno LIKE ?", (f"%{codigo}%",))
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def buscar_por_categoria(categoria):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM productos WHERE categoria LIKE ?", (f"%{categoria}%",))
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def buscar_por_vencimiento(fecha_limite):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM productos WHERE fecha_vencimiento <= ?", (fecha_limite,))
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

    @staticmethod
    def editar(id_producto, nombre, categoria, precio_compra, precio_venta, stock,
               codigo_interno, codigo_externo, iva, ubicacion, fecha_vencimiento):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE productos SET
                nombre = ?, categoria = ?, precio_compra = ?, precio_venta = ?, stock = ?,
                codigo_interno = ?, codigo_externo = ?, iva = ?, ubicacion = ?, fecha_vencimiento = ?
            WHERE id = ?
        """, (nombre, categoria, precio_compra, precio_venta, stock,
              codigo_interno, codigo_externo, iva, ubicacion, fecha_vencimiento, id_producto))
        conn.commit()
        conn.close()
