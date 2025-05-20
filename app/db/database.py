import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "negocio.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Productos
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

    # Clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT,
            direccion TEXT,
            telefono TEXT
        )
    """)

    # Proveedores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT,
            direccion TEXT,
            telefono TEXT
        )
    """)

    # Compras
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor TEXT,
            producto TEXT,
            cantidad INTEGER,
            precio_unitario REAL,
            iva REAL,
            total REAL
        )
    """)

    # Órdenes de Venta
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

    # Ingresos
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

    # Gastos
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

    # Facturas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            proveedor TEXT,
            monto REAL,
            estado TEXT,
            fecha TEXT,
            tipo TEXT -- 'cliente' o 'proveedor'
        )
    """)

    # Categorías
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)

    # Movimientos de Inventario
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_producto TEXT,
            tipo TEXT,              -- entrada o salida
            cantidad INTEGER,
            ubicacion TEXT,
            metodo TEXT,            -- manual, escaner, orden_compra, etc.
            fecha TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada con todas las tablas.")
