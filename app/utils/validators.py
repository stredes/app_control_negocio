# Archivo: validators.py
"""
Validadores reutilizables (Chile).
- validar_rut: Módulo 11 (admite formatos con puntos/guion; DV 0-9 o K).
"""

import re


def normalizar_rut(rut: str) -> str:
    """
    Normaliza el RUT (quita puntos/guion, mayúsculas).
    Ej: "12.345.678-5" -> "123456785"
    """
    return rut.replace(".", "").replace("-", "").strip().upper()


def validar_rut(rut: str) -> bool:
    """
    Retorna True si el RUT es válido según Módulo 11.
    Acepta 'k'/'K' como dígito verificador.
    """
    s = normalizar_rut(rut)
    if len(s) < 2 or not re.match(r"^\d+[\dK]$", s):
        return False

    cuerpo, dv = s[:-1], s[-1]
    if not cuerpo.isdigit():
        return False

    # Módulo 11 con factores 2..7 cíclicos
    suma, factor = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1

    resto = suma % 11
    dv_calc_num = 11 - resto
    if dv_calc_num == 11:
        dv_calc = "0"
    elif dv_calc_num == 10:
        dv_calc = "K"
    else:
        dv_calc = str(dv_calc_num)

    return dv == dv_calc


def formatear_rut(rut: str) -> str:
    """
    Devuelve el RUT formateado con puntos y guion.
    Básico, sin validación estricta. Útil solo para mostrar.
    """
    s = normalizar_rut(rut)
    if len(s) < 2:
        return rut
    cuerpo, dv = s[:-1], s[-1]
    # Inserta puntos cada 3 desde la derecha
    partes = []
    while len(cuerpo) > 3:
        partes.insert(0, cuerpo[-3:])
        cuerpo = cuerpo[:-3]
    if cuerpo:
        partes.insert(0, cuerpo)
    return f"{'.'.join(partes)}-{dv}"
