# control_negocio/app/db/database.py

import sqlite3
from pathlib import Path

# Ruta absoluta a la base de datos SQLite
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "negocio.db"

def get_connection():
    """Devuelve una conexión a la base de datos."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Inicializa todas las tablas necesarias en la base de datos si no existen."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla de productos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            categoria TEXT,
            precio_compra REAL,
            precio_venta REAL,
            stock INTEGER DEFAULT 0
        )
    """)

    # Tabla de clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT,
            direccion TEXT,
            telefono TEXT
        )
    """)

    # Tabla de proveedores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            rut TEXT,
            direccion TEXT,
            telefono TEXT
        )
    """)

    # Tabla de compras
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor TEXT,
            producto TEXT,
            cantidad INTEGER,
            precio_unitario REAL
        )
    """)

    # Tabla de ventas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            producto TEXT,
            cantidad INTEGER,
            precio_unitario REAL
        )
    """)

    # Tabla de ingresos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingresos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT,
            monto REAL
        )
    """)

    # Tabla de gastos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT,
            monto REAL
        )
    """)

    # ✅ Tabla de facturas (integración con Finanzas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            proveedor TEXT,
            monto REAL,
            estado TEXT,
            fecha TEXT
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE
    )
    """)


    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada con todas las tablas.")
