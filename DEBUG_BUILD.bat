@echo off
setlocal
color 0C
echo ==================================================
echo DEBUG-BUILD: Drinkport-Barcode (MIT KONSOLE)
echo ==================================================
echo.

:: 1. Aufräumen
if exist build rmdir /s /q build
if exist "dist\Drinkport-Barcode_debug.exe" del /q "dist\Drinkport-Barcode_debug.exe"

:: 2. Pfad festlegen
if exist .venv\Scripts\python.exe (
    set PY_EXE=.venv\Scripts\python.exe
) else (
    set PY_EXE=python
)

echo Baue Debug-EXE...
:: HINWEIS: Wir lassen --noconsole WEG, um Fehler zu sehen!
%PY_EXE% -m PyInstaller --onefile ^
    --name="Drinkport-Barcode_debug" ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
    --add-data "label_templates.json;." ^
    --add-data "HANDBUCH.html;." ^
    --collect-all sv_ttk ^
    --collect-all mysql.connector ^
    --hidden-import win32timezone ^
    main.py

echo.
echo FERTIG! Starte jetzt die "dist/Drinkport-Barcode_debug.exe" 
echo ueber ein CMD-Fenster oder achte auf die Ausgaben im schwarzen Fenster.
pause
