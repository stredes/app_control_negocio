# control_negocio/main.py

from app.ui.main_window import iniciar_app
from app.db.database import init_db, get_connection, DB_PATH
from pathlib import Path
import sqlite3
import os

def asegurar_directorio_db():
    data_path = Path(__file__).resolve().parent / "app" / "data"
    if not data_path.exists():
        os.makedirs(data_path)
        print(f"📁 Carpeta de base de datos creada: {data_path}")

def verificar_tablas():
    if not DB_PATH.exists():
        print(f"❌ Base de datos no existe: {DB_PATH}")
        return

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = cur.fetchall()
    conn.close()

    if not tablas:
        print("⚠️  La base de datos no contiene ninguna tabla.")
    else:
        print("📋 Tablas disponibles:")
        for t in tablas:
            print(f" - {t[0]}")

if __name__ == "__main__":
    print("🛠 Preparando entorno...")
    asegurar_directorio_db()
    init_db()
    print("✅ Base de datos inicializada.")
    verificar_tablas()
    print("🚀 Iniciando aplicación...")
    iniciar_app()
