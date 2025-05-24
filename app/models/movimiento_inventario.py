from app.db.database import get_connection

class MovimientoInventario:
    @staticmethod
    def listar_todo():
        """
        Lista todos los movimientos de inventario (entradas y salidas),
        ordenados de más recientes a más antiguos.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id,
                codigo_producto,
                tipo,
                cantidad,
                ubicacion,
                metodo,
                fecha
            FROM movimientos_inventario
            ORDER BY fecha DESC, id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def filtrar_por_codigo(codigo):
        """
        Filtra movimientos cuyo código de producto contenga la cadena dada.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, codigo_producto, tipo, cantidad, ubicacion, metodo, fecha
            FROM movimientos_inventario
            WHERE codigo_producto LIKE ?
            ORDER BY fecha DESC, id DESC
        """, (f"%{codigo}%",))
        rows = cur.fetchall()
        conn.close()
        return rows
