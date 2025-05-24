# control_negocio/app/models/factura.py

from app.db.database import get_connection
from datetime import date

class Factura:
    @staticmethod
    def crear(numero, tercero, monto, tipo, fecha=None):
        """
        Crea una factura con estado inicial 'emitida'.
        tipo ∈ {'cliente', 'proveedor'}.
        """
        fecha = fecha or date.today().isoformat()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO facturas
                (numero, proveedor, monto, estado, fecha, tipo)
            VALUES (?, ?, ?, 'emitida', ?, ?)
        """, (numero.strip(), tercero.strip(), monto, fecha, tipo))
        conn.commit()
        conn.close()

    @staticmethod
    def listar_por_tipo_y_estado(tipo, estados):
        """
        Devuelve facturas de un tipo cuyo estado esté en la lista `estados`.
        """
        conn = get_connection()
        cur = conn.cursor()
        # construye placeholders: "?,?" etc.
        ph = ",".join("?" for _ in estados)
        sql = f"""
            SELECT id, numero, proveedor, monto, estado, fecha
            FROM facturas
            WHERE tipo = ? AND estado IN ({ph})
            ORDER BY fecha DESC
        """
        cur.execute(sql, [tipo, *estados])
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def cambiar_estado(id_factura, nuevo_estado):
        """
        Cambia el campo 'estado' de la factura seleccionada.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE facturas SET estado = ? WHERE id = ?", (nuevo_estado, id_factura))
        conn.commit()
        conn.close()
