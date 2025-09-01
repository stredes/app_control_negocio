# Archivo: tx.py
"""
Context manager de transacción para SQLite.
Requiere que app.db.database exponga get_conn() y que devuelva la MISMA conexión
por hilo/sesión (patrón de conexión global simple).
"""

from contextlib import contextmanager
from typing import Iterator
from app.db.database import get_conn  # Asegúrate que exista en tu proyecto


@contextmanager
def tx() -> Iterator:
    """
    Uso:
      with tx() as conn:
          conn.execute("INSERT ...")
          conn.execute("UPDATE ...")
    """
    conn = get_conn()
    try:
        conn.execute("BEGIN")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise
