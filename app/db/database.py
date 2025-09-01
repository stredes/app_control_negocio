# app/db/database.py
"""
Gestión de base de datos SQLite (init + migraciones idempotentes).

Mejoras:
- PRAGMA (foreign_keys, WAL, synchronous) para robustez y rendimiento.
- Helpers para comprobar/agregar columnas e índices sin romper datos.
- Migraciones para lógica chilena:
  - facturas: doc_tipo, neto, iva, retencion, total, vencimiento
  - ordenes_venta: doc_tipo, neto, retencion, total (asegura)
  - compras: doc_tipo, neto, retencion, total, vencimiento
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "negocio.db"


# -------------------------------------------------
# Conexión (con PRAGMA de robustez y rendimiento)
# -------------------------------------------------
def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # PRAGMA recomendados (seguros en SQLite embebido)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")   # respeta FKs si las defines en el futuro
        conn.execute("PRAGMA journal_mode = WAL;")  # mejor concurrencia/recuperación
        conn.execute("PRAGMA synchronous = NORMAL;")# equilibrio rendimiento/seguridad
    except Exception:
        # Si la versión de SQLite no soporta alguno, lo ignoramos
        pass
    return conn


# -------------------------------------------------
# Migraciones previas existentes (compatibilidad)
# -------------------------------------------------
def migrar_proveedores_agregar_campos() -> None:
    """Añade razon_social, correo, comuna a proveedores (si faltan)."""
    conn = get_connection()
    cur = conn.cursor()
    for col in ("razon_social", "correo", "comuna"):
        try:
            cur.execute(f"ALTER TABLE proveedores ADD COLUMN {col} TEXT;")
        except sqlite3.OperationalError:
            pass  # ya existe
    conn.commit()
    conn.close()


def migrar_compras_agregar_fecha() -> None:
    """Añade fecha a compras (si falta)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE compras ADD COLUMN fecha TEXT;")
    except sqlite3.OperationalError:
        pass  # ya existe
    conn.commit()
    conn.close()


# -------------------------------------------------
# Helpers de migración idempotente
# -------------------------------------------------
def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cur.fetchall()]


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, decl: str) -> None:
    if not _has_column(conn, table, column):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")


def _create_index_if_missing(conn: sqlite3.Connection, name: str, table: str, cols: Iterable[str]) -> None:
    try:
        conn.execute(f"CREATE INDEX {name} ON {table} ({', '.join(cols)})")
    except Exception:
        # ya existe o no procede; lo ignoramos
        pass


def _create_basic_indices(conn: sqlite3.Connection) -> None:
    """Índices comunes que aceleran las vistas/consultas típicas."""
    # Productos
    _create_index_if_missing(conn, "idx_productos_nombre", "productos", ["nombre"])
    # Compras
    _create_index_if_missing(conn, "idx_compras_producto", "compras", ["producto"])
    _create_index_if_missing(conn, "idx_compras_fecha", "compras", ["fecha"])
    _create_index_if_missing(conn, "idx_compras_doc_tipo", "compras", ["doc_tipo"])
    # Ventas
    _create_index_if_missing(conn, "idx_ov_producto", "ordenes_venta", ["producto"])
    _create_index_if_missing(conn, "idx_ov_fecha", "ordenes_venta", ["fecha"])
    _create_index_if_missing(conn, "idx_ov_doc_tipo", "ordenes_venta", ["doc_tipo"])
    # Facturas (algunos ya se crean en migrate_schema, pero reforzamos aquí también)
    _create_index_if_missing(conn, "idx_facturas_estado", "facturas", ["estado"])
    _create_index_if_missing(conn, "idx_facturas_venc", "facturas", ["vencimiento"])
    _create_index_if_missing(conn, "idx_facturas_tipo", "facturas", ["tipo"])
    _create_index_if_missing(conn, "idx_facturas_doc_tipo", "facturas", ["doc_tipo"])


# -------------------------------------------------
# Migraciones “lógica Chile”
# -------------------------------------------------
def migrate_schema(conn: sqlite3.Connection) -> None:
    """
    Idempotente: asegura columnas usadas por los modelos extendidos y crea índices útiles.
    """
    conn.execute("BEGIN")
    try:
        # --- FACTURAS ---
        _add_column_if_missing(conn, "facturas", "doc_tipo",    "TEXT")
        _add_column_if_missing(conn, "facturas", "neto",        "REAL DEFAULT 0")
        _add_column_if_missing(conn, "facturas", "iva",         "REAL DEFAULT 0")
        _add_column_if_missing(conn, "facturas", "retencion",   "REAL DEFAULT 0")
        _add_column_if_missing(conn, "facturas", "total",       "REAL DEFAULT 0")
        _add_column_if_missing(conn, "facturas", "vencimiento", "TEXT")
        _create_index_if_missing(conn, "idx_facturas_estado",   "facturas", ["estado"])
        _create_index_if_missing(conn, "idx_facturas_venc",     "facturas", ["vencimiento"])
        _create_index_if_missing(conn, "idx_facturas_tipo",     "facturas", ["tipo"])
        _create_index_if_missing(conn, "idx_facturas_doc_tipo", "facturas", ["doc_tipo"])

        # --- ORDENES_VENTA ---
        _add_column_if_missing(conn, "ordenes_venta", "doc_tipo",  "TEXT")
        _add_column_if_missing(conn, "ordenes_venta", "neto",      "REAL DEFAULT 0")
        _add_column_if_missing(conn, "ordenes_venta", "retencion", "REAL DEFAULT 0")
        _add_column_if_missing(conn, "ordenes_venta", "total",     "REAL DEFAULT 0")
        _create_index_if_missing(conn, "idx_ov_doc_tipo", "ordenes_venta", ["doc_tipo"])

        # --- COMPRAS ---
        _add_column_if_missing(conn, "compras", "doc_tipo",    "TEXT")
        _add_column_if_missing(conn, "compras", "neto",        "REAL DEFAULT 0")
        _add_column_if_missing(conn, "compras", "retencion",   "REAL DEFAULT 0")
        _add_column_if_missing(conn, "compras", "total",       "REAL DEFAULT 0")
        _add_column_if_missing(conn, "compras", "vencimiento", "TEXT")
        _create_index_if_missing(conn, "idx_compras_doc_tipo", "compras", ["doc_tipo"])

        # Índices adicionales recomendados
        _create_basic_indices(conn)

        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


# -------------------------------------------------
# Inicialización + schema base
# -------------------------------------------------
def init_db() -> None:
    """
    - Ejecuta migraciones previas (compatibilidad con tu proyecto original).
    - Crea tablas base si no existen.
    - Aplica migraciones “lógica Chile” y crea índices.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1) Migraciones previas (compatibilidad)
    migrar_proveedores_agregar_campos()
    migrar_compras_agregar_fecha()

    # 2) Tablas base
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT,
            precio_compra REAL,
            precio_venta REAL,
            stock INTEGER DEFAULT 0,
            codigo_interno TEXT,
            codigo_externo TEXT,
            iva REAL,
            ubicacion TEXT,
            fecha_vencimiento TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT,
            direccion TEXT,
            telefono TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT,
            direccion TEXT,
            telefono TEXT,
            razon_social TEXT,
            correo TEXT,
            comuna TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor TEXT,
            producto TEXT,
            cantidad INTEGER,
            precio_unitario REAL,
            iva REAL,
            total REAL,
            fecha TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ordenes_venta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            producto TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            iva REAL NOT NULL,
            total REAL NOT NULL,
            fecha TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingresos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            descripcion TEXT,
            monto REAL,
            estado TEXT,
            fecha TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            descripcion TEXT,
            monto REAL,
            estado TEXT,
            fecha TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            proveedor TEXT,
            monto REAL,
            estado TEXT,
            fecha TEXT,
            tipo TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_producto TEXT,
            tipo TEXT,
            cantidad INTEGER,
            ubicacion TEXT,
            metodo TEXT,
            fecha TEXT
        )
    """)

    conn.commit()
    conn.close()

    # 3) Migraciones extendidas (idempotentes) + índices
    conn = get_connection()
    migrate_schema(conn)
    conn.close()

    print(f"✅ Base de datos inicializada y migraciones aplicadas. Ruta: {DB_PATH}")
