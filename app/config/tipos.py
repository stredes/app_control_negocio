# control_negocio/app/config/tipos.py
"""
Tipos de documentos soportados por la lógica de negocio,
alineados con los códigos del SII (Chile).
"""

from enum import Enum


class DocTipo(str, Enum):
    FACTURA = "FACTURA"                 # 33
    FACTURA_EXENTA = "FACTURA_EXENTA"   # 34
    BOLETA = "BOLETA"                   # 39
    BOLETA_EXENTA = "BOLETA_EXENTA"     # 41
    BOLETA_HONORARIOS = "BOLETA_HONORARIOS"  # 46 (no oficial en SII, pero práctico en gestión interna)

    @property
    def code(self) -> int:
        """Código oficial SII (cuando aplica)."""
        mapping = {
            DocTipo.FACTURA: 33,
            DocTipo.FACTURA_EXENTA: 34,
            DocTipo.BOLETA: 39,
            DocTipo.BOLETA_EXENTA: 41,
            DocTipo.BOLETA_HONORARIOS: 46,  # usado como convención interna
        }
        return mapping[self]

    @property
    def label(self) -> str:
        """Descripción amigable para mostrar en UI/reportes."""
        labels = {
            DocTipo.FACTURA: "Factura Afecta",
            DocTipo.FACTURA_EXENTA: "Factura Exenta",
            DocTipo.BOLETA: "Boleta Afecta",
            DocTipo.BOLETA_EXENTA: "Boleta Exenta",
            DocTipo.BOLETA_HONORARIOS: "Boleta de Honorarios",
        }
        return labels[self]

    @property
    def is_exenta(self) -> bool:
        """True si el documento está exento de IVA."""
        return self in (DocTipo.FACTURA_EXENTA, DocTipo.BOLETA_EXENTA)

    @property
    def is_honorarios(self) -> bool:
        """True si corresponde a boleta de honorarios (aplica retención)."""
        return self == DocTipo.BOLETA_HONORARIOS
