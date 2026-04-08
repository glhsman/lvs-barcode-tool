@echo off
setlocal
echo Baue Diagnose-Tool...
.\.venv\Scripts\python.exe -m PyInstaller --onefile --name="Drinkport-Diagnose" --collect-all mysql.connector db_test.py
echo.
echo FERTIG! Starte jetzt "dist/Drinkport-Diagnose.exe".
pause
