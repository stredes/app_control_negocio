# control_negocio/app/models/finanzas.py

from app.db.database import get_connection

class Finanzas:
    @staticmethod
    def registrar_ingreso(descripcion, monto):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO ingresos (descripcion, monto) VALUES (?, ?)", (descripcion, monto))
        conn.commit()
        conn.close()

    @staticmethod
    def registrar_gasto(descripcion, monto):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO gastos (descripcion, monto) VALUES (?, ?)", (descripcion, monto))
        conn.commit()
        conn.close()

    @staticmethod
    def listar_ingresos():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM ingresos")
        datos = cur.fetchall()
        conn.close()
        return datos

    @staticmethod
    def listar_gastos():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM gastos")
        datos = cur.fetchall()
        conn.close()
        return datos

    @staticmethod
    def estado_resultado():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT SUM(monto) FROM ingresos")
        total_ingresos = cur.fetchone()[0] or 0

        cur.execute("SELECT SUM(monto) FROM gastos")
        total_gastos = cur.fetchone()[0] or 0

        conn.close()
        return total_ingresos, total_gastos, total_ingresos - total_gastos
