# 🏷️ Drinkport-Barcode – Python Edition v1.6

Ein leistungsstarker WYSIWYG Etikett-Editor mit Datenbankanbindung, spezialisiert auf Lagerbeschriftung und Barcodes.

## ✨ Highlights in Version 1.6

- **🚀 Hochleistungs-CSV-Import:** Bis zu 20x schnellerer Import durch optimiertes Transaction-Batching.
- **⚡ Sitzungs-Modus:** Große Datenmengen flexibel "nur für diese Sitzung" laden, ohne die Datenbank zu füllen.
- **🖨️ Seriendruck (Batch Printing):** Drucken Sie hunderte oder tausende Etiketten in einem einzigen Druckauftrag.
- **🔍 Globale Schnellsuche:** Suchen und Springen zu Datensätzen direkt aus der Haupt-Symbolleiste.
- **📂 Pfad-Gedächtnis:** Merkt sich den letzten CSV-Speicherort für effiziente, tägliche Workflows.
- **🛠️ Feld-Management:** Automatische Neuerstellung von Datenbankfeldern direkt aus CSV-Headern.
- **📱 Optimierte UI:** Überarbeitete Dialoge und Fortschrittsanzeigen für flüssiges Arbeiten auch bei großen Datenmengen.

---

## 🏗️ Voraussetzungen (Development)

- **Python:** Version 3.9 oder neuer
- **Datenbank:** MariaDB oder MySQL Server
- **Betriebssystem:** Windows (für nativen GDI-Druck)

## ⚙️ Konfiguration

Tragen Sie Ihre DB-Zugangsdaten in der `config.ini` ein:

```ini
[database]
host     = <Hostname>
port     = 3306
user     = <Benutzer>
password = <Passwort>
database = drinkport_barcode

[app]
default_dpi = 203
username    = <Ihr_Kürzel>
```

Die Verwaltung und Gestaltung der Etiketten-Vorlagen erfolgt komfortabel über das separate Programm **Barcode-Admin**. Mit diesem Tool können Sie Felder hinzufügen, Barcodes positionieren und Styles definieren, ohne die `label_templates.json` manuell bearbeiten zu müssen.

Das Hauptprogramm lädt die Vorlagen automatisch bei jedem Öffnen des Format-Dialogs neu.

## 🚀 Einrichtung (Source-Installation)

```powershell
# 1. Virtuelle Umgebung anlegen
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Abhängigkeiten installieren
pip install -r requirements.txt

# 3. Datenbank-Schema initialisieren
python db_setup.py
```

## 🖥️ Anwendung starten

### Als Entwickler
```powershell
python main.py
```

### Als Endanwender (Windows)
Verwenden Sie den Installer: `dist/Drinkport-Barcode_Setup.exe` (falls gebaut).

## 🛠️ Build-Prozess (EXE & Installer)

Um eine eigenständige Windows-Anwendung inklusive Installer zu erstellen, führen Sie einfach die Batch-Datei aus:

```cmd
BUILD_DRINKPORT_BARCODE.bat
```
Dies führt folgende Schritte automatisch aus:
1. Prüft Python-Umgebung und Abhängigkeiten.
2. Kompiliert die App via **PyInstaller** zu einer Standalone-Verzeichnisstruktur.
3. Erstellt mit **Inno Setup** einen installationsfähigen Windows-Installer.

---

## 📚 Hilfe & Dokumentation
Zusätzliche Informationen zur Bedienung finden Sie im integrierten Benutzerhandbuch über das Menü **Hilfe -> Benutzerhandbuch**.
