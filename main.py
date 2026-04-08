"""
Drinkport-Barcode – Python Edition
Modernes Dark-Design für Zebra-Lagerbeschriftungen.
"""
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import sv_ttk


def _apply_soft_dark_tuning(root: tk.Tk, profile: str) -> None:
    """Dark-Mode-Abstimmung mit mehreren Helligkeitsprofilen."""
    style = ttk.Style(root)

    palettes = {
        "dark": {
            "base": "#2F3540",
            "fg": "#E6ECF5",
            "entry": "#3A4452",
            "button": "#465263",
            "button_active": "#526179",
            "tab": "#414C5A",
            "tab_selected": "#58677D",
            "tree": "#36414F",
            "tree_selected": "#677EA3",
            "heading": "#515D6C",
        },
        "soft": {
            "base": "#353C46",
            "fg": "#F0F4FA",
            "entry": "#414B58",
            "button": "#4B5666",
            "button_active": "#58667C",
            "tab": "#444F5D",
            "tab_selected": "#5E6C80",
            "tree": "#3C4654",
            "tree_selected": "#7088AE",
            "heading": "#586372",
        },
        "soft_plus": {
            "base": "#3F4652",
            "fg": "#F4F7FC",
            "entry": "#4B5564",
            "button": "#59667A",
            "button_active": "#66758D",
            "tab": "#566274",
            "tab_selected": "#71819A",
            "tree": "#4A5564",
            "tree_selected": "#7E97BD",
            "heading": "#667385",
        },
    }
    colors = palettes.get(profile, palettes["soft"])

    # Gesamtfenster und Standardfarben weiter aufhellen, Dark-Mode bleibt aktiv.
    root.configure(bg=colors["base"])
    style.configure(".", background=colors["base"], foreground=colors["fg"])
    style.configure("TFrame", background=colors["base"])
    style.configure("TLabel", background=colors["base"], foreground=colors["fg"])

    # Form-Elemente mit klareren Kontrasten.
    style.configure("TEntry", fieldbackground=colors["entry"], foreground="#F7FAFF")
    style.configure("TCombobox", fieldbackground=colors["entry"], foreground="#F7FAFF")

    # Buttons etwas heller, damit Werkzeugleisten besser lesbar sind.
    style.configure("TButton", background=colors["button"], foreground="#F6F9FF", padding=(10, 4))
    style.map(
        "TButton",
        background=[("pressed", colors["tab_selected"]), ("active", colors["button_active"])],
        foreground=[("disabled", "#B7C0CD")],
    )

    # Notebook/Tabs etwas heller als der Hintergrund, damit Bereiche besser getrennt sind.
    style.configure("TNotebook", background=colors["base"])
    style.configure("TNotebook.Tab", padding=(12, 6), background=colors["tab"], foreground="#F1F5FB")
    style.map("TNotebook.Tab", background=[("selected", colors["tab_selected"]), ("active", colors["button_active"])])

    # Gruppenboxen sichtbarer machen.
    style.configure("TLabelframe", background=colors["base"], borderwidth=1)
    style.configure("TLabelframe.Label", background=colors["base"], foreground=colors["fg"])

    # Tabellenbereich: weniger schwarz, dafuer hoehere Textkontraste.
    style.configure(
        "Treeview",
        background=colors["tree"],
        fieldbackground=colors["tree"],
        foreground="#F8FBFF",
        borderwidth=0,
        rowheight=25,
    )
    style.map(
        "Treeview",
        background=[("selected", colors["tree_selected"])],
        foreground=[("selected", "#FFFFFF")],
    )
    style.configure("Treeview.Heading", background=colors["heading"], foreground="#F8FBFF")


def apply_theme_profile(root: tk.Tk, profile: str) -> None:
    """Aktiviert Dark-Mode plus gewaehltes Lesbarkeitsprofil."""
    sv_ttk.set_theme("dark")
    _apply_soft_dark_tuning(root, profile)
    root.theme_profile = profile


def main() -> None:
    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        
        # Sun Valley Theme auf 'dark' stellen
        try:
            apply_theme_profile(root, "soft_plus")
            root.apply_theme_profile = lambda profile: apply_theme_profile(root, profile)
        except Exception as te:
            print(f"Theme-Fehler (ignoriert): {te}")
        
        from ui.main_window import MainWindow
        MainWindow(root)
        root.deiconify()
        root.mainloop()
    except Exception as e:
        if root is not None:
            try:
                root.deiconify()
            except Exception:
                pass
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
