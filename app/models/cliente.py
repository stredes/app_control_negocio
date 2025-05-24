# control_negocio/app/models/cliente.py

from app.db.database import get_connection

class Cliente:
    @staticmethod
    def crear(nombre, rut, direccion, telefono):
        """
        Inserta un nuevo cliente en la base de datos.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO clientes (nombre, rut, direccion, telefono)
            VALUES (?, ?, ?, ?)
        """, (nombre.strip(), rut.strip(), direccion.strip(), telefono.strip()))
        conn.commit()
        conn.close()

    @staticmethod
    def editar(id_cliente, nombre, rut, direccion, telefono):
        """
        Actualiza los datos de un cliente existente.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE clientes SET
                nombre = ?, rut = ?, direccion = ?, telefono = ?
            WHERE id = ?
        """, (nombre.strip(), rut.strip(), direccion.strip(), telefono.strip(), id_cliente))
        conn.commit()
        conn.close()

    @staticmethod
    def listar_todos():
        """
        Devuelve todos los clientes, ordenados por nombre.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, rut, direccion, telefono
            FROM clientes
            ORDER BY nombre ASC
        """)
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def buscar_por_nombre(nombre):
        """
        Filtra clientes cuyo nombre contenga la cadena proporcionada.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, rut, direccion, telefono
            FROM clientes
            WHERE nombre LIKE ?
            ORDER BY nombre ASC
        """, (f"%{nombre.strip()}%",))
        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def eliminar(id_cliente):
        """
        Elimina el cliente con el ID especificado.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM clientes WHERE id = ?", (id_cliente,))
        conn.commit()
        conn.close()
