# control_negocio/main.py

import os
from pathlib import Path
from app.ui.main_window import iniciar_app
from app.db.database import init_db

def asegurar_directorio_db():
    data_path = Path(__file__).resolve().parent / "app" / "data"
    if not data_path.exists():
        os.makedirs(data_path)
        print(f"📁 Carpeta creada: {data_path}")

if __name__ == "__main__":
    asegurar_directorio_db()
    init_db()  # ← Esto debe ejecutarse antes de iniciar la app
    iniciar_app()
