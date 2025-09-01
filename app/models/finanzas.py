# app/models/finanzas.py
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Tuple

from app.db.database import get_connection
from app.models.factura import Factura
from app.config.constantes import (
    MONETARY_DECIMALS,
)

# ------------------------------
# Utilidades monetarias
# ------------------------------
Q = Decimal(10) ** -MONETARY_DECIMALS  # p.ej. 0.01


def _D(x: Any) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x or 0))


def _round(x: Any) -> float:
    """Redondeo HALF_UP según decimales monetarios, retornando float para compatibilidad UI."""
    return float(_D(x).quantize(Q, rounding=ROUND_HALF_UP))


# ======================================================================
#                           M Ó D U L O   F I N A N Z A S
# ======================================================================
class Finanzas:
    # ------------------------------------------------------------------
    # INGRESOS
    # ------------------------------------------------------------------
    @staticmethod
    def registrar_ingreso(nombre: str, descripcion: str, monto: float, estado: str = "pendiente", fecha: str | None = None) -> None:
        """
        Inserta un ingreso. 'monto' se almacena con redondeo monetario.
        estado sugerido: 'pendiente' | 'recibido'
        """
        fecha = fecha or date.today().isoformat()
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO ingresos (nombre, descripcion, monto, estado, fecha)
                VALUES (?, ?, ?, ?, ?)
                """,
                (nombre.strip(), descripcion.strip(), _round(monto), estado.strip(), fecha),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def listar_ingresos():
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, nombre, descripcion, monto, estado, fecha FROM ingresos ORDER BY date(fecha) DESC, id DESC"
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def editar_ingreso(id_ingreso: int, nombre: str, descripcion: str, monto: float, estado: str, fecha: str) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE ingresos
                SET nombre = ?, descripcion = ?, monto = ?, estado = ?, fecha = ?
                WHERE id = ?
                """,
                (nombre.strip(), descripcion.strip(), _round(monto), estado.strip(), fecha.strip(), id_ingreso),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def eliminar_ingreso(id_ingreso: int) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM ingresos WHERE id = ?", (id_ingreso,))
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # GASTOS
    # ------------------------------------------------------------------
    @staticmethod
    def registrar_gasto(nombre: str, descripcion: str, monto: float, estado: str = "pendiente", fecha: str | None = None) -> None:
        """
        Inserta un gasto. 'monto' con redondeo monetario.
        estado sugerido: 'pendiente' | 'pagado'
        """
        fecha = fecha or date.today().isoformat()
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO gastos (nombre, descripcion, monto, estado, fecha)
                VALUES (?, ?, ?, ?, ?)
                """,
                (nombre.strip(), descripcion.strip(), _round(monto), estado.strip(), fecha),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def listar_gastos():
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, nombre, descripcion, monto, estado, fecha FROM gastos ORDER BY date(fecha) DESC, id DESC"
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def editar_gasto(id_gasto: int, nombre: str, descripcion: str, monto: float, estado: str, fecha: str) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE gastos
                SET nombre = ?, descripcion = ?, monto = ?, estado = ?, fecha = ?
                WHERE id = ?
                """,
                (nombre.strip(), descripcion.strip(), _round(monto), estado.strip(), fecha.strip(), id_gasto),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def eliminar_gasto(id_gasto: int) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM gastos WHERE id = ?", (id_gasto,))
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # FACTURAS  (enrutadas al modelo Factura para respetar la lógica CH)
    # ------------------------------------------------------------------
    @staticmethod
    def registrar_factura(numero: str, tercero: str, monto: float, estado: str, fecha: str, tipo: str) -> int:
        """
        Compatibilidad con la UI existente: inserta factura 'legacy' usando el modelo Factura,
        que a su vez escribe extendido si el schema lo permite.
        - tipo: 'cliente' | 'proveedor'
        - estado: 'emitida' | 'pendiente' | 'pagada' | 'vencida'
        Retorna el ID insertado.
        """
        return Factura.crear(
            numero=numero,
            tercero=tercero,
            monto=_round(monto),
            tipo=tipo,
            fecha=fecha or date.today().isoformat(),
        )

    @staticmethod
    def listar_facturas():
        """
        Devuelve todas las facturas. Si el schema extendido existe, incluye doc_tipo, neto, iva, retención, total, vencimiento.
        Ordena por vencimiento/fecha.
        """
        return Factura.listar_todas()

    @staticmethod
    def cambiar_estado_factura(id_factura: int, nuevo_estado: str) -> None:
        Factura.cambiar_estado(id_factura, nuevo_estado.strip())

    @staticmethod
    def editar_factura(id_factura: int, numero: str, tercero: str, monto: float, estado: str, fecha: str, tipo: str) -> None:
        """
        Compatibilidad con UI actual: actualiza campos base de la factura.
        Si tienes una UI nueva para columnas extendidas, usa los métodos del modelo Factura.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE facturas
                SET numero = ?, proveedor = ?, monto = ?, estado = ?, fecha = ?, tipo = ?
                WHERE id = ?
                """,
                (numero.strip(), tercero.strip(), _round(monto), estado.strip(), fecha, tipo.strip(), id_factura),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def eliminar_factura(id_factura: int) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM facturas WHERE id = ?", (id_factura,))
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # REPORTES
    # ------------------------------------------------------------------
    @staticmethod
    def total_facturas_pagadas() -> float:
        """
        Suma 'monto' de facturas pagadas.
        Nota: en schema extendido 'monto' = 'total' (compatibilidad).
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT SUM(monto) FROM facturas WHERE estado = 'pagada'")
            total = cur.fetchone()[0] or 0
            return _round(total)
        finally:
            conn.close()

    @staticmethod
    def estado_resultado() -> Tuple[float, float, float]:
        """
        Retorna (total_ingresos_recibidos, total_gastos_completo, utilidad).
        Donde:
          - ingresos 'recibido'
          - gastos 'pagado'
          - + facturas de proveedor 'pagada' (evita doble contar)
        """
        conn = get_connection()
        try:
            cur = conn.cursor()

            # Ingresos efectivamente recibidos
            cur.execute("SELECT SUM(monto) FROM ingresos WHERE estado = 'recibido'")
            total_ingresos = _round(cur.fetchone()[0] or 0)

            # Gastos pagados (gastos directos)
            cur.execute("SELECT SUM(monto) FROM gastos WHERE estado = 'pagado'")
            total_gastos = _round(cur.fetchone()[0] or 0)

        finally:
            conn.close()

        # Facturas de proveedor pagadas (flujo equivalente a costo/gasto)
        conn2 = get_connection()
        try:
            cur2 = conn2.cursor()
            cur2.execute(
                "SELECT SUM(monto) FROM facturas WHERE estado = 'pagada' AND tipo = 'proveedor'"
            )
            total_fact_prov = _round(cur2.fetchone()[0] or 0)
        finally:
            conn2.close()

        total_gastos_completo = _round(total_gastos + total_fact_prov)
        utilidad = _round(total_ingresos - total_gastos_completo)
        return total_ingresos, total_gastos_completo, utilidad
