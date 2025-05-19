from app.db.database import get_connection

class Finanzas:

    # Ingresos
    @staticmethod
    def registrar_ingreso(descripcion, monto):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO ingresos (descripcion, monto) VALUES (?, ?)", (descripcion, monto))
        conn.commit()
        conn.close()

    # Gastos
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

    # Facturas
    @staticmethod
    def registrar_factura(numero, proveedor, monto, estado, fecha):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO facturas (numero, proveedor, monto, estado, fecha) VALUES (?, ?, ?, ?, ?)",
                    (numero, proveedor, monto, estado, fecha))
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

    # Estado de resultado
    @staticmethod
    def estado_resultado():
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT SUM(monto) FROM ingresos")
        total_ingresos = cur.fetchone()[0] or 0

        cur.execute("SELECT SUM(monto) FROM gastos")
        total_gastos = cur.fetchone()[0] or 0

        total_facturas = Finanzas.total_facturas_pagadas()
        conn.close()

        total_gastos_completo = total_gastos + total_facturas
        utilidad = total_ingresos - total_gastos_completo

        return total_ingresos, total_gastos_completo, utilidad

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
