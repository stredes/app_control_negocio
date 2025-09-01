# app/models/factura.py
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Sequence, Any, Dict

from app.db.database import get_connection
from app.config.constantes import (
    IVA_RATE,
    RETENCION_HONORARIOS,
    DEFAULT_PAYMENT_DAYS,
    SII_FACTURA,
    SII_FACTURA_EXENTA,
    SII_BOLETA,
    SII_BOLETA_EXENTA,
    MONETARY_DECIMALS,
)

# ---------------------------
# Utils monetarios y de fechas
# ---------------------------
Q = Decimal(10) ** -MONETARY_DECIMALS  # p.ej. 0.01 con 2 decimales


def _D(x: Any) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x or 0))


def _round(x: Any) -> Decimal:
    return _D(x).quantize(Q, rounding=ROUND_HALF_UP)


def _calc_vencimiento(fecha_iso: str, dias: int = DEFAULT_PAYMENT_DAYS) -> str:
    y, m, d = map(int, fecha_iso.split("-"))
    return (date(y, m, d) + timedelta(days=int(dias))).isoformat()


def _es_exento(doc_tipo: Optional[int]) -> bool:
    return doc_tipo in (SII_FACTURA_EXENTA, SII_BOLETA_EXENTA)


def _es_honorarios(doc_tipo: Optional[int]) -> bool:
    """
    Si manejas un código específico para boleta de honorarios,
    ajusta esta función para detectarlo y aplicar retención.
    """
    return False  # Cambia a True si defines SII_BOLETA_HONORARIOS


def _validar_doc_tipo(doc_tipo: Optional[int]) -> Optional[int]:
    if doc_tipo is None:
        return None
    validos = {SII_FACTURA, SII_FACTURA_EXENTA, SII_BOLETA, SII_BOLETA_EXENTA}
    if doc_tipo not in validos:
        raise ValueError(f"doc_tipo inválido: {doc_tipo}")
    return doc_tipo


def _calcular_desglose_factura(
    neto: Decimal,
    doc_tipo: Optional[int],
    iva_rate: float = IVA_RATE,
    retencion_rate: float = RETENCION_HONORARIOS,
) -> Dict[str, Decimal]:
    """
    A partir de un neto calcula iva/retención/total según doc_tipo.
    - Exentos: iva=0.
    - Honorarios: aplica retención (descuento) si corresponde.
    """
    if neto < 0:
        raise ValueError("Neto no puede ser negativo.")

    iva = _round(0) if _es_exento(doc_tipo) else _round(_D(iva_rate) * neto)
    retencion = _round(_D(retencion_rate) * neto) if _es_honorarios(doc_tipo) else _round(0)
    total = _round(neto + iva - retencion)
    if total < 0:
        total = _round(0)

    return {"iva": iva, "retencion": retencion, "total": total}


# ---------------------------
# Modelo
# ---------------------------
class Factura:
    """
    Modelo con compatibilidad legacy y soporte extendido:

    Legacy:
      facturas(id, numero, proveedor, monto, estado, fecha, tipo)
      - Solo 'monto' (total).

    Extendida:
      facturas(..., doc_tipo, neto, iva, retencion, total, vencimiento)
      - 'iva' y 'retencion' son montos.
      - 'total' es total a cobrar/pagar.
      - 'vencimiento' ISO (YYYY-MM-DD).
    """

    # ---------------------------
    # Introspección de esquema
    # ---------------------------
    @staticmethod
    def _extended_enabled(conn=None) -> bool:
        close = False
        if conn is None:
            conn = get_connection()
            close = True
        try:
            needed = {"doc_tipo", "neto", "iva", "retencion", "total", "vencimiento"}
            cur = conn.execute("PRAGMA table_info(facturas)")
            cols = {row[1] for row in cur.fetchall()}
            return needed.issubset(cols)
        finally:
            if close:
                conn.close()

    # ---------------------------
    # Altas
    # ---------------------------
    @staticmethod
    def crear_desde_neto(
        tercero: str,                # en tu schema se llama 'proveedor' (puede ser cliente/proveedor)
        tipo: str,                   # 'cliente' | 'proveedor'
        neto: float | Decimal,       # neto a facturar/pagar
        doc_tipo: Optional[int] = None,  # SII_* (33,34,39,41) o None
        numero: Optional[str] = None,
        fecha: Optional[str] = None,       # ISO; default hoy
        dias_plazo: Optional[int] = None,  # default DEFAULT_PAYMENT_DAYS
        estado: str = "emitida",           # 'emitida' por defecto
    ) -> int:
        """
        Crea una factura calculando IVA/retención/total a partir de neto + doc_tipo.
        Usa columnas extendidas si existen; si no, degrada a legacy guardando 'monto=total'.
        """
        doc_tipo = _validar_doc_tipo(doc_tipo) if doc_tipo is not None else None
        fecha = fecha or date.today().isoformat()
        venc = _calc_vencimiento(fecha, dias_plazo or DEFAULT_PAYMENT_DAYS)

        neto_dec = _round(neto)
        desg = _calcular_desglose_factura(neto=_D(neto_dec), doc_tipo=doc_tipo)

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            if Factura._extended_enabled(conn):
                cur.execute(
                    """
                    INSERT INTO facturas (
                        numero, proveedor, monto, estado, fecha, tipo,
                        doc_tipo, neto, iva, retencion, total, vencimiento
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        (numero or "").strip(),
                        tercero.strip(),
                        float(desg["total"]),   # compat: 'monto' legacy = total
                        estado,
                        fecha,
                        tipo,
                        doc_tipo,
                        float(neto_dec),
                        float(desg["iva"]),
                        float(desg["retencion"]),
                        float(desg["total"]),
                        venc,
                    ),
                )
            else:
                # Legacy: solo guardamos 'monto' (total) y campos base
                cur.execute(
                    """
                    INSERT INTO facturas (numero, proveedor, monto, estado, fecha, tipo)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        (numero or "").strip(),
                        tercero.strip(),
                        float(desg["total"]),
                        estado,
                        fecha,
                        tipo,
                    ),
                )

            new_id = cur.lastrowid
            conn.commit()
            return int(new_id)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def crear_extendida(
        numero: Optional[str],
        tercero: str,
        doc_tipo: Optional[int],
        neto: float,
        iva: float,
        retencion: float,
        total: float,
        tipo: str,                      # 'cliente' | 'proveedor'
        fecha: Optional[str] = None,    # ISO
        vencimiento: Optional[str] = None,
        estado: str = "pendiente",
    ) -> int:
        """
        Inserta con montos ya calculados. Si el schema no es extendido, cae a legacy guardando 'monto=total'.
        """
        doc_tipo = _validar_doc_tipo(doc_tipo) if doc_tipo is not None else None
        fecha = fecha or date.today().isoformat()

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            if Factura._extended_enabled(conn):
                cur.execute(
                    """
                    INSERT INTO facturas (
                        numero, proveedor, monto, estado, fecha, tipo,
                        doc_tipo, neto, iva, retencion, total, vencimiento
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        (numero or "").strip(),
                        tercero.strip(),
                        float(_round(total)),   # compat: 'monto' legacy
                        estado,
                        fecha,
                        tipo,
                        doc_tipo,
                        float(_round(neto)),
                        float(_round(iva)),
                        float(_round(retencion)),
                        float(_round(total)),
                        vencimiento,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO facturas (numero, proveedor, monto, estado, fecha, tipo)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        (numero or "").strip(),
                        tercero.strip(),
                        float(_round(total)),
                        estado,
                        fecha,
                        tipo,
                    ),
                )

            new_id = cur.lastrowid
            conn.commit()
            return int(new_id)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def crear(numero, tercero, monto, tipo, fecha=None) -> int:
        """
        Legacy: crea factura 'emitida' con 'monto' (total).
        Si hay columnas extendidas, rellena doc_tipo=None, neto=monto, iva=0, retencion=0, total=monto.
        """
        fecha = fecha or date.today().isoformat()
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            if Factura._extended_enabled(conn):
                cur.execute(
                    """
                    INSERT INTO facturas (
                        numero, proveedor, monto, estado, fecha, tipo,
                        doc_tipo, neto, iva, retencion, total, vencimiento
                    ) VALUES (?, ?, ?, 'emitida', ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        (numero or "").strip(),
                        tercero.strip(),
                        float(_round(monto)),
                        fecha,
                        tipo,
                        None,
                        float(_round(monto)),
                        0.0,
                        0.0,
                        float(_round(monto)),
                        None,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO facturas (numero, proveedor, monto, estado, fecha, tipo)
                    VALUES (?, ?, ?, 'emitida', ?, ?)
                    """,
                    ((numero or "").strip(), tercero.strip(), float(_round(monto)), fecha, tipo),
                )

            new_id = cur.lastrowid
            conn.commit()
            return int(new_id)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---------------------------
    # Estados
    # ---------------------------
    @staticmethod
    def cambiar_estado(id_factura: int, nuevo_estado: str) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE facturas SET estado = ? WHERE id = ?", (nuevo_estado, id_factura))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def marcar_vencidas_automaticamente() -> int:
        """
        Marca 'vencida' toda factura 'pendiente' con vencimiento < hoy.
        Retorna filas afectadas (0 si schema legacy).
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            if Factura._extended_enabled(conn):
                cur.execute(
                    """
                    UPDATE facturas
                    SET estado = 'vencida'
                    WHERE estado = 'pendiente'
                      AND vencimiento IS NOT NULL
                      AND date(vencimiento) < date('now')
                    """
                )
                count = cur.rowcount
            else:
                count = 0
            conn.commit()
            return count
        finally:
            conn.close()

    # ---------------------------
    # Lecturas
    # ---------------------------
    @staticmethod
    def obtener_por_id(id_factura: int):
        conn = get_connection()
        try:
            cur = conn.cursor()
            if Factura._extended_enabled(conn):
                cur.execute(
                    """
                    SELECT id, numero, proveedor, monto, estado, fecha, tipo,
                           doc_tipo, neto, iva, retencion, total, vencimiento
                    FROM facturas
                    WHERE id = ?
                    """,
                    (id_factura,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, numero, proveedor, monto, estado, fecha, tipo
                    FROM facturas
                    WHERE id = ?
                    """,
                    (id_factura,),
                )
            return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def listar_por_tipo_y_estado(tipo: str, estados: Sequence[str]):
        """
        Devuelve facturas de un tipo ('cliente' | 'proveedor') en los estados dados.
        Si el schema es extendido, incluye columnas extra.
        """
        if not estados:
            return []

        conn = get_connection()
        try:
            cur = conn.cursor()
            ph = ",".join("?" for _ in estados)
            if Factura._extended_enabled(conn):
                sql = f"""
                    SELECT id, numero, proveedor, monto, estado, fecha, tipo,
                           doc_tipo, neto, iva, retencion, total, vencimiento
                    FROM facturas
                    WHERE tipo = ? AND estado IN ({ph})
                    ORDER BY date(COALESCE(vencimiento, fecha)) DESC, id DESC
                """
            else:
                sql = f"""
                    SELECT id, numero, proveedor, monto, estado, fecha, tipo
                    FROM facturas
                    WHERE tipo = ? AND estado IN ({ph})
                    ORDER BY date(fecha) DESC, id DESC
                """
            cur.execute(sql, [tipo, *estados])
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def listar_todas():
        conn = get_connection()
        try:
            cur = conn.cursor()
            if Factura._extended_enabled(conn):
                cur.execute(
                    """
                    SELECT id, numero, proveedor, monto, estado, fecha, tipo,
                           doc_tipo, neto, iva, retencion, total, vencimiento
                    FROM facturas
                    ORDER BY date(COALESCE(vencimiento, fecha)) DESC, id DESC
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT id, numero, proveedor, monto, estado, fecha, tipo
                    FROM facturas
                    ORDER BY date(fecha) DESC, id DESC
                    """
                )
            return cur.fetchall()
        finally:
            conn.close()
