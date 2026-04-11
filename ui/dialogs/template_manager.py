"""Dialog zur Verwaltung (Ansehen, Löschen) der globalen Etiketten-Vorlagen."""
import tkinter as tk
from tkinter import ttk, messagebox
import db.repository as repo

class TemplateManagerDialog:
    def __init__(self, parent: tk.Widget):
        self._parent = parent
        self._win = tk.Toplevel(parent)
        self._win.title("Vorlagen verwalten")
        self._win.geometry("600x400")
        self._win.grab_set()
        self._win.transient(parent)
        
        self._build_ui()
        self._refresh()
        self._win.wait_window()

    def _build_ui(self):
        f = ttk.Frame(self._win, padding=12)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="Globale Etiketten-Vorlagen", font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # Container für Treeview und Scrollbar
        tree_frame = ttk.Frame(f)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self._tree = ttk.Treeview(tree_frame, columns=("name", "manufacturer", "product", "size"), show="headings", selectmode="browse")
        self._tree.heading("name",         text="Name")
        self._tree.heading("manufacturer", text="Hersteller")
        self._tree.heading("product",      text="Produkt")
        self._tree.heading("size",         text="Maße (mm)")
        
        self._tree.column("name",         width=200)
        self._tree.column("manufacturer", width=100)
        self._tree.column("product",      width=100)
        self._tree.column("size",         width=100)

        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        btn_f = ttk.Frame(f, padding=(0, 12, 0, 0))
        btn_f.pack(fill=tk.X)

        ttk.Button(btn_f, text="Löschen", command=self._delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_f, text="Schließen", command=self._win.destroy).pack(side=tk.RIGHT)

    def _refresh(self):
        for item in self._tree.get_children():
            self._tree.delete(item)
        
        templates = repo.list_global_templates()
        for name, data in templates:
            w = data.get("width_mm", 0)
            h = data.get("height_mm", 0)
            self._tree.insert("", tk.END, iid=name, values=(
                name,
                data.get("manufacturer", ""),
                data.get("product_name", ""),
                f"{w} x {h}"
            ))

    def _delete(self):
        sel = self._tree.selection()
        if not sel:
            return
        name = sel[0]
        if messagebox.askyesno("Vorlage löschen", f"Soll die Vorlage '{name}' wirklich gelöscht werden?", parent=self._win):
            try:
                repo.delete_global_template(name)
                self._refresh()
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Löschen: {e}", parent=self._win)
