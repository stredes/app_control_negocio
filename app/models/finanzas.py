# control_negocio/app/models/finanzas.py

from app.db.database import get_connection
from datetime import date

class Finanzas:

    # ------------------------------
    # INGRESOS
    # ------------------------------
    @staticmethod
    def registrar_ingreso(nombre, descripcion, monto, estado="pendiente", fecha=None):
        fecha = fecha or str(date.today())
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO ingresos (nombre, descripcion, monto, estado, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, descripcion, monto, estado, fecha))
        conn.commit()
        conn.close()

    @staticmethod
    def listar_ingresos():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM ingresos ORDER BY fecha DESC")
        datos = cur.fetchall()
        conn.close()
        return datos

    # ------------------------------
    # GASTOS
    # ------------------------------
    @staticmethod
    def registrar_gasto(nombre, descripcion, monto, estado="pendiente", fecha=None):
        fecha = fecha or str(date.today())
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO gastos (nombre, descripcion, monto, estado, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, descripcion, monto, estado, fecha))
        conn.commit()
        conn.close()

    @staticmethod
    def listar_gastos():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM gastos ORDER BY fecha DESC")
        datos = cur.fetchall()
        conn.close()
        return datos

    # ------------------------------
    # FACTURAS
    # ------------------------------
    @staticmethod
    def registrar_factura(numero, proveedor, monto, estado, fecha, tipo):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO facturas (numero, proveedor, monto, estado, fecha, tipo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (numero, proveedor, monto, estado, fecha, tipo))
        conn.commit()
        conn.close()

    @staticmethod
    def listar_facturas():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM facturas ORDER BY fecha DESC")
        datos = cur.fetchall()
        conn.close()
        return datos

    @staticmethod
    def cambiar_estado_factura(id_factura, nuevo_estado):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE facturas SET estado = ? WHERE id = ?", (nuevo_estado, id_factura))
        conn.commit()
        conn.close()

    @staticmethod
    def total_facturas_pagadas():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT SUM(monto) FROM facturas WHERE estado = 'pagada'")
        total = cur.fetchone()[0] or 0
        conn.close()
        return total

    # ------------------------------
    # ESTADO DE RESULTADOS
    # ------------------------------
    @staticmethod
    def estado_resultado():
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT SUM(monto) FROM ingresos WHERE estado = 'recibido'")
        total_ingresos = cur.fetchone()[0] or 0

        cur.execute("SELECT SUM(monto) FROM gastos WHERE estado = 'pagado'")
        total_gastos = cur.fetchone()[0] or 0

        total_facturas = Finanzas.total_facturas_pagadas()
        conn.close()

        total_gastos_completo = total_gastos + total_facturas
        utilidad = total_ingresos - total_gastos_completo

        return total_ingresos, total_gastos_completo, utilidad
