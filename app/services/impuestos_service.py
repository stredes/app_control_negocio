"""
Cálculos de impuestos/retenciones centralizados.
Se usa redondeo a MONETARY_DECIMALS desde config.
"""

from decimal import Decimal, ROUND_HALF_UP
from app.config.constantes import IVA_RATE, RETENCION_HONORARIOS, MONETARY_DECIMALS


def _round_money(value: float | Decimal) -> float:
    """
    Redondea a MONETARY_DECIMALS con HALF_UP (estándar contable).
    Devuelve float para compatibilidad con código existente.
    """
    q = Decimal(10) ** -MONETARY_DECIMALS
    d = Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP)
    return float(d)


def calc_iva(neto: float) -> float:
    """IVA = neto * 0.19"""
    return _round_money(neto * IVA_RATE)


def calc_retencion_honorarios(bruto: float) -> float:
    """Retención honorarios = bruto * 10,75% (o tasa vigente en config)."""
    return _round_money(bruto * RETENCION_HONORARIOS)


def neto_desde_bruto_con_iva(bruto: float) -> float:
    """
    Si el precio/bruto YA incluye IVA (caso boleta mostrada al consumidor),
    calcula el neto: neto = bruto / (1 + IVA).
    """
    return _round_money(bruto / (1.0 + IVA_RATE))


def bruto_desde_neto_con_iva(neto: float) -> float:
    """
    Si tienes neto y quieres el bruto (mostrar precio con IVA al consumidor).
    """
    return _round_money(neto * (1.0 + IVA_RATE))
