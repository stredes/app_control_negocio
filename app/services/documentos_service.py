# app/services/documentos_service.py
"""
Servicio de documentos: totales por tipo de documento y vencimientos.
- Centraliza reglas SII (Factura vs Boleta vs Honorarios).
- Sin dependencias externas: helpers de impuestos incluidos aquí.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal, TypedDict

from app.config.constantes import (
    DEFAULT_PAYMENT_DAYS,
    IVA_RATE,
    RETENCION_HONORARIOS,
    MONETARY_DECIMALS,
)
from app.config.tipos import DocTipo


# -------------------------------------------------------------------
# Redondeo y helpers numéricos
# -------------------------------------------------------------------
_Q = Decimal(10) ** -MONETARY_DECIMALS  # 0.01 si MONETARY_DECIMALS=2


def _D(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


def _round_money(x) -> float:
    """Redondeo monetario estándar (HALF_UP) a MONETARY_DECIMALS."""
    return float(_D(x).quantize(_Q, rounding=ROUND_HALF_UP))


def _to_rate(x: float) -> float:
    """Convierte 19 -> 0.19; si ya es tasa (<=1), la devuelve tal cual."""
    return x / 100.0 if x > 1 else x


# -------------------------------------------------------------------
# Cálculos de impuestos básicos (incluidos aquí para evitar dependencias)
# -------------------------------------------------------------------
def calc_iva(neto: float) -> float:
    """IVA = neto * IVA_RATE (tasa, no porcentaje)."""
    neto_d = _D(neto)
    iva = neto_d * _D(_to_rate(IVA_RATE))
    return _round_money(iva)


def calc_retencion_honorarios(bruto: float) -> float:
    """Retención en boleta de honorarios (monto)."""
    ret = _D(bruto) * _D(_to_rate(RETENCION_HONORARIOS))
    return _round_money(ret)


def neto_desde_bruto_con_iva(bruto_con_iva: float) -> float:
    """
    Convierte un monto con IVA a neto: neto = bruto / (1 + IVA_RATE).
    IVA_RATE es tasa (p. ej., 0.19).
    """
    bruto = _D(bruto_con_iva)
    factor = _D(1) + _D(_to_rate(IVA_RATE))
    neto = bruto / factor if factor != 0 else _D(0)
    return _round_money(neto)


# -------------------------------------------------------------------
# Tipados
# -------------------------------------------------------------------
class Totales(TypedDict):
    neto: float
    iva: float
    retencion: float
    total: float


# -------------------------------------------------------------------
# Reglas de vencimiento
# -------------------------------------------------------------------
def calcular_vencimiento(fecha_emision: date | None = None, dias: int = DEFAULT_PAYMENT_DAYS) -> date:
    """
    Vencimiento por defecto (Ley Pago a 30 días).
    Ajusta 'dias' si tienes acuerdos distintos.
    """
    f = fecha_emision or date.today()
    return f + timedelta(days=int(dias))


# -------------------------------------------------------------------
# Reglas de cálculo por tipo de documento
# -------------------------------------------------------------------
def calcular_totales_desde_neto(doc_tipo: DocTipo, neto: float) -> Totales:
    """
    Recibe NETO (sin IVA) y retorna desglose según tipo de documento.

    - FACTURA / BOLETA: afecta a IVA (19% por defecto).
    - FACTURA_EXENTA / BOLETA_EXENTA: IVA = 0.
    - BOLETA_HONORARIOS: IVA = 0, aplica RETENCIÓN sobre el bruto (= neto).
    """
    neto = _round_money(neto)

    if doc_tipo in (DocTipo.FACTURA, DocTipo.BOLETA):
        iva = calc_iva(neto)
        return Totales(neto=neto, iva=iva, retencion=0.0, total=_round_money(neto + iva))

    if doc_tipo in (DocTipo.FACTURA_EXENTA, DocTipo.BOLETA_EXENTA):
        return Totales(neto=neto, iva=0.0, retencion=0.0, total=neto)

    if doc_tipo == DocTipo.BOLETA_HONORARIOS:
        ret = calc_retencion_honorarios(neto)
        return Totales(neto=neto, iva=0.0, retencion=ret, total=_round_money(neto - ret))

    raise ValueError(f"Tipo de documento no soportado: {doc_tipo}")


def calcular_totales_desde_bruto_con_iva(doc_tipo: DocTipo, bruto: float) -> Totales:
    """
    Caso de UI donde el usuario ingresa PRECIOS CON IVA (retail/boleta):

    - Para BOLETA: convierte a neto y delega al cálculo desde neto.
    - Para BOLETA_EXENTA: bruto == neto.
    - Para FACTURA: si llegara bruto con IVA, se convierte a neto.
    - Para FACTURA_EXENTA: bruto == neto.
    - Para BOLETA_HONORARIOS: se interpreta 'bruto' como base sin IVA (no se divide).
    """
    bruto = _round_money(bruto)

    if doc_tipo == DocTipo.BOLETA:
        neto = neto_desde_bruto_con_iva(bruto)
        return calcular_totales_desde_neto(DocTipo.BOLETA, neto)

    if doc_tipo == DocTipo.BOLETA_EXENTA:
        return calcular_totales_desde_neto(DocTipo.BOLETA_EXENTA, bruto)

    if doc_tipo == DocTipo.FACTURA:
        neto = neto_desde_bruto_con_iva(bruto)
        return calcular_totales_desde_neto(DocTipo.FACTURA, neto)

    if doc_tipo == DocTipo.FACTURA_EXENTA:
        return calcular_totales_desde_neto(DocTipo.FACTURA_EXENTA, bruto)

    if doc_tipo == DocTipo.BOLETA_HONORARIOS:
        # En honorarios no hay IVA; el monto ingresado se considera base.
        return calcular_totales_desde_neto(DocTipo.BOLETA_HONORARIOS, bruto)

    raise ValueError(f"Tipo de documento no soportado: {doc_tipo}")
