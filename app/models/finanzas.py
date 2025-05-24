# control_negocio/app/models/finanzas.py

from app.db.database import get_connection
from datetime import date

class Finanzas:

    # ------------------------------
    # INGRESOS
    # ------------------------------
    @staticmethod
    def registrar_ingreso(nombre, descripcion, monto, estado="pendiente", fecha=None):
        fecha = fecha or date.today().isoformat()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO ingresos (nombre, descripcion, monto, estado, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre.strip(), descripcion.strip(), monto, estado.strip(), fecha))
        conn.commit()
        conn.close()

    @staticmethod
    def listar_ingresos():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, descripcion, monto, estado, fecha FROM ingresos ORDER BY fecha DESC")
        datos = cur.fetchall()
        conn.close()
        return datos

    @staticmethod
    def editar_ingreso(id_ingreso, nombre, descripcion, monto, estado, fecha):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE ingresos
            SET nombre = ?, descripcion = ?, monto = ?, estado = ?, fecha = ?
            WHERE id = ?
        """, (nombre.strip(), descripcion.strip(), monto, estado.strip(), fecha.strip(), id_ingreso))
        conn.commit()
        conn.close()

    @staticmethod
    def eliminar_ingreso(id_ingreso):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM ingresos WHERE id = ?", (id_ingreso,))
        conn.commit()
        conn.close()


    # ------------------------------
    # GASTOS
    # ------------------------------
    @staticmethod
    def registrar_gasto(nombre, descripcion, monto, estado="pendiente", fecha=None):
        fecha = fecha or date.today().isoformat()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO gastos (nombre, descripcion, monto, estado, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre.strip(), descripcion.strip(), monto, estado.strip(), fecha))
        conn.commit()
        conn.close()

    @staticmethod
    def listar_gastos():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, descripcion, monto, estado, fecha FROM gastos ORDER BY fecha DESC")
        datos = cur.fetchall()
        conn.close()
        return datos

    @staticmethod
    def editar_gasto(id_gasto, nombre, descripcion, monto, estado, fecha):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE gastos
            SET nombre = ?, descripcion = ?, monto = ?, estado = ?, fecha = ?
            WHERE id = ?
        """, (nombre.strip(), descripcion.strip(), monto, estado.strip(), fecha.strip(), id_gasto))
        conn.commit()
        conn.close()

    @staticmethod
    def eliminar_gasto(id_gasto):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM gastos WHERE id = ?", (id_gasto,))
        conn.commit()
        conn.close()


    # ------------------------------
    # FACTURAS
    # ------------------------------
    @staticmethod
    def registrar_factura(numero, tercero, monto, estado, fecha, tipo):
        """
        Inserta una factura (cliente o proveedor).
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO facturas (numero, proveedor, monto, estado, fecha, tipo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (numero.strip(), tercero.strip(), monto, estado.strip(), fecha, tipo.strip()))
        conn.commit()
        conn.close()

    @staticmethod
    def listar_facturas():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, numero, proveedor, monto, estado, fecha, tipo FROM facturas ORDER BY fecha DESC")
        datos = cur.fetchall()
        conn.close()
        return datos

    @staticmethod
    def cambiar_estado_factura(id_factura, nuevo_estado):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE facturas SET estado = ? WHERE id = ?", (nuevo_estado.strip(), id_factura))
        conn.commit()
        conn.close()

    @staticmethod
    def editar_factura(id_factura, numero, tercero, monto, estado, fecha, tipo):
        """
        Actualiza todos los campos de una factura existente.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE facturas
            SET numero = ?, proveedor = ?, monto = ?, estado = ?, fecha = ?, tipo = ?
            WHERE id = ?
        """, (numero.strip(), tercero.strip(), monto, estado.strip(), fecha, tipo.strip(), id_factura))
        conn.commit()
        conn.close()

    @staticmethod
    def eliminar_factura(id_factura):
        """
        Elimina una factura por su ID.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM facturas WHERE id = ?", (id_factura,))
        conn.commit()
        conn.close()


    # ------------------------------
    # REPORTES
    # ------------------------------
    @staticmethod
    def total_facturas_pagadas():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT SUM(monto) FROM facturas WHERE estado = 'pagada'")
        total = cur.fetchone()[0] or 0
        conn.close()
        return total

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

        # Gastos completos incluyen facturas de proveedor pagadas
        cur2 = get_connection().cursor()
        cur2.execute("SELECT SUM(monto) FROM facturas WHERE estado = 'pagada' AND tipo = 'proveedor'")
        total_fact_prov = cur2.fetchone()[0] or 0
        cur2.connection.close()

        total_gastos_completo = total_gastos + total_fact_prov
        utilidad = total_ingresos - total_gastos_completo

        return total_ingresos, total_gastos_completo, utilidad
