# control_negocio/main.py
"""
Punto de entrada de la aplicación.

Mejoras:
- Inyección de servicios a la UI (documentos/impuestos/vencimientos).
- Validaciones y mensajes claros al inicializar la BD.
- Manejo de errores con salidas controladas.
- Código tipado y comentado para fácil mantención.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import os
import sys
import traceback

from app.ui.main_window import iniciar_app
from app.db.database import init_db, get_connection, DB_PATH

# Servicio funcional (módulo) ya implementado.
# Si migras a clases (DocumentosService/CalculadoraImpuestos), cambia acá.
from app.services import documentos_service as doc_svc


# =========================
# Utilidades de arranque
# =========================

def _print_header() -> None:
    print("🛠 Preparando entorno...")

def asegurar_directorio_db() -> Path:
    """
    Asegura que exista la carpeta 'app/data' donde vive la base SQLite.
    Retorna la ruta creada/existente.
    """
    data_path = Path(__file__).resolve().parent / "app" / "data"
    if not data_path.exists():
        os.makedirs(data_path, exist_ok=True)
        print(f"📁 Carpeta de base de datos creada: {data_path}")
    return data_path

def verificar_tablas() -> None:
    """
    Lista tablas existentes en la BD si el archivo existe.
    """
    if not DB_PATH.exists():
        print(f"❌ Base de datos no existe aún: {DB_PATH}")
        return

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = [row[0] for row in cur.fetchall()]
        if not tablas:
            print("⚠️  La base de datos no contiene ninguna tabla.")
        else:
            print("📋 Tablas disponibles:")
            for t in sorted(tablas):
                print(f"   • {t}")
    except Exception as e:
        print("❌ Error al verificar tablas:")
        print(f"   {e}")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

def _construir_servicios() -> Dict[str, Any]:
    """
    Crea el contenedor de servicios a inyectar en la UI.
    Si en el futuro usas ConfigLoader/Clases, ajusta aquí.
    """
    servicios: Dict[str, Any] = {
        # Servicio de documentos/impuestos/vencimientos (actualmente como módulo)
        "documentos_service": doc_svc,
    }
    return servicios


# =========================
# Main
# =========================

def main() -> int:
    """
    Orquestación de arranque:
    - Asegura carpeta de datos
    - Inicializa/migra la BD
    - Muestra tablas
    - Inyecta servicios y lanza UI
    """
    _print_header()

    data_path = asegurar_directorio_db()
    if not os.access(str(data_path), os.W_OK):
        print(f"❌ Sin permisos de escritura en: {data_path}")
        return 1

    try:
        init_db()
        print("✅ Base de datos inicializada/migrada.")
    except Exception as e:
        print("❌ Error inicializando la base de datos:")
        print(f"   {e}")
        traceback.print_exc()
        return 2

    verificar_tablas()

    # Construcción de servicios a compartir con las vistas
    servicios = _construir_servicios()

    print("🚀 Iniciando aplicación...")
    try:
        # Nota: iniciar_app debe aceptar iniciar_app(servicios=servicios)
        iniciar_app(servicios=servicios)
    except Exception as e:
        print("❌ Error ejecutando la UI:")
        print(f"   {e}")
        traceback.print_exc()
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
