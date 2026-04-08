# build_exe.py
import os
import subprocess
import shutil

# --- Einstellungen ---
PROJECT_NAME = "Drinkport-Barcode"
MAIN_SCRIPT = "main.py"
ICON_FILE = None # Falls ein .ico vorhanden ist, hier eintragen

# --- Vorbereitung ---
print(f"Baue {PROJECT_NAME} EXE...")

# Da sv-ttk ein spezielles Theme ist, müssen wir den Ordner finden.
import sv_ttk
sv_ttk_dir = os.path.dirname(sv_ttk.__file__)
# Das Theme liegt im Unterordner 'theme'
theme_path = os.path.join(sv_ttk_dir, "theme")

# Befehl für PyInstaller
# --onefile: Alles in eine EXE
# --noconsole: Kein schwarzes Fenster im Hintergrund
# --add-data: Füge das Sun Valley Theme hinzu (Syntax: Quelle;Ziel auf Windows)
# --collect-all: Sammelt alle Hooks für komplexe Bibliotheken
cmd = [
    "pyinstaller",
    "--noconsole",
    "--onefile",
    f"--name={PROJECT_NAME}",
    f"--add-data={theme_path};sv_ttk/theme", 
    "--collect-all=mysql.connector",
    "--collect-all=sv_ttk",
    "--hidden-import=win32timezone", # Oft vergessen von PyInstaller
    MAIN_SCRIPT
]

# Ausführen
subprocess.run(cmd)

print("\n--- FERTIG! ---")
print(f"Die fertige Datei findest du im Ordner 'dist/{PROJECT_NAME}.exe'.")
print("Bitte stelle sicher, dass eine 'config.ini' im selben Ordner wie die .exe liegt.")
