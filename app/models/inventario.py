from app.db.database import get_connection

class Inventario:
    @staticmethod
    def listar_todo():
        """
        Lista todos los productos con sus datos esenciales.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id,
                nombre,
                categoria,
                codigo_interno,
                precio_compra,
                precio_venta,
                stock,
                iva,
                ubicacion,
                fecha_vencimiento
            FROM productos
            ORDER BY nombre ASC
        """)
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def buscar_por_nombre(nombre):
        """
        Filtra productos cuyo nombre contenga el texto dado.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id,
                nombre,
                categoria,
                codigo_interno,
                precio_compra,
                precio_venta,
                stock,
                iva,
                ubicacion,
                fecha_vencimiento
            FROM productos
            WHERE nombre LIKE ?
            ORDER BY nombre ASC
        """, (f"%{nombre}%",))
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def buscar_por_codigo_interno(codigo):
        """
        Filtra productos cuyo código interno contenga el texto dado.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id,
                nombre,
                categoria,
                codigo_interno,
                precio_compra,
                precio_venta,
                stock,
                iva,
                ubicacion,
                fecha_vencimiento
            FROM productos
            WHERE codigo_interno LIKE ?
            ORDER BY codigo_interno ASC
        """, (f"%{codigo}%",))
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def buscar_por_categoria(categoria):
        """
        Filtra productos cuya categoría contenga el texto dado.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id,
                nombre,
                categoria,
                codigo_interno,
                precio_compra,
                precio_venta,
                stock,
                iva,
                ubicacion,
                fecha_vencimiento
            FROM productos
            WHERE categoria LIKE ?
            ORDER BY nombre ASC
        """, (f"%{categoria}%",))
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def buscar_por_vencimiento(fecha_limite):
        """
        Filtra productos cuya fecha de vencimiento sea anterior o igual
        a la fecha límite (formato 'YYYY-MM-DD').
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id,
                nombre,
                categoria,
                codigo_interno,
                precio_compra,
                precio_venta,
                stock,
                iva,
                ubicacion,
                fecha_vencimiento
            FROM productos
            WHERE fecha_vencimiento <= ?
            ORDER BY fecha_vencimiento ASC
        """, (fecha_limite,))
        resultados = cur.fetchall()
        conn.close()
        return resultados
