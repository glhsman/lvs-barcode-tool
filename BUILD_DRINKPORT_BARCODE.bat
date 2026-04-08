@echo off
setlocal
color 0B
echo ==================================================
echo RADIKAL-BUILD: Drinkport-Barcode (v1.0)
echo ==================================================
echo.

:: 1. Aufräumen
echo 1. Raeume temporaere Build-Reste auf...
if exist build rmdir /s /q build
if exist "Drinkport-Barcode.spec" del /q "Drinkport-Barcode.spec"
if exist "dist\Drinkport-Barcode.exe" del /q "dist\Drinkport-Barcode.exe"

echo.
:: 2. Abhängigkeiten (nutzt das lokale .venv)
echo 2. Installiere/Pruefe Abhaengigkeiten...
if exist .venv\Scripts\python.exe (
    set PY_EXE=.venv\Scripts\python.exe
) else (
    set PY_EXE=python
)
%PY_EXE% -m pip install pyinstaller sv-ttk mariadb python-barcode qrcode pillow pywin32 --quiet

echo.
:: 3. EXE erstellen (Modernes Dark-Style)
echo 3. Erstelle App-Ordner (dist/Drinkport-Barcode)...
:: Wir nutzen --onedir für maximale Stabilitaet.
%PY_EXE% -m PyInstaller --noconsole --onedir ^
    --name="Drinkport-Barcode" ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
    --collect-all sv_ttk ^
    --collect-all mysql.connector ^
    --hidden-import win32timezone ^
    main.py

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
