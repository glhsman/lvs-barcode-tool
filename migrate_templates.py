"""
Migration der Etiketten-Vorlagen von label_templates.json in die MariaDB-Datenbank.
"""
import json
import configparser
from pathlib import Path
import mysql.connector

# Pfade
BASE_DIR = Path(__file__).parent
JSON_FILE = BASE_DIR / "label_templates.json"
CFG_FILE = BASE_DIR / "config.ini"

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
    if not JSON_FILE.exists():
        print(f"Fehler: {JSON_FILE} nicht gefunden.")
        return

    print(f"Lese Vorlagen aus {JSON_FILE} ...")
    with JSON_FILE.open(encoding="utf-8") as f:
        templates = json.load(f)

    db_params = _load_cfg()
    print(f"Verbinde mit Datenbank {db_params['database']} ...")
    try:
        conn = mysql.connector.connect(**db_params)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Verbindungsfehler: {e}")
        return

    print(f"Importiere {len(templates)} Vorlagen ...")
    success_count = 0
    
    insert_sql = """
        INSERT INTO global_label_templates 
        (name, manufacturer, product_name, width_mm, height_mm, 
         margin_top_mm, margin_bottom_mm, margin_left_mm, margin_right_mm, 
         `cols`, `rows`, col_gap_mm, row_gap_mm)
        VALUES (%(name)s, %(manufacturer)s, %(product_name)s, %(width_mm)s, %(height_mm)s, 
                %(margin_top_mm)s, %(margin_bottom_mm)s, %(margin_left_mm)s, %(margin_right_mm)s, 
                %(cols)s, %(rows)s, %(col_gap_mm)s, %(row_gap_mm)s)
        ON DUPLICATE KEY UPDATE 
            manufacturer=VALUES(manufacturer),
            product_name=VALUES(product_name),
            width_mm=VALUES(width_mm),
            height_mm=VALUES(height_mm),
            margin_top_mm=VALUES(margin_top_mm),
            margin_bottom_mm=VALUES(margin_bottom_mm),
            margin_left_mm=VALUES(margin_left_mm),
            margin_right_mm=VALUES(margin_right_mm),
            `cols`=VALUES(`cols`),
            `rows`=VALUES(`rows`),
            col_gap_mm=VALUES(col_gap_mm),
            row_gap_mm=VALUES(row_gap_mm)
    """

    for t in templates:
        try:
            cursor.execute(insert_sql, t)
            success_count += 1
        except Exception as e:
            print(f"  Fehler bei Vorlage '{t.get('name')}': {e}")

    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"OK: {success_count} Vorlagen erfolgreich importiert.")

if __name__ == "__main__":
    run()
