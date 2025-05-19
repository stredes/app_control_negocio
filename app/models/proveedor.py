# control_negocio/app/models/proveedor.py

from app.db.database import get_connection

class Proveedor:
    @staticmethod
    def crear(nombre, rut, direccion, telefono):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO proveedores (nombre, rut, direccion, telefono)
            VALUES (?, ?, ?, ?)
        """, (nombre, rut, direccion, telefono))
        conn.commit()
        conn.close()

    @staticmethod
    def listar_todos():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM proveedores")
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def buscar_por_nombre(nombre):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM proveedores WHERE nombre LIKE ?", (f"%{nombre}%",))
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def eliminar(id_proveedor):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM proveedores WHERE id = ?", (id_proveedor,))
        conn.commit()
        conn.close()
