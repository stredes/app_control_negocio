# control_negocio/verificar_db.py

from app.db.database import init_db, DB_PATH, get_connection
import sqlite3

def verificar_tablas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = cur.fetchall()
    conn.close()

    if not tablas:
        print("⚠️  La base de datos no contiene ninguna tabla.")
    else:
        print("📋 Tablas existentes en la base de datos:")
        for tabla in tablas:
            print(f" - {tabla[0]}")

if __name__ == "__main__":
    print("🛠 Ejecutando init_db()...")
    init_db()
    print("✅ init_db ejecutado.")
    verificar_tablas()
