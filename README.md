# Barcode Forge – Python Edition

## Voraussetzungen

- Python 3.10 oder neuer
- Zugriff auf die MariaDB-Datenbank `barcode`
- `zint.dll` im Projektordner (oder Pfad in `config.ini` unter `zint_dll` anpassen)
  - Download: https://sourceforge.net/projects/zint/

## Konfiguration

Zugangsdaten in `config.ini` eintragen:

```ini
[database]
host     = <Hostname>
port     = 3306
user     = <Benutzer>
password = <Passwort>
database = barcode
```

## Einrichtung (einmalig)

```powershell
# Optional: virtuelle Umgebung anlegen
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Abhängigkeiten installieren (inkl. ttkbootstrap für das UI-Design)
pip install -r requirements.txt

# Falls ttkbootstrap fehlt, einzeln nachinstallieren:
# pip install ttkbootstrap

# Datenbank-Schema anlegen (Tabellen in bestehender DB erstellen)
python db_setup.py
```

## Anwendung starten

```powershell
python main.py
```

## Verbindung testen

```powershell
python -c "from db.connection import get_connection; c = get_connection(); print('Verbindung OK'); c.close()"
```
