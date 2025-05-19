from app.db.database import get_connection

class Categoria:
    @staticmethod
    def listar():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM categorias")
        datos = cur.fetchall()
        conn.close()
        return datos

    @staticmethod
    def agregar(nombre):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
        conn.commit()
        conn.close()

    @staticmethod
    def eliminar(id_categoria):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM categorias WHERE id = ?", (id_categoria,))
        conn.commit()
        conn.close()
