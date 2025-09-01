# app/models/venta.py
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Any, Dict

from app.db.database import get_connection
from app.config.constantes import (
    IVA_RATE,
    RETENCION_HONORARIOS,
    MONETARY_DECIMALS,
)
# Opcional: si usas el Enum DocTipo en la capa UI/servicios
# from app.config.tipos import DocTipo

# -----------------------------------------------------
# Utilidades de cálculo
# -----------------------------------------------------
Q = Decimal(10) ** -MONETARY_DECIMALS  # 0.01 si trabajas con 2 decimales


def _D(x: Any) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x or 0))


def _round(x: Any) -> Decimal:
    return _D(x).quantize(Q, rounding=ROUND_HALF_UP)


def _to_rate(iva_value: float) -> float:
    """Convierte 19 → 0.19; si ya es tasa (≤1), la devuelve igual."""
    return iva_value / 100.0 if iva_value > 1 else iva_value


def _es_exenta(doc_tipo: Optional[str]) -> bool:
    # Si usas Enum DocTipo, podrías mapear con: return doc_tipo in (DocTipo.FACTURA_EXENTA.value, DocTipo.BOLETA_EXENTA.value)
    return str(doc_tipo or "").upper() in {"FACTURA_EXENTA", "BOLETA_EXENTA"}


def _es_honorarios(doc_tipo: Optional[str]) -> bool:
    # Si manejas boleta de honorarios por ventas (raro pero posible p/ servicios),
    # aplica retención. Ajusta si no corresponde a tu giro.
    return str(doc_tipo or "").upper() in {"BOLETA_HONORARIOS"}


def _desglose_venta(
    cantidad: int,
    precio_unitario_neto: float | Decimal,
    doc_tipo: Optional[str],
    iva_rate: float = IVA_RATE,
    retencion_rate: float = RETENCION_HONORARIOS,
) -> Dict[str, Decimal]:
    """Calcula neto, iva (MONTO), retención (MONTO) y total."""
    cant = int(cantidad)
    if cant <= 0:
        raise ValueError("Cantidad debe ser > 0.")
    pu = _D(precio_unitario_neto)
    if pu < 0:
        raise ValueError("Precio unitario no puede ser negativo.")

    neto = _round(pu * cant)
    iva_monto = _round(0 if _es_exenta(doc_tipo) else _D(iva_rate) * neto)
    retencion = _round(_D(retencion_rate) * neto) if _es_honorarios(doc_tipo) else _round(0)
    total = _round(neto + iva_monto - retencion)
    if total < 0:
        total = _round(0)

    return {"neto": neto, "iva": iva_monto, "retencion": retencion, "total": total}


# -----------------------------------------------------
# Modelo
# -----------------------------------------------------
class Venta:
    """
    Compatible con esquema legacy y extendido (lógica Chile).

    Legacy:
      ordenes_venta(id, cliente, producto, cantidad, precio_unitario, iva, total, fecha)
      - 'iva' se guarda como tasa/porcentaje (0.19 o 19).

    Extendido:
      ordenes_venta(..., doc_tipo TEXT, neto REAL, iva REAL, retencion REAL, total REAL, fecha TEXT)
      - 'iva' y 'retencion' son MONTOS; 'doc_tipo' = FACTURA/BOLETA/… (texto).
    """

    # ---------------------------
    # Helpers de introspección
    # ---------------------------
    @staticmethod
    def _has_column(conn, table: str, column: str) -> bool:
        cur = conn.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in cur.fetchall()]
        return column in cols

    @staticmethod
    def _extended_schema_enabled(conn=None) -> bool:
        """
        True si existen columnas clave de esquema extendido.
        Usamos un set mínimo para evitar falsos positivos.
        """
        close = False
        if conn is None:
            conn = get_connection()
            close = True
        try:
            cur = conn.execute("PRAGMA table_info(ordenes_venta)")
            cols = {row[1] for row in cur.fetchall()}
            needed = {"doc_tipo", "neto", "retencion", "total"}
            return needed.issubset(cols)
        finally:
            if close:
                conn.close()

    # ---------------------------
    # Altas (API recomendada)
    # ---------------------------
    @staticmethod
    def crear(
        cliente: str,
        producto: str,
        cantidad: int,
        precio_unitario_neto: float | Decimal,
        doc_tipo: Optional[str] = None,  # "FACTURA" | "BOLETA" | "FACTURA_EXENTA" | "BOLETA_EXENTA" | "BOLETA_HONORARIOS"
        fecha: Optional[str] = None,     # YYYY-MM-DD
    ) -> int:
        """
        Crea una venta con cálculo automático (neto/iva/retención/total). Valida stock.
        Degrada a legacy si el esquema extendido no está disponible.
        """
        fecha_actual = fecha or date.today().isoformat()
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            # Verificar existencia y stock
            cur.execute("SELECT stock FROM productos WHERE nombre = ?", (producto,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Producto '{producto}' no existe.")
            stock_actual = int(row[0] or 0)
            if int(cantidad) > stock_actual:
                raise ValueError(f"Stock insuficiente ({stock_actual}) para '{producto}'.")

            desglose = _desglose_venta(
                cantidad=cantidad,
                precio_unitario_neto=precio_unitario_neto,
                doc_tipo=doc_tipo,
                iva_rate=IVA_RATE,
                retencion_rate=RETENCION_HONORARIOS,
            )

            if Venta._extended_schema_enabled(conn):
                cur.execute(
                    """
                    INSERT INTO ordenes_venta (
                        cliente, producto, cantidad, precio_unitario,
                        doc_tipo, neto, iva, retencion, total, fecha
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cliente,
                        producto,
                        int(cantidad),
                        float(_round(precio_unitario_neto)),
                        (doc_tipo or None),
                        float(desglose["neto"]),
                        float(desglose["iva"]),
                        float(desglose["retencion"]),
                        float(desglose["total"]),
                        fecha_actual,
                    ),
                )
            else:
                # Legacy: guardamos tasa en 'iva' (si exento → 0.0)
                iva_rate = 0.0 if _es_exenta(doc_tipo) else _to_rate(IVA_RATE)
                cur.execute(
                    """
                    INSERT INTO ordenes_venta (
                        cliente, producto, cantidad, precio_unitario, iva, total, fecha
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cliente,
                        producto,
                        int(cantidad),
                        float(_round(precio_unitario_neto)),
                        float(_round(iva_rate)),
                        float(desglose["total"]),
                        fecha_actual,
                    ),
                )

            # Descontar stock
            cur.execute(
                "UPDATE productos SET stock = stock - ? WHERE nombre = ?",
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
    def registrar(cliente, producto, cantidad, precio_unitario, iva):
        """
        Método legacy. Mantiene firma original:
        - 'iva' puede venir como 0.19 o 19 → se normaliza a tasa.
        """
        if int(cantidad) <= 0 or float(precio_unitario) < 0:
            raise ValueError("Cantidad y precio deben ser válidos.")

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            # Stock
            cur.execute("SELECT stock FROM productos WHERE nombre = ?", (producto,))
            fila = cur.fetchone()
            if not fila:
                raise ValueError(f"Producto '{producto}' no existe.")
            stock_actual = int(fila[0] or 0)
            if int(cantidad) > stock_actual:
                raise ValueError(f"Stock insuficiente ({stock_actual}) para '{producto}'.")

            iva_rate = _to_rate(float(iva))
            neto = _round(_D(precio_unitario) * int(cantidad))
            iva_monto = _round(neto * _D(iva_rate))
            total = _round(neto + iva_monto)
            fecha = date.today().isoformat()

            if Venta._extended_schema_enabled(conn):
                # Guardamos desglose completo para mantener consistencia
                cur.execute(
                    """
                    INSERT INTO ordenes_venta (
                        cliente, producto, cantidad, precio_unitario,
                        doc_tipo, neto, iva, retencion, total, fecha
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cliente,
                        producto,
                        int(cantidad),
                        float(_round(precio_unitario)),
                        None,
                        float(neto),
                        float(iva_monto),
                        0.0,
                        float(total),
                        fecha,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO ordenes_venta (
                        cliente, producto, cantidad, precio_unitario, iva, total, fecha
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (cliente, producto, int(cantidad), float(_round(precio_unitario)), float(_round(iva_rate)), float(total), fecha),
                )

            # Descontar stock
            cur.execute(
                "UPDATE productos SET stock = stock - ? WHERE nombre = ?",
                (int(cantidad), producto),
            )

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---------------------------
    # Edición
    # ---------------------------
    @staticmethod
    def editar_extendido(
        id_venta: int,
        cliente: str,
        producto: str,
        cantidad: int,
        precio_unitario_neto: float,
        doc_tipo: Optional[str],
    ) -> None:
        """
        Recalcula y actualiza (extendido). Repone stock anterior y descuenta el nuevo.
        """
        if int(cantidad) <= 0 or float(precio_unitario_neto) < 0:
            raise ValueError("Cantidad y precio deben ser válidos.")

        fecha_actual = date.today().isoformat()
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            # Reponer stock anterior
            cur.execute("SELECT cantidad, producto FROM ordenes_venta WHERE id = ?", (id_venta,))
            prev = cur.fetchone()
            if not prev:
                raise ValueError(f"Venta con ID {id_venta} no encontrada.")
            cant_prev, prod_prev = prev
            cur.execute("UPDATE productos SET stock = stock + ? WHERE nombre = ?", (int(cant_prev), prod_prev))

            # Verificar stock del nuevo producto
            cur.execute("SELECT stock FROM productos WHERE nombre = ?", (producto,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Producto '{producto}' no existe.")
            stock_disp = int(row[0] or 0)
            if int(cantidad) > stock_disp:
                raise ValueError(f"Stock insuficiente ({stock_disp}) para '{producto}'.")

            # Calcular de nuevo
            desglose = _desglose_venta(
                cantidad=cantidad,
                precio_unitario_neto=precio_unitario_neto,
                doc_tipo=doc_tipo,
                iva_rate=IVA_RATE,
                retencion_rate=RETENCION_HONORARIOS,
            )

            if Venta._extended_schema_enabled(conn):
                cur.execute(
                    """
                    UPDATE ordenes_venta SET
                        cliente = ?, producto = ?, cantidad = ?, precio_unitario = ?,
                        doc_tipo = ?, neto = ?, iva = ?, retencion = ?, total = ?, fecha = ?
                    WHERE id = ?
                    """,
                    (
                        cliente,
                        producto,
                        int(cantidad),
                        float(_round(precio_unitario_neto)),
                        (doc_tipo or None),
                        float(desglose["neto"]),
                        float(desglose["iva"]),
                        float(desglose["retencion"]),
                        float(desglose["total"]),
                        fecha_actual,
                        id_venta,
                    ),
                )
            else:
                iva_rate = 0.0 if _es_exenta(doc_tipo) else _to_rate(IVA_RATE)
                cur.execute(
                    """
                    UPDATE ordenes_venta SET
                        cliente = ?, producto = ?, cantidad = ?,
                        precio_unitario = ?, iva = ?, total = ?, fecha = ?
                    WHERE id = ?
                    """,
                    (
                        cliente,
                        producto,
                        int(cantidad),
                        float(_round(precio_unitario_neto)),
                        float(_round(iva_rate)),
                        float(desglose["total"]),
                        fecha_actual,
                        id_venta,
                    ),
                )

            # Descontar stock nuevo
            cur.execute("UPDATE productos SET stock = stock - ? WHERE nombre = ?", (int(cantidad), producto))

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---------------------------
    # Lecturas y borrado
    # ---------------------------
    @staticmethod
    def listar_todas():
        """
        Si hay esquema extendido, incluye doc_tipo, neto, retención.
        """
        conn = get_connection()
        cur = conn.cursor()
        if Venta._extended_schema_enabled(conn):
            cur.execute(
                """
                SELECT id, cliente, producto, cantidad, precio_unitario,
                       doc_tipo, neto, iva, retencion, total, fecha
                FROM ordenes_venta
                ORDER BY id DESC
                """
            )
        else:
            cur.execute(
                """
                SELECT id, cliente, producto, cantidad,
                       precio_unitario, iva, total, fecha
                FROM ordenes_venta
                ORDER BY id DESC
                """
            )
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def ultima_venta_producto(nombre_producto: str):
        conn = get_connection()
        cur = conn.cursor()
        if Venta._extended_schema_enabled(conn):
            cur.execute(
                """
                SELECT id, cliente, producto, cantidad, precio_unitario,
                       doc_tipo, neto, iva, retencion, total, fecha
                FROM ordenes_venta
                WHERE producto = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (nombre_producto,),
            )
        else:
            cur.execute(
                """
                SELECT id, cliente, producto, cantidad,
                       precio_unitario, iva, total, fecha
                FROM ordenes_venta
                WHERE producto = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (nombre_producto,),
            )
        row = cur.fetchone()
        conn.close()
        return row

    @staticmethod
    def eliminar(id_venta: int):
        """
        Elimina una venta y repone stock (transaccional).
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            cur.execute("SELECT producto, cantidad FROM ordenes_venta WHERE id = ?", (id_venta,))
            fila = cur.fetchone()
            if not fila:
                raise ValueError(f"Venta con ID {id_venta} no encontrada.")
            producto, cantidad = fila

            cur.execute("DELETE FROM ordenes_venta WHERE id = ?", (id_venta,))
            cur.execute("UPDATE productos SET stock = stock + ? WHERE nombre = ?", (int(cantidad), producto))

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
