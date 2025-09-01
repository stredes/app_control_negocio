# control_negocio/app/models/categoria.py
from __future__ import annotations

import sqlite3
from typing import List, Optional, Tuple

from app.db.database import get_connection


def _norm(nombre: str) -> str:
    """
    Normaliza el nombre de categoría:
    - quita espacios extremos,
    - colapsa espacios internos múltiples,
    - opcionalmente lo deja en Título (commented; descomenta si lo prefieres).
    """
    base = " ".join((nombre or "").strip().split())
    # base = base.title()  # <- si quieres "Bebidas Alcohólicas" en vez de "bebidas alcohólicas"
    return base


class Categoria:
    """
    Operaciones sobre la tabla `categorias`.

    Notas de integridad:
    - La columna `nombre` es UNIQUE (ver schema en database.py).
    - En la tabla `productos` el campo `categoria` es TEXT; no hay FK.
      Por eso, al renombrar una categoría, también actualizamos `productos.categoria`
      de forma atómica para mantener consistencia.
    """

    # ---------------------------
    # Lecturas
    # ---------------------------
    @staticmethod
    def listar() -> List[Tuple[int, str]]:
        """
        Devuelve lista de tuplas (id, nombre), ordenadas alfabéticamente.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
        datos = cur.fetchall()
        conn.close()
        return datos

    @staticmethod
    def obtener_por_id(id_categoria: int) -> Optional[Tuple[int, str]]:
        """
        Retorna (id, nombre) o None si no existe.
        """
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM categorias WHERE id = ?", (id_categoria,))
        row = cur.fetchone()
        conn.close()
        return row

    @staticmethod
    def obtener_por_nombre(nombre: str) -> Optional[Tuple[int, str]]:
        """
        Retorna (id, nombre) buscando por nombre normalizado; None si no existe.
        """
        nombre_n = _norm(nombre)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM categorias WHERE nombre = ?", (nombre_n,))
        row = cur.fetchone()
        conn.close()
        return row

    @staticmethod
    def existe(nombre: str) -> bool:
        """
        True si ya existe una categoría con ese nombre (normalizado).
        """
        return Categoria.obtener_por_nombre(nombre) is not None

    @staticmethod
    def contar_uso_en_productos(nombre: str) -> int:
        """
        Retorna cuántos productos referencian esta categoría por nombre.
        """
        nombre_n = _norm(nombre)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM productos WHERE categoria = ?", (nombre_n,))
        (count,) = cur.fetchone()
        conn.close()
        return int(count)

    # ---------------------------
    # Altas
    # ---------------------------
    @staticmethod
    def agregar(nombre: str) -> int:
        """
        Crea una categoría y devuelve su ID.
        - Normaliza nombre.
        - Maneja duplicado (UNIQUE) devolviendo el ID existente.
        """
        nombre_n = _norm(nombre)
        if not nombre_n:
            raise ValueError("El nombre de la categoría no puede estar vacío.")

        # Si ya existe, retorna su id (idempotencia)
        existente = Categoria.obtener_por_nombre(nombre_n)
        if existente:
            return int(existente[0])

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")
            cur.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre_n,))
            new_id = cur.lastrowid
            conn.commit()
            return int(new_id)
        except sqlite3.IntegrityError as e:
            # Si otra transacción la creó en paralelo (UNIQUE), recuperar su ID
            conn.rollback()
            row = Categoria.obtener_por_nombre(nombre_n)
            if row:
                return int(row[0])
            raise e
        finally:
            conn.close()

    # ---------------------------
    # Actualizaciones
    # ---------------------------
    @staticmethod
    def editar(id_categoria: int, nuevo_nombre: str) -> None:
        """
        Renombra la categoría (y actualiza `productos.categoria` de forma atómica).
        Reglas:
        - Normaliza nombre.
        - Si el nombre no cambia, no hace nada.
        - Si ya existe otra categoría con el mismo nuevo nombre -> error claro.
        """
        nuevo_n = _norm(nuevo_nombre)
        if not nuevo_n:
            raise ValueError("El nuevo nombre de la categoría no puede estar vacío.")

        # Datos actuales
        actual = Categoria.obtener_por_id(id_categoria)
        if not actual:
            raise ValueError(f"Categoría con id={id_categoria} no existe.")
        _, nombre_actual = actual
        if nombre_actual == nuevo_n:
            return  # no-op

        # Verificar colisión de nombre
        colision = Categoria.obtener_por_nombre(nuevo_n)
        if colision and int(colision[0]) != int(id_categoria):
            raise ValueError(f"Ya existe la categoría '{nuevo_n}'.")

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            # 1) renombrar categoría
            cur.execute("UPDATE categorias SET nombre = ? WHERE id = ?", (nuevo_n, id_categoria))

            # 2) actualizar productos que referencian por texto
            cur.execute(
                "UPDATE productos SET categoria = ? WHERE categoria = ?",
                (nuevo_n, nombre_actual),
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
    def eliminar(id_categoria: int, forzar: bool = False) -> None:
        """
        Elimina la categoría. Si `forzar=False`, no permite borrar si hay productos
        que la usan. Si `forzar=True`, la elimina y **desasigna** la categoría de productos
        (pone NULL) de forma atómica.

        Recomendación: dejar forzar=False en UI y ofrecer un mensaje claro al usuario.
        """
        actual = Categoria.obtener_por_id(id_categoria)
        if not actual:
            # idempotente: nada que borrar
            return
        _, nombre_actual = actual

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN")

            # ¿Hay productos que la referencian?
            cur.execute("SELECT COUNT(*) FROM productos WHERE categoria = ?", (nombre_actual,))
            (count,) = cur.fetchone()
            count = int(count)

            if count > 0 and not forzar:
                conn.rollback()
                raise ValueError(
                    f"No se puede eliminar la categoría '{nombre_actual}' "
                    f"porque {count} producto(s) la utilizan."
                )

            if count > 0 and forzar:
                # Desasigna categoría: setear NULL (o cadena vacía, si prefieres)
                cur.execute(
                    "UPDATE productos SET categoria = NULL WHERE categoria = ?",
                    (nombre_actual,),
                )

            # Borra categoría
            cur.execute("DELETE FROM categorias WHERE id = ?", (id_categoria,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
