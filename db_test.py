import os
import sys
import traceback

print("=== DRINKPORT DB-DIAGNOSE ===")
print(f"Python Version: {sys.version}")
print(f"CWD: {os.getcwd()}")

try:
    print("\n1. Versuche App-Config zu laden...")
    import app_config
    cfg = app_config.get_db_config()
    print(f"   Konfiguration: {cfg['host']} @ {cfg['database']}")

    print("\n2. Versuche Datenbank-Treiber zu laden...")
    import mysql.connector
    print(f"   Treiber-Version: {mysql.connector.__version__}")

    print("\n3. Versuche Verbindung aufzubauen (PURE-MODUS)...")
    from db.connection import get_connection
    conn = get_connection()
    if conn:
        print("   ERFOLG: Verbindung steht!")
        conn.close()
    else:
        print("   FEHLER: Verbindung fehlgeschlagen (get_connection gab None zurueck).")

except Exception:
    print("\n!!! KRITISCHER FEHLER GEFUNDEN !!!")
    traceback.print_exc()

print("\nDiagnose beendet.")
input("Druecke ENTER zum Schliessen...")
