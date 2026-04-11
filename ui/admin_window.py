"""
Drinkport-Barcode – Dediziertes Admin-Fenster zur Vorlagenverwaltung.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import db.repository as repo
from models.types import LabelFormat

class AdminWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Drinkport-Barcode – VORLAGENVERWALTUNG (ADMIN)")
        
        # Icon setzen
        import os
        if os.path.exists("icon.ico"):
            try:
                self.root.iconbitmap("icon.ico")
            except Exception:
                pass

        # Fenstergröße
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        
        # Datenspeicher
        self._templates = []
        self._vars = {}
        self._current_template_name = None

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        # Haupt-Container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # PanedWindow für flexible Aufteilung
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # --- LINKER BEREICH: Liste ---
        list_container = ttk.Frame(paned, padding=(0, 0, 10, 0))
        paned.add(list_container, weight=1)

        ttk.Label(list_container, text="Vorlagendatenbank", font=("", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Treeview mit Scrollbar
        tree_frame = ttk.Frame(list_container)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self._tree = ttk.Treeview(tree_frame, columns=("spec"), show="headings", selectmode="browse")
        self._tree.heading("spec", text="Vorlage / Maße")
        self._tree.column("spec", width=250)
        
        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # --- RECHTER BEREICH: Editor-Formular ---
        right_container = ttk.Frame(paned, padding=(10, 0, 0, 0))
        paned.add(right_container, weight=2)

        ttk.Label(right_container, text="Details & Abmessungen", font=("", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # Scrollbarer Bereich für das Formular
        canvas_f = ttk.Frame(right_container)
        canvas_f.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(canvas_f, highlightthickness=0)
        form_sb = ttk.Scrollbar(canvas_f, orient=tk.VERTICAL, command=self._canvas.yview)
        
        self._form = ttk.Frame(self._canvas, padding=5)
        self._canvas_win = self._canvas.create_window((0, 0), window=self._form, anchor=tk.NW)
        
        self._canvas.configure(yscrollcommand=form_sb.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        form_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._form.bind("<Configure>", self._on_form_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        self._build_form_fields(self._form)

        # --- UNTERER BEREICH: Buttons ---
        btn_frame = ttk.Frame(main_frame, padding=(0, 15, 0, 0))
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(btn_frame, text="🗑 Ausgewählte Vorlage löschen", 
                   command=self._delete_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🧹 Felder leeren", 
                   command=self._clear_fields).pack(side=tk.LEFT, padx=5)
        
        # Rechtsbündig
        ttk.Button(btn_frame, text="💾 Änderungen speichern", 
                   command=self._save_changes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="✨ Als NEUE Vorlage speichern", 
                   command=self._save_as_new).pack(side=tk.RIGHT, padx=5)
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 0))

    def _build_form_fields(self, f):
        def row(p, lbl: str, attr: str, r: int, col: int = 0,
                from_: float = 0.0, to: float = 800.0, inc: float = 0.5) -> None:
            ttk.Label(p, text=lbl).grid(row=r, column=col * 3, sticky=tk.W, padx=(10, 2), pady=8)
            var = tk.DoubleVar(value=0.0)
            sb  = ttk.Spinbox(p, from_=from_, to=to, increment=inc, textvariable=var, width=12, format="%.2f")
            sb.grid(row=r, column=col * 3 + 1, sticky=tk.W, padx=5, pady=8)
            ttk.Label(p, text="mm").grid(row=r, column=col * 3 + 2, sticky=tk.W, padx=(0, 15), pady=8)
            self._vars[attr] = var

        # --- Stammdaten ---
        g1 = ttk.LabelFrame(f, text=" Basisdaten ", padding=15)
        g1.grid(row=0, column=0, columnspan=6, sticky=tk.EW, pady=10, padx=5)

        ttk.Label(g1, text="Name der Vorlage:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self._name_var = tk.StringVar()
        ttk.Entry(g1, textvariable=self._name_var, width=60).grid(row=0, column=1, columnspan=5, sticky=tk.W, padx=5, pady=5)

        ttk.Label(g1, text="Hersteller:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self._vars["manufacturer"] = tk.StringVar()
        ttk.Entry(g1, textvariable=self._vars["manufacturer"], width=25).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(g1, text="Produkt:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self._vars["product_name"] = tk.StringVar()
        ttk.Entry(g1, textvariable=self._vars["product_name"], width=25).grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

        # --- Abmessungen ---
        g2 = ttk.LabelFrame(f, text=" Abmessungen (Etikett) ", padding=15)
        g2.grid(row=1, column=0, columnspan=6, sticky=tk.EW, pady=10, padx=5)
        row(g2, "Breite:", "width_mm", 0, col=0)
        row(g2, "Höhe:",  "height_mm", 0, col=1)

        # --- Ränder ---
        g3 = ttk.LabelFrame(f, text=" Ränder / Abstände (mm) ", padding=15)
        g3.grid(row=2, column=0, columnspan=6, sticky=tk.EW, pady=10, padx=5)
        row(g3, "Oben:",  "margin_top_mm",    0, col=0)
        row(g3, "Unten:", "margin_bottom_mm", 0, col=1)
        row(g3, "Links:", "margin_left_mm",   1, col=0)
        row(g3, "Rechts:","margin_right_mm",  1, col=1)

        # --- Layout (Bogen) ---
        g4 = ttk.LabelFrame(f, text=" Mehrfachetiketten (Bogenlayout) ", padding=15)
        g4.grid(row=3, column=0, columnspan=6, sticky=tk.EW, pady=10, padx=5)
        
        ttk.Label(g4, text="Spalten:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=8)
        self._vars["cols"] = tk.IntVar(value=1)
        ttk.Spinbox(g4, from_=1, to=50, textvariable=self._vars["cols"], width=12).grid(row=0, column=1, sticky=tk.W, padx=5, pady=8)

        ttk.Label(g4, text="Reihen:").grid(row=0, column=3, sticky=tk.W, padx=10, pady=8)
        self._vars["rows"] = tk.IntVar(value=1)
        ttk.Spinbox(g4, from_=1, to=100, textvariable=self._vars["rows"], width=12).grid(row=0, column=4, sticky=tk.W, padx=5, pady=8)

        row(g4, "Spaltenabstand:", "col_gap_mm", 1, col=0)
        row(g4, "Reihenabstand: ", "row_gap_mm", 1, col=1)

    def _on_form_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        # Breite des Form-Frames an Canvas anpassen
        self._canvas.itemconfig(self._canvas_win, width=event.width)

    def _refresh_list(self):
        # Merke Selektion
        sel_name = self._current_template_name
        
        self._tree.delete(*self._tree.get_children())
        try:
            self._templates = repo.list_global_templates()
        except Exception as e:
            messagebox.showerror("Datenbankfehler", f"Fehler beim Laden: {e}")
            return

        for name, data in self._templates:
            w = data.get("width_mm", 0)
            h = data.get("height_mm", 0)
            man = data.get("manufacturer", "Unbekannt")
            self._tree.insert("", tk.END, iid=name, values=(f"{name}  [{man} - {w}x{h}mm]",))
            
        if sel_name and self._tree.exists(sel_name):
            self._tree.selection_set(sel_name)
            self._tree.see(sel_name)

    def _on_select(self, event):
        sel = self._tree.selection()
        if not sel: 
            return
        name = sel[0]
        self._current_template_name = name
        
        # Daten finden
        data = next((d for n, d in self._templates if n == name), None)
        if not data: 
            return
        
        self._name_var.set(name)
        for attr, var in self._vars.items():
            val = data.get(attr)
            if val is not None:
                var.set(val)

    def _get_fmt_from_vars(self) -> LabelFormat:
        return LabelFormat(
            id=0, project_id=0,
            manufacturer=self._vars["manufacturer"].get(),
            product_name=self._vars["product_name"].get(),
            width_mm=self._vars["width_mm"].get(),
            height_mm=self._vars["height_mm"].get(),
            margin_top_mm=self._vars["margin_top_mm"].get(),
            margin_bottom_mm=self._vars["margin_bottom_mm"].get(),
            margin_left_mm=self._vars["margin_left_mm"].get(),
            margin_right_mm=self._vars["margin_right_mm"].get(),
            cols=self._vars["cols"].get(),
            rows=self._vars["rows"].get(),
            col_gap_mm=self._vars["col_gap_mm"].get(),
            row_gap_mm=self._vars["row_gap_mm"].get()
        )

    def _delete_template(self):
        if not self._current_template_name:
            messagebox.showwarning("Hinweis", "Bitte zuerst eine Vorlage auswählen.")
            return
        if messagebox.askyesno("Vorlage löschen", 
                               f"Soll die Vorlage '{self._current_template_name}' wirklich unwiederbringlich gelöscht werden?"):
            try:
                repo.delete_global_template(self._current_template_name)
                self._current_template_name = None
                self._refresh_list()
                # Felder leeren
                self._name_var.set("")
            except Exception as e:
                messagebox.showerror("Fehler", str(e))

    def _save_changes(self):
        if not self._current_template_name:
            messagebox.showwarning("Speichern", "Bitte zuerst eine Vorlage aus der Liste wählen oder 'Als NEUE Vorlage' nutzen.")
            return
        
        new_name = self._name_var.get().strip()
        if not new_name:
            messagebox.showwarning("Fehler", "Der Name darf nicht leer sein.")
            return
            
        fmt = self._get_fmt_from_vars()
        
        try:
            # Wenn Name geändert wurde, altes löschen (Rename-Simulation)
            if new_name != self._current_template_name:
                repo.delete_global_template(self._current_template_name)
            
            repo.add_global_template(new_name, fmt)
            self._current_template_name = new_name
            self._refresh_list()
            messagebox.showinfo("Speichern", f"Vorlage '{new_name}' wurde aktualisiert.")
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", str(e))

    def _save_as_new(self):
        name = self._name_var.get().strip()
        
        # Falls der Name identisch zum aktuellen ist, fragen wir nach einem neuen.
        if not name or name == self._current_template_name:
            name = simpledialog.askstring("Neue Vorlage", "Bitte einen neuen Namen für die Vorlage eingeben:")
            if not name: 
                return
        
        # Prüfen ob Name existiert
        if any(n for n, _ in self._templates if n == name):
            if not messagebox.askyesno("Existiert bereits", f"Eine Vorlage mit dem Namen '{name}' existiert bereits. Überschreiben?"):
                return

        fmt = self._get_fmt_from_vars()
        try:
            repo.add_global_template(name, fmt)
            self._current_template_name = name
            self._refresh_list()
            messagebox.showinfo("Erfolg", f"Neue Vorlage '{name}' wurde angelegt.")
        except Exception as e:
            messagebox.showerror("Fehler beim Anlegen", str(e))

    def _clear_fields(self):
        """Leert alle Eingabefelder für eine neue Vorlage."""
        self._current_template_name = None
        self._tree.selection_remove(self._tree.selection())
        self._name_var.set("")
        for attr, var in self._vars.items():
            if isinstance(var, (tk.DoubleVar, tk.IntVar)):
                var.set(0)
                if attr in ("cols", "rows"):
                    var.set(1)
            else:
                var.set("")
