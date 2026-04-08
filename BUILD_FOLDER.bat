@echo off
setlocal
color 0B
echo ==================================================
echo PORTABLE-BUILD: Drinkport-Barcode (ALS ORDNER)
echo ==================================================
echo.

:: 1. Aufräumen
if exist build rmdir /s /q build
if exist "dist\Drinkport-Barcode" rmdir /s /q "dist\Drinkport-Barcode"

echo Baue den Drinkport-Barcode Ordner...
:: --onedir: Erstellt einen fertigen Ordner (statt einer Single-EXE)
:: Das ist viel schneller zu starten und stabiler auf PCs.
.\.venv\Scripts\python.exe -m PyInstaller --onedir ^
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
echo Dein Programm liegt im Ordner "dist/Drinkport-Barcode/".
echo Kopiere diesen ORDNER einfach auf andere Rechner.
echo Starte dort die "Drinkport-Barcode.exe" im Ordner!
echo ==================================================
pause
