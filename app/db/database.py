import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "negocio.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def migrar_proveedores_agregar_campos():
    """
    Añade las columnas razon_social, correo y comuna a proveedores
    sin eliminar datos existentes.
    """
    conn = get_connection()
    cur = conn.cursor()
    for col in ("razon_social", "correo", "comuna"):
        try:
            cur.execute(f"ALTER TABLE proveedores ADD COLUMN {col} TEXT;")
        except sqlite3.OperationalError:
            # La columna ya existe
            pass
    conn.commit()
    conn.close()

def migrar_compras_agregar_fecha():
    """
    Añade la columna fecha a la tabla compras sin eliminar datos existentes.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE compras ADD COLUMN fecha TEXT;")
    except sqlite3.OperationalError:
        # La columna ya existe
        pass
    conn.commit()
    conn.close()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1) Migraciones en caliente
    migrar_proveedores_agregar_campos()
    migrar_compras_agregar_fecha()

    # 2) Crear tablas si no existen
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
    print("✅ Base de datos inicializada y migraciones aplicadas.")
