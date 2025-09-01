# control_negocio/app/models/proveedor.py
from __future__ import annotations

import re
from typing import List, Optional, Tuple, Any, Dict

from app.db.database import get_connection

Row = Tuple[
    int,            # id
    str,            # nombre
    Optional[str],  # rut
    Optional[str],  # direccion
    Optional[str],  # telefono
    Optional[str],  # razon_social
    Optional[str],  # correo
    Optional[str],  # comuna
]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# -----------------------------
# Helpers de validación/normalización
# -----------------------------
def _norm(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = str(s).strip()
    return s or None


def _valid_email(email: Optional[str]) -> bool:
    if email is None or email == "":
        return True
    return bool(EMAIL_RE.match(email))


def _clean_rut(rut: Optional[str]) -> Optional[str]:
    """
    Limpia el RUT a formato base: sin puntos, con guión y dígito verificador.
    Acepta '12.345.678-5' o '123456785' -> '12345678-5'
    """
    if rut is None:
        return None
    s = rut.strip().lower().replace(".", "").replace(" ", "")
    if not s:
        return None
    # Si viene sin guión, lo insertamos antes del último carácter
    if "-" not in s and len(s) >= 2:
        s = f"{s[:-1]}-{s[-1]}"
    return s


def _valid_rut(rut: Optional[str]) -> bool:
    """
    Valida DV (módulo 11). Permite K/k como DV.
    Si viene vacío/None, lo consideramos válido (campo opcional).
    """
    if rut is None or rut == "":
        return True
    r = _clean_rut(rut)
    if not r or "-" not in r:
        return False
    num, dv = r.split("-", 1)
    if not num.isdigit():
        return False
    dv = dv.lower()
    # cálculo módulo 11
    factors = [2, 3, 4, 5, 6, 7]
    acc = 0
    f_idx = 0
    for ch in reversed(num):
        acc += int(ch) * factors[f_idx]
        f_idx = (f_idx + 1) % len(factors)
    mod = 11 - (acc % 11)
    dv_calc = {10: "k", 11: "0"}.get(mod, str(mod))
    return dv == dv_calc


def _validate_fields(nombre: Optional[str], rut: Optional[str], correo: Optional[str]) -> None:
    if not nombre or not nombre.strip():
        raise ValueError("El nombre del proveedor es obligatorio.")
    if not _valid_rut(rut):
        raise ValueError("RUT inválido.")
    if not _valid_email(correo):
        raise ValueError("Correo inválido.")


# -----------------------------
# Modelo
# -----------------------------
class Proveedor:
    # ---------------
    # Altas
    # ---------------
    @staticmethod
    def crear(
        nombre: str,
        rut: Optional[str],
        direccion: Optional[str],
        telefono: Optional[str],
        razon_social: Optional[str],
        correo: Optional[str],
        comuna: Optional[str],
    ) -> int:
        """
        Crea un proveedor. Valida nombre, RUT (si se provee) y correo (si se provee).
        """
        nombre = _norm(nombre) or ""
        rut = _clean_rut(_norm(rut))
        direccion = _norm(direccion)
        telefono = _norm(telefono)
        razon_social = _norm(razon_social)
        correo = _norm(correo)
        comuna = _norm(comuna)

        _validate_fields(nombre, rut, correo)

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO proveedores (nombre, rut, direccion, telefono, razon_social, correo, comuna)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (nombre, rut, direccion, telefono, razon_social, correo, comuna),
            )
            new_id = cur.lastrowid
            conn.commit()
            return int(new_id)
        finally:
            conn.close()

    @staticmethod
    def upsert_por_rut(
        nombre: str,
        rut: Optional[str],
        direccion: Optional[str] = None,
        telefono: Optional[str] = None,
        razon_social: Optional[str] = None,
        correo: Optional[str] = None,
        comuna: Optional[str] = None,
    ) -> int:
        """
        Si existe un proveedor con ese RUT, actualiza campos no vacíos.
        Si no, lo crea. Si rut es None/vacío, crea normal.
        """
        rut_n = _clean_rut(_norm(rut))
        if not rut_n:
            return Proveedor.crear(nombre, rut, direccion, telefono, razon_social, correo, comuna)

        existente = Proveedor.obtener_por_rut(rut_n)
        if not existente:
            return Proveedor.crear(nombre, rut_n, direccion, telefono, razon_social, correo, comuna)

        # actualización parcial
        id_prov = existente[0]
        patch: Dict[str, Any] = {}
        if nombre and nombre.strip():
            patch["nombre"] = _norm(nombre)
        for k, v in {
            "direccion": direccion,
            "telefono": telefono,
            "razon_social": razon_social,
            "correo": correo,
            "comuna": comuna,
        }.items():
            v2 = _norm(v)
            if v2:
                patch[k] = v2

        if patch:
            Proveedor.actualizar_parcial(id_prov, **patch)
        return id_prov

    # ---------------
    # Lecturas
    # ---------------
    @staticmethod
    def listar_todos() -> List[Row]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, nombre, rut, direccion, telefono, razon_social, correo, comuna
                FROM proveedores
                ORDER BY LOWER(nombre) ASC, id ASC
                """
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def listar_paginado(limit: int = 50, offset: int = 0) -> List[Row]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, nombre, rut, direccion, telefono, razon_social, correo, comuna
                FROM proveedores
                ORDER BY LOWER(nombre) ASC, id ASC
                LIMIT ? OFFSET ?
                """,
                (int(limit), int(offset)),
            )
            return cur.fetchall()
        finally:
            conn.close()

    @staticmethod
    def obtener_por_id(id_proveedor: int) -> Optional[Row]:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, nombre, rut, direccion, telefono, razon_social, correo, comuna
                FROM proveedores
                WHERE id = ?
                """,
                (id_proveedor,),
            )
            return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def obtener_por_rut(rut: str) -> Optional[Row]:
        rut_n = _clean_rut(_norm(rut))
        if not rut_n:
            return None
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, nombre, rut, direccion, telefono, razon_social, correo, comuna
                FROM proveedores
                WHERE rut = ?
                """,
                (rut_n,),
            )
            return cur.fetchone()
        finally:
            conn.close()

    @staticmethod
    def buscar_por_nombre(nombre: str) -> List[Row]:
        patron = f"%{(_norm(nombre) or '')}%"
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, nombre, rut, direccion, telefono, razon_social, correo, comuna
                FROM proveedores
                WHERE LOWER(nombre) LIKE LOWER(?)
                ORDER BY LOWER(nombre) ASC, id ASC
                """,
                (patron,),
            )
            return cur.fetchall()
        finally:
            conn.close()

    # ---------------
    # Ediciones
    # ---------------
    @staticmethod
    def editar(
        id_proveedor: int,
        nombre: str,
        rut: Optional[str],
        direccion: Optional[str],
        telefono: Optional[str],
        razon_social: Optional[str],
        correo: Optional[str],
        comuna: Optional[str],
    ) -> None:
        """
        Reemplazo completo (modo tradicional).
        """
        nombre = _norm(nombre) or ""
        rut = _clean_rut(_norm(rut))
        direccion = _norm(direccion)
        telefono = _norm(telefono)
        razon_social = _norm(razon_social)
        correo = _norm(correo)
        comuna = _norm(comuna)

        _validate_fields(nombre, rut, correo)

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE proveedores SET
                    nombre = ?, rut = ?, direccion = ?, telefono = ?,
                    razon_social = ?, correo = ?, comuna = ?
                WHERE id = ?
                """,
                (nombre, rut, direccion, telefono, razon_social, correo, comuna, id_proveedor),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def actualizar_parcial(id_proveedor: int, **campos) -> None:
        """
        Patch selectivo. Valida si se incluye 'nombre', 'rut' o 'correo'.
        Ej: actualizar_parcial(3, correo='proveedor@acme.cl', comuna='Santiago')
        """
        if not campos:
            return

        # Normalizar entrantes
        norm_fields: Dict[str, Any] = {}
        for k, v in campos.items():
            if k == "rut":
                norm_fields[k] = _clean_rut(_norm(v))
            else:
                norm_fields[k] = _norm(v)

        # Validaciones de negocio si vienen esos campos
        nombre = norm_fields.get("nombre", None)
        rut = norm_fields.get("rut", None)
        correo = norm_fields.get("correo", None)
        if nombre is not None or rut is not None or correo is not None:
            _validate_fields(nombre if nombre is not None else "dummy", rut, correo)
            # Nota: usamos "dummy" para no requerir nombre cuando no se edita nombre.

        allowed = {"nombre", "rut", "direccion", "telefono", "razon_social", "correo", "comuna"}
        sets = []
        values = []
        for k, v in norm_fields.items():
            if k not in allowed:
                continue
            sets.append(f"{k} = ?")
            values.append(v)

        if not sets:
            return

        values.append(id_proveedor)

        sql = f"UPDATE proveedores SET {', '.join(sets)} WHERE id = ?"
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, tuple(values))
            conn.commit()
        finally:
            conn.close()

    # ---------------
    # Borrado
    # ---------------
    @staticmethod
    def eliminar(id_proveedor: int) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM proveedores WHERE id = ?", (id_proveedor,))
            conn.commit()
        finally:
            conn.close()
