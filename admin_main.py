"""
Drinkport-Barcode – Admin-Tool (Voller Editor-Zugriff).
"""
import sys
import tkinter as tk
from tkinter import messagebox
import sv_ttk
from main import apply_theme_profile

def main() -> None:
    root = None
    try:
        root = tk.Tk()
        root.title("Drinkport-Barcode – ADMIN-MODUS")
        root.withdraw()
        
        # Icon setzen
        import os
        if os.path.exists("icon.ico"):
            try:
                root.iconbitmap("icon.ico")
            except Exception:
                pass

        # Theme anwenden
        try:
            apply_theme_profile(root, "soft_plus")
            root.apply_theme_profile = lambda profile: apply_theme_profile(root, profile)
        except Exception as te:
            print(f"Theme-Fehler: {te}")
        
        from ui.admin_window import AdminWindow
        # Starte dediziertes ADMIN-FENSTER zur Vorlagenverwaltung
        AdminWindow(root)
        
        root.deiconify()
        root.mainloop()
    except Exception as e:
        with open("admin_error_log.txt", "w") as f:
            import traceback
            f.write(traceback.format_exc())
        try:
            messagebox.showerror("Admin-Tool Fehler", f"Kritischer Fehler beim Starten:\n{e}")
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
