# control_negocio/app/models/cliente.py

from app.db.database import get_connection

class Cliente:
    @staticmethod
    def crear(nombre, rut, direccion, telefono):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO clientes (nombre, rut, direccion, telefono)
            VALUES (?, ?, ?, ?)
        """, (nombre, rut, direccion, telefono))
        conn.commit()
        conn.close()

    @staticmethod
    def listar_todos():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM clientes")
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def buscar_por_nombre(nombre):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM clientes WHERE nombre LIKE ?", (f"%{nombre}%",))
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def eliminar(id_cliente):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM clientes WHERE id = ?", (id_cliente,))
        conn.commit()
        conn.close()
