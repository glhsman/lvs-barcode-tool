# 🏷️ Drinkport-Barcode – Python Edition v1.5

Ein professioneller Etikett-Editor mit Datenbankanbindung, Barcode-Integration und Python/Tkinter-Frontend.

## Neu in Version 1.5

- **WYSIWYG Etiketten-Editor:** Vollständige Überarbeitung der Vorschau zur Beseitigung von Skalierungsproblemen zwischen Editor und Druck.
- **Präzisere Formatierung:** Verbesserte Handhabung von Schriftarten, Textausrichtung und Stilvorgaben.
- **Integrierte Hilfe:** Direkter Zugriff auf das Benutzerhandbuch (`HANDBUCH.html`) aus der Anwendung heraus (Menü Hilfe).
- **Setup-Optimierung:** Handbuch wird nun automatisch mitinstalliert und im Paket ausgeliefert.

## Verfügbare Versionen

- **Windows Standalone:** [dist/Drinkport-Barcode_Setup.exe](dist/Drinkport-Barcode_Setup.exe) – Installierbare EXE für Windows 64-bit
- **Source Code:** Für Entwicklung und Anpassungen: Python 3.9+ erforderlich

## Voraussetzungen (für Development)

- Python 3.9 oder neuer
- Zugriff auf die MariaDB-Datenbank `barcode`

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

Etikett-Templates in `label_templates.json` anpassen (liegt neben der EXE bzw. im Projektordner). Neue Templates können ohne Code-Änderung ergänzt werden – das Programm lädt die Datei bei jedem Öffnen des Format-Dialogs neu.

## Einrichtung (einmalig)

```powershell
# Optional: virtuelle Umgebung anlegen
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Abhängigkeiten installieren (inkl. sv-ttk für das UI-Theme)
pip install -r requirements.txt

# Falls sv-ttk fehlt, einzeln nachinstallieren:
# pip install sv-ttk

# Datenbank-Schema anlegen (Tabellen in bestehender DB erstellen)
python db_setup.py
```

## Anwendung starten

### Windows (via Installer)
Windows Installer starten: `Drinkport-Barcode_Setup.exe`

### Development (via Python)
```powershell
python main.py
```

## Verbindung testen

```powershell
python -c "from db.connection import get_connection; c = get_connection(); print('Verbindung OK'); c.close()"
```

## Build (für Entwickler)

Standalone EXE unter Windows erstellen:
```cmd
BUILD_DRINKPORT_BARCODE.bat
```
✓ Setzt automatisch alle Abhängigkeiten auf
✓ PyInstaller kompiliert die App zu `dist/Drinkport-Barcode/`
✓ Inno Setup erstellt das Installer-Setup
