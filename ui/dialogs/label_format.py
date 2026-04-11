"""Dialog zur Konfiguration des Etikettenformats (Abmessungen, Ränder, Reihen/Spalten)."""
from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import db.repository as repo
from models.types import LabelFormat


def _load_templates() -> list[tuple[str, dict[str, float | int | str]]]:
    return repo.list_global_templates()

class LabelFormatDialog:
    def __init__(self, parent: tk.Widget, fmt: LabelFormat, admin_mode: bool = False):
        self._fmt = fmt
        self.admin_mode = admin_mode
        self.changed = False
        self._templates = _load_templates()

        self._win = tk.Toplevel(parent)
        self._win.title("Etikettenformat")
        self._win.grab_set()
        self._win.resizable(False, False)
        self._build_ui()
        self._win.wait_window()

    def _build_ui(self) -> None:
        f = ttk.Frame(self._win, padding=14)
        f.pack(fill=tk.BOTH)

        def row(lbl: str, attr: str, r: int, col: int = 0,
                from_: float = 0.1, to: float = 500.0, inc: float = 0.5) -> None:
            ttk.Label(f, text=lbl).grid(row=r, column=col * 3,
                                        sticky=tk.W, padx=4, pady=4)
            var = tk.DoubleVar(value=getattr(self._fmt, attr))
            sb  = ttk.Spinbox(f, from_=from_, to=to, increment=inc,
                              textvariable=var, width=8, format="%.2f",
                              state="readonly" if not self.admin_mode else "normal")
            sb.grid(row=r, column=col * 3 + 1, sticky=tk.W, padx=4)
            ttk.Label(f, text="mm").grid(row=r, column=col * 3 + 2, sticky=tk.W)
            self._vars[attr] = var

        self._vars: dict[str, tk.Variable] = {}

        ttk.Label(f, text="Vorlage", font=("", 9, "bold")).grid(
            row=0, column=0, columnspan=6, sticky=tk.W, pady=(0, 4)
        )

        ttk.Label(f, text="Template:").grid(row=1, column=0, sticky=tk.W, padx=4, pady=4)
        self._template_var = tk.StringVar(value="Benutzerdefiniert")
        self._template_combo = ttk.Combobox(
            f,
            textvariable=self._template_var,
            values=["Benutzerdefiniert"] + [name for name, _ in self._templates],
            state="readonly",
            width=34,
        )
        self._template_combo.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=4)
        ttk.Button(f, text="Uebernehmen", command=self._apply_template).grid(
            row=1, column=4, columnspan=2, sticky=tk.W, padx=4
        )

        ttk.Label(f, text="Hersteller:").grid(row=2, column=0, sticky=tk.W, padx=4, pady=4)
        self._vars["manufacturer"] = tk.StringVar(value=self._fmt.manufacturer)
        ttk.Entry(f, textvariable=self._vars["manufacturer"], width=22,
                  state="disabled" if not self.admin_mode else "normal").grid(
            row=2, column=1, columnspan=2, sticky=tk.W, padx=4
        )

        ttk.Label(f, text="Produkt:").grid(row=2, column=3, sticky=tk.W, padx=4, pady=4)
        self._vars["product_name"] = tk.StringVar(value=self._fmt.product_name)
        ttk.Entry(f, textvariable=self._vars["product_name"], width=20,
                  state="disabled" if not self.admin_mode else "normal").grid(
            row=2, column=4, columnspan=2, sticky=tk.W, padx=4
        )

        ttk.Label(f, text="Abmessungen", font=("", 9, "bold")).grid(
            row=3, column=0, columnspan=3, sticky=tk.W, pady=(8, 4))
        row("Breite:",            "width_mm",           4)
        row("Höhe:",              "height_mm",           5)

        ttk.Separator(f, orient=tk.HORIZONTAL).grid(
            row=6, column=0, columnspan=6, sticky=tk.EW, pady=8)
        ttk.Label(f, text="Ränder", font=("", 9, "bold")).grid(
            row=7, column=0, columnspan=3, sticky=tk.W, pady=(0, 4))
        row("Oben:",              "margin_top_mm",       8)
        row("Unten:",             "margin_bottom_mm",    9)
        row("Links:",             "margin_left_mm",      10)
        row("Rechts:",            "margin_right_mm",     11)

        ttk.Separator(f, orient=tk.HORIZONTAL).grid(
            row=12, column=0, columnspan=6, sticky=tk.EW, pady=8)
        ttk.Label(f, text="Mehrfachetiketten", font=("", 9, "bold")).grid(
            row=13, column=0, columnspan=3, sticky=tk.W, pady=(0, 4))

        ttk.Label(f, text="Spalten:").grid(row=14, column=0, sticky=tk.W, padx=4, pady=4)
        var_cols = tk.IntVar(value=self._fmt.cols)
        ttk.Spinbox(f, from_=1, to=20, textvariable=var_cols, width=8,
                    state="readonly" if not self.admin_mode else "normal").grid(
            row=14, column=1, sticky=tk.W, padx=4)
        self._vars["cols"] = var_cols

        ttk.Label(f, text="Reihen:").grid(row=15, column=0, sticky=tk.W, padx=4, pady=4)
        var_rows = tk.IntVar(value=self._fmt.rows)
        ttk.Spinbox(f, from_=1, to=50, textvariable=var_rows, width=8,
                    state="readonly" if not self.admin_mode else "normal").grid(
            row=15, column=1, sticky=tk.W, padx=4)
        self._vars["rows"] = var_rows

        row("Spaltenabstand:", "col_gap_mm", 16)
        row("Reihenabstand:",  "row_gap_mm", 17)

        ttk.Separator(f, orient=tk.HORIZONTAL).grid(
            row=18, column=0, columnspan=6, sticky=tk.EW, pady=8)

        btn = ttk.Frame(f)
        btn.grid(row=19, column=0, columnspan=6, sticky=tk.E, pady=4)
        if self.admin_mode:
            ttk.Button(btn, text="Als Vorlage speichern …", 
                       command=self._save_as_template).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn, text="OK",         command=self._ok).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn, text="Abbrechen",  command=self._win.destroy).pack(side=tk.RIGHT)

    def _apply_template(self) -> None:
        selected = self._template_var.get()
        template_map = {name: values for name, values in self._templates}
        values = template_map.get(selected)
        if not values:
            return
        for attr, value in values.items():
            var = self._vars.get(attr)
            if var is not None:
                var.set(value)

    def _ok(self) -> None:
        for attr, var in self._vars.items():
            setattr(self._fmt, attr, var.get())
        self.changed = True
        self._win.destroy()

    def _save_as_template(self) -> None:
        name = simpledialog.askstring("Vorlage speichern", "Name der neuen Vorlage:", parent=self._win)
        if not name:
            return
        
        # Aktuelle Werte aus den Variablen in ein temporäres Objekt/Fmt übernehmen
        from copy import copy
        temp_fmt = copy(self._fmt)
        for attr, var in self._vars.items():
            setattr(temp_fmt, attr, var.get())
        
        try:
            repo.add_global_template(name, temp_fmt)
            messagebox.showinfo("Erfolg", f"Vorlage '{name}' erfolgreich gespeichert.", parent=self._win)
            # Liste aktualisieren
            self._templates = _load_templates()
            self._template_combo["values"] = ["Benutzerdefiniert"] + [n for n, _ in self._templates]
            self._template_var.set(name)
        except Exception as e:
            messagebox.showerror("Fehler", f"Vorlage konnte nicht gespeichert werden:\n{e}", parent=self._win)
