# control_negocio/app/models/cliente.py
from __future__ import annotations

import re
import sqlite3
from typing import List, Optional, Tuple

from app.db.database import get_connection


# =========================
# Helpers de normalización
# =========================

def _clean_str(s: Optional[str]) -> str:
    """Recorta, colapsa espacios y devuelve '' si viene None."""
    if s is None:
        return ""
    return " ".join(s.strip().split())


def _normalize_phone(phone: Optional[str]) -> str:
    """
    Normaliza teléfono a dígitos (+ separadores mínimos si quieres extender).
    Aquí simplemente dejamos solo dígitos y '+' inicial si venía.
    """
    if not phone:
        return ""
    phone = phone.strip()
    sign = "+" if phone.startswith("+") else ""
    digits = re.sub(r"\D+", "", phone)
    return (sign + digits) if digits else ""


# =========================
# Validación de RUT (Chile)
# =========================

def _normalize_rut(rut: Optional[str]) -> str:
    """
    Normaliza RUT a formato compacto: '12345678K' (sin puntos ni guion).
    DV puede ser 'K' mayúscula.
    """
    if not rut:
        return ""
    rut = rut.strip().upper()
    # eliminar puntos y guiones
    rut = re.sub(r"[\.\-]", "", rut)
    return rut


def _validate_rut(rut: str) -> bool:
    """
    Valida RUT chileno (módulo 11).
    Acepta DV '0-9' o 'K'. Asume rut ya normalizado sin puntos ni guion.
    """
    if not rut or len(rut) < 2:
        return False
    cuerpo, dv = rut[:-1], rut[-1]
    if not cuerpo.isdigit():
        return False

    # Cálculo módulo 11
    factores = [2, 3, 4, 5, 6, 7]
    suma = 0
    factor_idx = 0
    for d in reversed(cuerpo):
        suma += int(d) * factores[factor_idx]
        factor_idx = (factor_idx + 1) % len(factores)
    resto = suma % 11
    calc = 11 - resto
    dv_calc = "0" if calc == 11 else "K" if calc == 10 else str(calc)
    return dv == dv_calc


class Cliente:
    """
    Operaciones sobre la tabla `clientes`:
      clientes(id, nombre, rut, direccion, telefono)

    Consideraciones:
    - El esquema no define UNIQUE para `rut`, por lo que aquí validamos
      duplicados antes de crear/editar.
    - En comprobantes (ordenes_venta) se guarda el nombre literal del cliente.
      Si eliminas un cliente, los registros históricos mantienen el texto.
    """

    # ---------------
    # Consultas
    # ---------------
    @staticmethod
    def listar_todos() -> List[Tuple[int, str, str, str, str]]:
        """
        Devuelve todos los clientes, ordenados por nombre.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, nombre, rut, direccion, telefono
            FROM clientes
            ORDER BY nombre ASC
            """
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def obtener_por_id(id_cliente: int) -> Optional[Tuple[int, str, str, str, str]]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nombre, rut, direccion, telefono FROM clientes WHERE id = ?",
            (id_cliente,),
        )
        row = cur.fetchone()
        conn.close()
        return row

    @staticmethod
    def obtener_por_rut(rut: str) -> Optional[Tuple[int, str, str, str, str]]:
        rut_n = _normalize_rut(rut)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nombre, rut, direccion, telefono FROM clientes WHERE UPPER(REPLACE(REPLACE(rut,'.',''),'-','')) = ?",
            (rut_n,),
        )
        row = cur.fetchone()
        conn.close()
        return row

    @staticmethod
    def existe_rut(rut: str) -> bool:
        return Cliente.obtener_por_rut(rut) is not None

    # ---------------
    # Altas / Ediciones
    # ---------------
    @staticmethod
    def crear(nombre: str, rut: str, direccion: str, telefono: str) -> int:
        """
        Inserta un nuevo cliente y devuelve su ID.

        Reglas:
        - nombre obligatorio.
        - rut opcional, pero si viene debe ser válido y no duplicado.
        """
        nombre_n = _clean_str(nombre)
        if not nombre_n:
            raise ValueError("El nombre del cliente es obligatorio.")

        rut_n = _normalize_rut(rut)
        if rut_n:
            if not _validate_rut(rut_n):
                raise ValueError("RUT inválido.")
            if Cliente.existe_rut(rut_n):
                raise ValueError("Ya existe un cliente con ese RUT.")

        direccion_n = _clean_str(direccion)
        telefono_n = _normalize_phone(telefono)

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO clientes (nombre, rut, direccion, telefono)
                VALUES (?, ?, ?, ?)
                """,
                (nombre_n, rut_n, direccion_n, telefono_n),
            )
            conn.commit()
            return int(cur.lastrowid)
        finally:
            conn.close()

    @staticmethod
    def editar(id_cliente: int, nombre: str, rut: str, direccion: str, telefono: str) -> None:
        """
        Actualiza un cliente existente.

        Reglas:
        - nombre obligatorio.
        - Si rut viene, debe ser válido.
        - No permite duplicar RUT de otro cliente.
        """
        # Existe el cliente
        actual = Cliente.obtener_por_id(id_cliente)
        if not actual:
            raise ValueError(f"Cliente id={id_cliente} no existe.")

        nombre_n = _clean_str(nombre)
        if not nombre_n:
            raise ValueError("El nombre del cliente es obligatorio.")

        rut_n = _normalize_rut(rut)
        if rut_n and not _validate_rut(rut_n):
            raise ValueError("RUT inválido.")

        # Verificar colisión de RUT con otro cliente
        if rut_n:
            otro = Cliente.obtener_por_rut(rut_n)
            if otro and int(otro[0]) != int(id_cliente):
                raise ValueError("El RUT indicado pertenece a otro cliente.")

        direccion_n = _clean_str(direccion)
        telefono_n = _normalize_phone(telefono)

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE clientes SET
                    nombre = ?, rut = ?, direccion = ?, telefono = ?
                WHERE id = ?
                """,
                (nombre_n, rut_n, direccion_n, telefono_n, id_cliente),
            )
            conn.commit()
        finally:
            conn.close()

    # ---------------
    # Borrado
    # ---------------
    @staticmethod
    def _ventas_asociadas(cur: sqlite3.Cursor, id_cliente: int) -> int:
        """
        Cuenta ventas asociadas **por nombre** del cliente actual.
        Como 'ordenes_venta' guarda el nombre, necesitamos resolverlo primero.
        """
        cur.execute("SELECT nombre FROM clientes WHERE id = ?", (id_cliente,))
        row = cur.fetchone()
        if not row:
            return 0
        nombre = row[0]
        cur.execute("SELECT COUNT(*) FROM ordenes_venta WHERE cliente = ?", (nombre,))
        (count,) = cur.fetchone()
        return int(count)

    @staticmethod
    def eliminar(id_cliente: int, forzar: bool = False) -> None:
        """
        Elimina el cliente. Si tiene ventas asociadas (por nombre):
        - forzar=False: bloquea con mensaje claro.
        - forzar=True : elimina el registro del cliente y **no toca** ventas históricas
                        (conservan el nombre literal guardado en el comprobante).
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            # Existe?
            cur.execute("SELECT id FROM clientes WHERE id = ?", (id_cliente,))
            if not cur.fetchone():
                conn.rollback()
                return  # idempotente

            count = Cliente._ventas_asociadas(cur, id_cliente)
            if count > 0 and not forzar:
                conn.rollback()
                raise ValueError(
                    f"No se puede eliminar: el cliente tiene {count} venta(s) registrada(s). "
                    f"Use 'forzar=True' si desea eliminar solo el maestro (las ventas históricas conservarán el nombre)."
                )

            # Eliminar
            cur.execute("DELETE FROM clientes WHERE id = ?", (id_cliente,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---------------
    # Búsqueda libre por nombre
    # ---------------
    @staticmethod
    def buscar_por_nombre(nombre: str) -> List[Tuple[int, str, str, str, str]]:
        """
        Filtra clientes cuyo nombre contenga la cadena (case-insensitive).
        """
        patron = f"%{_clean_str(nombre)}%"
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, nombre, rut, direccion, telefono
            FROM clientes
            WHERE UPPER(nombre) LIKE UPPER(?)
            ORDER BY nombre ASC
            """,
            (patron,),
        )
        rows = cur.fetchall()
        conn.close()
        return rows
