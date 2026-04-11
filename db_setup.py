"""
Einmaliges DB-Setup-Skript.
Ausführen: python db_setup.py
"""
import sys
import configparser
from pathlib import Path

import mysql.connector

CFG_FILE    = Path(__file__).parent / "config.ini"
SCHEMA_FILE = Path(__file__).parent / "schema.sql"


def _load_cfg() -> dict:
    cfg = configparser.ConfigParser()
    cfg.read(CFG_FILE, encoding="utf-8")
    db = cfg["database"] if "database" in cfg else {}
    return {
        "host"    : db.get("host", "localhost"),
        "port"    : int(db.get("port", "3306")),
        "user"    : db.get("user", "root"),
        "password": db.get("password", ""),
        "database": db.get("database", "barcode"),
    }


def run() -> None:
    params = _load_cfg()
    print(f"Verbinde mit {params['host']}:{params['port']} als {params['user']} …")
    try:
        conn = mysql.connector.connect(**params)
    except mysql.connector.Error as exc:
        print(f"Verbindungsfehler: {exc}")
        sys.exit(1)

    sql = SCHEMA_FILE.read_text(encoding="utf-8")
    cursor = conn.cursor()
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt and not stmt.startswith("--"):
            try:
                cursor.execute(stmt)
            except mysql.connector.Error as exc:
                print(f"  Warnung: {exc}\n  SQL: {stmt[:100]}")
    conn.commit()
    cursor.close()
    conn.close()
    print("OK: Datenbank-Schema erfolgreich erstellt.")


if __name__ == "__main__":
    run()
