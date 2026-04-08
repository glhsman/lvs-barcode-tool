"""MariaDB-Verbindungspool (mysql-connector-python)."""
from __future__ import annotations

import mysql.connector
from mysql.connector import pooling
import app_config

_pool: pooling.MySQLConnectionPool | None = None


def get_connection() -> Optional[mysql.connector.MySQLConnection]:
    try:
        cfg = app_config.get_db_config()
        # use_pure=True zwingt den Treiber, auf fehleranfaellige C-Erweiterungen 
        # zu verzichten. Das rettet uns in der EXE-Umgebung!
        conn = mysql.connector.connect(**cfg, use_pure=True)
        return conn
    except Exception as e:
        print(f"Datenbank-Verbindungsfehler: {e}")
        return None


def test_connection() -> str:
    """Gibt Serverversion zurück oder wirft eine Exception."""
    conn = get_connection()
    if conn is None:
        return "Nicht verbunden"
    try:
        cur = conn.cursor()
        cur.execute("SELECT VERSION()")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        return version
    except Exception:
        return "Fehler beim Lesen der Version"
