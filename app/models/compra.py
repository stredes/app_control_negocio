# app/models/compra.py
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Any, Dict

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

# -----------------------------------------------------
# Utilidades de cálculo y normalización
# -----------------------------------------------------
Q = Decimal(10) ** -MONETARY_DECIMALS  # p.ej. 0.01 para 2 decimales


def _D(x: Any) -> Decimal:
    """Convierte a Decimal de forma segura."""
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x or 0))


def _round(x: Any) -> Decimal:
    """Redondeo monetario estándar (HALF_UP) según MONETARY_DECIMALS."""
    return _D(x).quantize(Q, rounding=ROUND_HALF_UP)


def _calc_vencimiento(fecha_iso: str, dias: int = DEFAULT_PAYMENT_DAYS) -> str:
    y, m, d = map(int, fecha_iso.split("-"))
    base = date(y, m, d)
    return (base + timedelta(days=int(dias))).isoformat()


def _es_doc_exento(doc_tipo: Optional[int]) -> bool:
    return doc_tipo in (SII_FACTURA_EXENTA, SII_BOLETA_EXENTA)


def _es_boleta_honorarios(doc_tipo: Optional[int]) -> bool:
    """
    Si manejas un código específico para boleta de honorarios,
    ajusta esta función para detectarlo y aplicar retención.
    """
    return False  # Cambia a True si defines, por ejemplo, SII_BOLETA_HONORARIOS


def _validar_doc_tipo(doc_tipo: Optional[int]) -> Optional[int]:
    if doc_tipo is None:
        return None
    validos = {SII_FACTURA, SII_FACTURA_EXENTA, SII_BOLETA, SII_BOLETA_EXENTA}
    if doc_tipo not in validos:
        raise ValueError(f"doc_tipo inválido: {doc_tipo}")
    return doc_tipo


def _calcular_desglose(
    cantidad: int,
    precio_unitario_neto: float | Decimal,
    doc_tipo: Optional[int],
    iva_rate: float = IVA_RATE,
    retencion_rate: float = RETENCION_HONORARIOS,
) -> Dict[str, Decimal]:
    """
    A partir de cantidad y precio neto unitario calcula neto, iva, retención y total:
    - Exentos: iva=0
    - Honorarios (si aplica): retención (se descuenta del total)
    """
    cant = int(cantidad)
    if cant <= 0:
        raise ValueError("Cantidad debe ser > 0.")
    pu = _D(precio_unitario_neto)
    if pu < 0:
        raise ValueError("Precio unitario no puede ser negativo.")

    neto = _round(pu * cant)
    iva_monto = _round(0) if _es_doc_exento(doc_tipo) else _round(_D(iva_rate) * neto)
    retencion = _round(_D(retencion_rate) * neto) if _es_boleta_honorarios(doc_tipo) else _round(0)
    total = _round(neto + iva_monto - retencion)
    if total < 0:
        total = _round(0)

    return {"neto": neto, "iva": iva_monto, "retencion": retencion, "total": total}


# -----------------------------------------------------
# Modelo
# -----------------------------------------------------
class Compra:
    """
    Modelo de Compras con compatibilidad hacia atrás y soporte de esquema extendido.

    Legacy:
      compras(id, proveedor, producto, cantidad, precio_unitario, iva, total, fecha)
      - 'iva' = porcentaje/tasa (0.19 o 19)

    Extendida (lógica Chile):
      compras(..., doc_tipo INT/TEXT, neto REAL, iva REAL, retencion REAL, total REAL, vencimiento TEXT)
      - aquí 'iva' es MONTO, no porcentaje.
    """

    # ---------------------------
    # Helpers internos de esquema
    # ---------------------------
    @staticmethod
    def _has_column(conn, table: str, column: str) -> bool:
        cur = conn.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in cur.fetchall()]
        return column in cols

    @staticmethod
    def _extended_schema_enabled(conn=None) -> bool:
        """
        True si existen las columnas clave del esquema extendido en 'compras'.
        """
        close = False
        if conn is None:
            conn = get_connection()
            close = True
        try:
            cur = conn.execute("PRAGMA table_info(compras)")
            cols = {r[1] for r in cur.fetchall()}
            needed = {"doc_tipo", "neto", "retencion", "total"}  # tolera faltas de 'iva'/'vencimiento'
            return needed.issubset(cols)
        finally:
            if close:
                conn.close()

    @staticmethod
    def _to_rate(iva_value: float) -> float:
        """Convierte 19 → 0.19; si ya es tasa (≤1), la devuelve igual."""
        return iva_value / 100.0 if iva_value > 1 else iva_value

    @staticmethod
    def _verificar_producto_existe(cur, nombre: str) -> None:
        cur.execute("SELECT 1 FROM productos WHERE nombre = ? LIMIT 1", (nombre,))
        if not cur.fetchone():
            raise ValueError(f"Producto '{nombre}' no existe.")

    # ---------------------------
    # Altas (API recomendada)
    # ---------------------------
    @staticmethod
    def crear(
        proveedor: str,
        producto: str,
        cantidad: int,
        precio_unitario_neto: float | Decimal,
        doc_tipo: Optional[int] = None,
        fecha: Optional[str] = None,        # YYYY-MM-DD; por defecto hoy
        vencimiento: Optional[str] = None,  # YYYY-MM-DD; por defecto +DEFAULT_PAYMENT_DAYS
    ) -> int:
        """
        Crea una compra calculando neto/iva/retención/total automáticamente según doc_tipo.
        Si el esquema extendido no está disponible, degrada a legacy con los campos posibles.
        """
        doc_tipo = _validar_doc_tipo(doc_tipo) if doc_tipo is not None else None
        fecha_actual = fecha or date.today().isoformat()
        venc = vencimiento or _calc_vencimiento(fecha_actual, DEFAULT_PAYMENT_DAYS)

        desglose = _calcular_desglose(
            cantidad=cantidad,
            precio_unitario_neto=precio_unitario_neto,
            doc_tipo=doc_tipo,
            iva_rate=IVA_RATE,
            retencion_rate=RETENCION_HONORARIOS,
        )

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            Compra._verificar_producto_existe(cur, producto)

            if Compra._extended_schema_enabled(conn):
                # Guardamos montos desglosados
                cur.execute(
                    """
                    INSERT INTO compras (
                        proveedor, producto, cantidad, precio_unitario,
                        doc_tipo, neto, iva, retencion, total, fecha, vencimiento
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        proveedor,
                        producto,
                        int(cantidad),
                        float(_round(precio_unitario_neto)),
                        doc_tipo,
                        float(desglose["neto"]),
                        float(desglose["iva"]),
                        float(desglose["retencion"]),
                        float(desglose["total"]),
                        fecha_actual,
                        venc,
                    ),
                )
            else:
                # Legacy: guardar tasa en 'iva' (sin retención)
                iva_rate = Compra._to_rate(IVA_RATE)
                if _es_doc_exento(doc_tipo):
                    iva_rate = 0.0
                cur.execute(
                    """
                    INSERT INTO compras (
                        proveedor, producto, cantidad, precio_unitario, iva, total, fecha
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        proveedor,
                        producto,
                        int(cantidad),
                        float(_round(precio_unitario_neto)),
                        float(_round(iva_rate)),
                        float(desglose["total"]),
                        fecha_actual,
                    ),
                )

            # Ajustar stock
            cur.execute(
                "UPDATE productos SET stock = stock + ? WHERE nombre = ?",
                (int(cantidad), producto),
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
    # Altas (compatibilidad legacy)
    # ---------------------------
    @staticmethod
    def registrar(proveedor, producto, cantidad, precio_unitario, iva=0.19) -> None:
        """
        Método legacy (compatibilidad). Mantiene la firma original.
        - 'iva' puede venir como 0.19 o 19 → se normaliza a tasa.
        - Calcula total y guarda extendido si está disponible (doc_tipo NULL, retención 0).
        """
        iva_rate = Compra._to_rate(float(iva))
        neto = _round(_D(precio_unitario) * int(cantidad))
        iva_monto = _round(neto * _D(iva_rate))
        total = _round(neto + iva_monto)
        fecha_actual = date.today().isoformat()
        venc = _calc_vencimiento(fecha_actual, DEFAULT_PAYMENT_DAYS)

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            Compra._verificar_producto_existe(cur, producto)

            if Compra._extended_schema_enabled(conn):
                cur.execute(
                    """
                    INSERT INTO compras (
                        proveedor, producto, cantidad, precio_unitario,
                        doc_tipo, neto, iva, retencion, total, fecha, vencimiento
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        proveedor,
                        producto,
                        int(cantidad),
                        float(_round(precio_unitario)),
                        None,  # doc_tipo desconocido en legacy
                        float(neto),
                        float(iva_monto),
                        0.0,
                        float(total),
                        fecha_actual,
                        venc,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO compras (
                        proveedor, producto, cantidad, precio_unitario, iva, total, fecha
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        proveedor,
                        producto,
                        int(cantidad),
                        float(_round(precio_unitario)),
                        float(_round(iva_rate)),
                        float(total),
                        fecha_actual,
                    ),
                )

            # Stock
            cur.execute(
                "UPDATE productos SET stock = stock + ? WHERE nombre = ?",
                (int(cantidad), producto),
            )

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---------------------------
    # Lecturas
    # ---------------------------
    @staticmethod
    def obtener_por_id(id_compra: int):
        conn = get_connection()
        cur = conn.cursor()

        if Compra._extended_schema_enabled(conn):
            cur.execute(
                """
                SELECT id, proveedor, producto, cantidad, precio_unitario,
                       doc_tipo, neto, iva, retencion, total, fecha, vencimiento
                FROM compras
                WHERE id = ?
                """,
                (id_compra,),
            )
        else:
            cur.execute(
                """
                SELECT id, proveedor, producto, cantidad,
                       precio_unitario, iva, total, fecha
                FROM compras
                WHERE id = ?
                """,
                (id_compra,),
            )

        compra = cur.fetchone()
        conn.close()
        return compra

    @staticmethod
    def listar_todas():
        conn = get_connection()
        cur = conn.cursor()

        if Compra._extended_schema_enabled(conn):
            cur.execute(
                """
                SELECT id, proveedor, producto, cantidad, precio_unitario,
                       doc_tipo, neto, iva, retencion, total, fecha, vencimiento
                FROM compras
                ORDER BY id DESC
                """
            )
        else:
            cur.execute(
                """
                SELECT id, proveedor, producto, cantidad,
                       precio_unitario, iva, total, fecha
                FROM compras
                ORDER BY id DESC
                """
            )

        resultados = cur.fetchall()
        conn.close()
        return resultados

    @staticmethod
    def ultima_compra_producto(nombre_producto: str):
        conn = get_connection()
        cur = conn.cursor()

        if Compra._extended_schema_enabled(conn):
            cur.execute(
                """
                SELECT id, proveedor, producto, cantidad, precio_unitario,
                       doc_tipo, neto, iva, retencion, total, fecha, vencimiento
                FROM compras
                WHERE producto = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (nombre_producto,),
            )
        else:
            cur.execute(
                """
                SELECT id, proveedor, producto, cantidad,
                       precio_unitario, iva, total, fecha
                FROM compras
                WHERE producto = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (nombre_producto,),
            )

        resultado = cur.fetchone()
        conn.close()
        return resultado

    # ---------------------------
    # Actualizaciones
    # ---------------------------
    @staticmethod
    def editar_extendido(
        id_compra: int,
        proveedor: str,
        producto: str,
        cantidad: int,
        precio_unitario_neto: float | Decimal,
        doc_tipo: Optional[int],
        fecha: Optional[str] = None,
        vencimiento: Optional[str] = None,
    ) -> None:
        """
        Recalcula y actualiza una compra (extendido) y ajusta stock correctamente.
        """
        doc_tipo = _validar_doc_tipo(doc_tipo) if doc_tipo is not None else None
        fecha_actual = fecha or date.today().isoformat()
        venc = vencimiento or _calc_vencimiento(fecha_actual, DEFAULT_PAYMENT_DAYS)

        desglose = _calcular_desglose(
            cantidad=cantidad,
            precio_unitario_neto=precio_unitario_neto,
            doc_tipo=doc_tipo,
            iva_rate=IVA_RATE,
            retencion_rate=RETENCION_HONORARIOS,
        )

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            # revertir stock anterior
            cur.execute("SELECT cantidad, producto FROM compras WHERE id = ?", (id_compra,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Compra id={id_compra} no existe.")
            antigua_cant, antiguo_prod = row
            cur.execute(
                "UPDATE productos SET stock = stock - ? WHERE nombre = ?",
                (int(antigua_cant), antiguo_prod),
            )

            # validar producto actual
            Compra._verificar_producto_existe(cur, producto)

            if Compra._extended_schema_enabled(conn):
                cur.execute(
                    """
                    UPDATE compras SET
                        proveedor = ?, producto = ?, cantidad = ?, precio_unitario = ?,
                        doc_tipo = ?, neto = ?, iva = ?, retencion = ?, total = ?,
                        fecha = ?, vencimiento = ?
                    WHERE id = ?
                    """,
                    (
                        proveedor,
                        producto,
                        int(cantidad),
                        float(_round(precio_unitario_neto)),
                        doc_tipo,
                        float(desglose["neto"]),
                        float(desglose["iva"]),
                        float(desglose["retencion"]),
                        float(desglose["total"]),
                        fecha_actual,
                        venc,
                        id_compra,
                    ),
                )
            else:
                # degradar a legacy con tasa en 'iva'
                iva_rate = Compra._to_rate(IVA_RATE)
                if _es_doc_exento(doc_tipo):
                    iva_rate = 0.0
                cur.execute(
                    """
                    UPDATE compras SET
                        proveedor = ?, producto = ?, cantidad = ?,
                        precio_unitario = ?, iva = ?, total = ?, fecha = ?
                    WHERE id = ?
                    """,
                    (
                        proveedor,
                        producto,
                        int(cantidad),
                        float(_round(precio_unitario_neto)),
                        float(_round(iva_rate)),
                        float(desglose["total"]),
                        fecha_actual,
                        id_compra,
                    ),
                )

            # aplicar nuevo stock
            cur.execute(
                "UPDATE productos SET stock = stock + ? WHERE nombre = ?",
                (int(cantidad), producto),
            )

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def editar(id_compra, proveedor, producto, cantidad, precio_unitario, iva=0.19):
        """
        Método legacy (compatibilidad). Recalcula total y actualiza, ajustando stock.
        """
        iva_rate = Compra._to_rate(float(iva))
        neto = _round(_D(precio_unitario) * int(cantidad))
        iva_monto = _round(neto * _D(iva_rate))
        total = _round(neto + iva_monto)
        fecha_actual = date.today().isoformat()
        venc = _calc_vencimiento(fecha_actual, DEFAULT_PAYMENT_DAYS)

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            # revertir stock viejo
            cur.execute("SELECT cantidad, producto FROM compras WHERE id = ?", (id_compra,))
            viejo = cur.fetchone()
            if not viejo:
                raise ValueError(f"Compra id={id_compra} no existe.")
            antigua_cant, antiguo_prod = viejo
            cur.execute(
                "UPDATE productos SET stock = stock - ? WHERE nombre = ?",
                (int(antigua_cant), antiguo_prod),
            )

            # validar producto actual
            Compra._verificar_producto_existe(cur, producto)

            if Compra._extended_schema_enabled(conn):
                cur.execute(
                    """
                    UPDATE compras SET
                        proveedor = ?, producto = ?, cantidad = ?, precio_unitario = ?,
                        doc_tipo = ?, neto = ?, iva = ?, retencion = ?, total = ?,
                        fecha = ?, vencimiento = ?
                    WHERE id = ?
                    """,
                    (
                        proveedor,
                        producto,
                        int(cantidad),
                        float(_round(precio_unitario)),
                        None,
                        float(neto),
                        float(iva_monto),
                        0.0,
                        float(total),
                        fecha_actual,
                        venc,
                        id_compra,
                    ),
                )
            else:
                cur.execute(
                    """
                    UPDATE compras SET
                        proveedor = ?, producto = ?, cantidad = ?,
                        precio_unitario = ?, iva = ?, total = ?, fecha = ?
                    WHERE id = ?
                    """,
                    (
                        proveedor,
                        producto,
                        int(cantidad),
                        float(_round(precio_unitario)),
                        float(_round(iva_rate)),
                        float(total),
                        fecha_actual,
                        id_compra,
                    ),
                )

            # aplicar nuevo stock
            cur.execute(
                "UPDATE productos SET stock = stock + ? WHERE nombre = ?",
                (int(cantidad), producto),
            )

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---------------------------
    # Borrado
    # ---------------------------
    @staticmethod
    def eliminar(id_compra: int):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            # Devolver stock
            cur.execute("SELECT cantidad, producto FROM compras WHERE id = ?", (id_compra,))
            row = cur.fetchone()
            if row:
                cant, prod = row
                cur.execute("DELETE FROM compras WHERE id = ?", (id_compra,))
                cur.execute(
                    "UPDATE productos SET stock = stock - ? WHERE nombre = ?",
                    (int(cant), prod),
                )

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
