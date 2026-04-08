"""
Drinkport-Barcode – Python Edition
Modernes Dark-Design für Zebra-Lagerbeschriftungen.
"""
import sys
import tkinter as tk
from tkinter import messagebox
import sv_ttk


def main() -> None:
    try:
        root = tk.Tk()
        
        # Sun Valley Theme auf 'dark' stellen
        try:
            sv_ttk.set_theme("dark")
        except Exception as te:
            print(f"Theme-Fehler (ignoriert): {te}")
        
        from ui.main_window import MainWindow
        MainWindow(root)
        root.mainloop()
    except Exception as e:
        # Fehler in Datei schreiben für EXE-Debugging
        with open("error_log.txt", "w") as f:
            import traceback
            f.write(traceback.format_exc())
        
        # Auch als Messagebox zeigen, falls möglich
        try:
            messagebox.showerror("Startfehler", f"Die Anwendung konnte nicht gestartet werden:\n\n{e}")
        except:
            pass
        
        print(f"CRITICAL STARTUP ERROR: {e}")
        input("\nDruecke ENTER zum Beenden...")


if __name__ == "__main__":
    main()
