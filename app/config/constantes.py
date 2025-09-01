"""
Constantes legales y de negocio (Chile) centralizadas.

⚠️ IMPORTANTE:
Siempre importa valores desde aquí en lugar de “hardcodear” (ej: 0.19, 30 días, etc.)
para mantener consistencia y facilitar futuras modificaciones legales.
"""

# ============================================================
# Impuestos y Retenciones
# ============================================================

# IVA general (vigente en Chile)
IVA_RATE: float = 0.19  # 19% IVA (tasa general)

# Retención de boletas de honorarios (según calendario progresivo del SII)
# ⚠️ Actualiza anualmente según la tasa oficial publicada por el SII.
RETENCION_HONORARIOS: float = 0.1075  # 10,75% vigente en 2025


# ============================================================
# Plazos / Vencimientos
# ============================================================

# Ley de Pago a 30 días (Ley N°21.131, vigente desde 2019)
DEFAULT_PAYMENT_DAYS: int = 30


# ============================================================
# Códigos SII (DTE más usados)
# Referencia: Servicio de Impuestos Internos (SII)
# ============================================================

SII_FACTURA: int = 33            # Factura electrónica afecta
SII_FACTURA_EXENTA: int = 34     # Factura electrónica exenta
SII_BOLETA: int = 39             # Boleta electrónica afecta
SII_BOLETA_EXENTA: int = 41      # Boleta electrónica exenta
SII_BOLETA_HONORARIOS: int = 48  # Boleta de honorarios (opcional según giro)


# ============================================================
# Redondeo Monetario
# ============================================================

# Cantidad de decimales usados en CLP:
# - 0 si manejas CLP como entero (lo más común, porque el CLP no tiene centavos).
# - 2 si manejas valores con centavos (ej: en sistemas que integran multimoneda).
MONETARY_DECIMALS: int = 0
