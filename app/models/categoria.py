# control_negocio/app/models/categoria.py

from app.db.database import get_connection

class Categoria:
    @staticmethod
    def listar():
        """
        Devuelve lista de tuplas (id, nombre).
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
        datos = cur.fetchall()
        conn.close()
        return datos

    @staticmethod
    def agregar(nombre):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre.strip(),))
        conn.commit()
        conn.close()

    @staticmethod
    def eliminar(id_categoria):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM categorias WHERE id = ?", (id_categoria,))
        conn.commit()
        conn.close()

    @staticmethod
    def editar(id_categoria, nuevo_nombre):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE categorias SET nombre = ? WHERE id = ?", (nuevo_nombre.strip(), id_categoria))
        conn.commit()
        conn.close()
