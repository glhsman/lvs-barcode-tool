@echo off
setlocal
color 0E
echo ==================================================
echo BUILD: Drinkport-Barcode Admin-Tool
echo ==================================================
echo.

:: 1. Aufräumen
echo 1. Raeume temporaere Build-Reste auf...
if exist "dist\Drinkport-Admin" rmdir /s /q "dist\Drinkport-Admin"

echo.
:: 2. Abhängigkeiten prüfen
if exist .venv\Scripts\python.exe (
    set PY_EXE=.venv\Scripts\python.exe
) else (
    set PY_EXE=python
)
%PY_EXE% -m pip install pyinstaller sv-ttk mysql-connector-python pillow --quiet

echo.
:: 3. EXE erstellen
echo 3. Erstelle Admin-Tool (dist/Drinkport-Admin)...
%PY_EXE% -m PyInstaller --noconfirm --noconsole --onedir ^
    --name="Drinkport-Admin" ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
    --collect-all sv_ttk ^
    --collect-all mysql.connector ^
    admin_main.py

if errorlevel 1 (
    echo.
    echo FEHLER: PyInstaller-Build fehlgeschlagen.
    pause
    exit /b 1
)

echo.
echo ==================================================
echo FERTIG! 
echo Das Admin-Tool liegt unter "dist/Drinkport-Admin".
echo.
echo WICHTIG: Die "config.ini" muss im selben Ordner 
echo wie die "Drinkport-Admin.exe" liegen.
echo ==================================================
pause
