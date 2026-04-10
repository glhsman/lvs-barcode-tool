@echo off
setlocal
color 0B
echo ==================================================
echo RADIKAL-BUILD: Drinkport-Barcode (v1.5)
echo ==================================================
echo.

:: 1. Aufräumen
echo 1. Raeume temporaere Build-Reste auf...
if exist build rmdir /s /q build
if exist "Drinkport-Barcode.spec" del /q "Drinkport-Barcode.spec"
if exist "dist\Drinkport-Barcode" rmdir /s /q "dist\Drinkport-Barcode"
if exist "dist\Drinkport-Barcode" (
    echo.
    echo FEHLER: Ordner "dist\Drinkport-Barcode" ist gesperrt.
    echo Bitte schliesse laufende Drinkport-Barcode.exe und ggf. geoeffnete Explorer-Fenster.
    pause
    exit /b 1
)

echo.
:: 2. Abhängigkeiten (nutzt das lokale .venv)
echo 2. Installiere/Pruefe Abhaengigkeiten...
if exist .venv\Scripts\python.exe (
    set PY_EXE=.venv\Scripts\python.exe
) else (
    set PY_EXE=python
)
%PY_EXE% -m pip install pyinstaller sv-ttk mariadb python-barcode qrcode pillow reportlab pywin32 --quiet
if errorlevel 1 (
    echo.
    echo FEHLER: Abhaengigkeiten konnten nicht installiert werden.
    pause
    exit /b 1
)

echo.
:: 3. EXE erstellen (Modernes Dark-Style)
echo 3. Erstelle App-Ordner (dist/Drinkport-Barcode)...
:: Wir nutzen --onedir für maximale Stabilitaet.
%PY_EXE% -m PyInstaller --noconfirm --noconsole --onedir ^
    --name="Drinkport-Barcode" ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
    --add-data "label_templates.json;." ^
    --add-data "HANDBUCH.html;." ^
    --collect-all sv_ttk ^
    --collect-all mysql.connector ^
    --hidden-import win32timezone ^
    main.py

if errorlevel 1 (
    echo.
    echo FEHLER: PyInstaller-Build fehlgeschlagen.
    pause
    exit /b 1
)

echo.
:: 4. Finale Dateien sicherstellen (Kopieren in den Root-Ordner für Inno Setup)
echo 4. Kopiere Handbuch und Vorlagen in den Programm-Ordner...
copy /y "HANDBUCH.html" "dist\Drinkport-Barcode\" >nul
copy /y "label_templates.json" "dist\Drinkport-Barcode\" >nul

echo.
echo ==================================================
echo FERTIG! 
echo Dein Programm-Ordner liegt unter "dist/Drinkport-Barcode".
echo Kopiere den gesamten Ordner auf andere Rechner.
echo Starte dort die "Drinkport-Barcode.exe" IM ORDNER.
echo.
echo WICHTIG: Die "config.ini" muss im selben Ordner 
echo wie die "Drinkport-Barcode.exe" liegen.
echo ==================================================
pause
