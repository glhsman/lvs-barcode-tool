"""Dialog zur Konfiguration des Etikettenformats (Abmessungen, Ränder, Reihen/Spalten)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from models.types import LabelFormat


LABEL_TEMPLATES: list[tuple[str, dict[str, float | int | str]]] = [
    (
        "Versandetikett 100 x 50 mm",
        {
            "manufacturer": "Generic",
            "product_name": "Versandetikett 100x50",
            "width_mm": 100.0,
            "height_mm": 50.0,
            "margin_top_mm": 2.0,
            "margin_bottom_mm": 2.0,
            "margin_left_mm": 2.0,
            "margin_right_mm": 2.0,
            "cols": 1,
            "rows": 1,
            "col_gap_mm": 0.0,
            "row_gap_mm": 0.0,
        },
    ),
    (
        "A4 Zweckform 3659 (48.5 x 25.4 mm)",
        {
            "manufacturer": "Zweckform",
            "product_name": "3659",
            "width_mm": 48.5,
            "height_mm": 25.4,
            "margin_top_mm": 10.0,
            "margin_bottom_mm": 10.0,
            "margin_left_mm": 7.5,
            "margin_right_mm": 7.5,
            "cols": 4,
            "rows": 11,
            "col_gap_mm": 0.0,
            "row_gap_mm": 0.0,
        },
    ),
    (
        "A4 Zweckform 3474 (105 x 70 mm)",
        {
            "manufacturer": "Zweckform",
            "product_name": "3474",
            "width_mm": 105.0,
            "height_mm": 70.0,
            "margin_top_mm": 8.5,
            "margin_bottom_mm": 8.5,
            "margin_left_mm": 0.0,
            "margin_right_mm": 0.0,
            "cols": 2,
            "rows": 4,
            "col_gap_mm": 0.0,
            "row_gap_mm": 0.0,
        },
    ),
    (
        "A6 Etikett 105 x 148 mm",
        {
            "manufacturer": "Generic",
            "product_name": "A6",
            "width_mm": 105.0,
            "height_mm": 148.0,
            "margin_top_mm": 2.0,
            "margin_bottom_mm": 2.0,
            "margin_left_mm": 2.0,
            "margin_right_mm": 2.0,
            "cols": 1,
            "rows": 1,
            "col_gap_mm": 0.0,
            "row_gap_mm": 0.0,
        },
    ),

    (
        "Vorlage LVS-Etikett 105 x 148 mm",
        {
            "manufacturer": "Generic",
            "product_name": "LVS",
            "width_mm": 105.0,
            "height_mm": 148.0,
            "margin_top_mm": 2.0,
            "margin_bottom_mm": 2.0,
            "margin_left_mm": 2.0,
            "margin_right_mm": 2.0,
            "cols": 1,
            "rows": 1,
            "col_gap_mm": 0.0,
            "row_gap_mm": 0.0,
        },
    ),
]

class LabelFormatDialog:
    def __init__(self, parent: tk.Widget, fmt: LabelFormat):
        self._fmt = fmt
        self.changed = False

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
                              textvariable=var, width=8, format="%.2f")
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
            values=["Benutzerdefiniert"] + [name for name, _ in LABEL_TEMPLATES],
            state="readonly",
            width=34,
        )
        self._template_combo.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=4)
        ttk.Button(f, text="Uebernehmen", command=self._apply_template).grid(
            row=1, column=4, columnspan=2, sticky=tk.W, padx=4
        )

        ttk.Label(f, text="Hersteller:").grid(row=2, column=0, sticky=tk.W, padx=4, pady=4)
        self._vars["manufacturer"] = tk.StringVar(value=self._fmt.manufacturer)
        ttk.Entry(f, textvariable=self._vars["manufacturer"], width=22).grid(
            row=2, column=1, columnspan=2, sticky=tk.W, padx=4
        )

        ttk.Label(f, text="Produkt:").grid(row=2, column=3, sticky=tk.W, padx=4, pady=4)
        self._vars["product_name"] = tk.StringVar(value=self._fmt.product_name)
        ttk.Entry(f, textvariable=self._vars["product_name"], width=20).grid(
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
        ttk.Spinbox(f, from_=1, to=20, textvariable=var_cols, width=8).grid(
            row=14, column=1, sticky=tk.W, padx=4)
        self._vars["cols"] = var_cols

        ttk.Label(f, text="Reihen:").grid(row=15, column=0, sticky=tk.W, padx=4, pady=4)
        var_rows = tk.IntVar(value=self._fmt.rows)
        ttk.Spinbox(f, from_=1, to=50, textvariable=var_rows, width=8).grid(
            row=15, column=1, sticky=tk.W, padx=4)
        self._vars["rows"] = var_rows

        row("Spaltenabstand:", "col_gap_mm", 16)
        row("Reihenabstand:",  "row_gap_mm", 17)

        ttk.Separator(f, orient=tk.HORIZONTAL).grid(
            row=18, column=0, columnspan=6, sticky=tk.EW, pady=8)

        btn = ttk.Frame(f)
        btn.grid(row=19, column=0, columnspan=6, sticky=tk.E, pady=4)
        ttk.Button(btn, text="OK",         command=self._ok).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn, text="Abbrechen",  command=self._win.destroy).pack(side=tk.RIGHT)

    def _apply_template(self) -> None:
        selected = self._template_var.get()
        template_map = {name: values for name, values in LABEL_TEMPLATES}
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
