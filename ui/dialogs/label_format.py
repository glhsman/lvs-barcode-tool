"""Dialog zur Konfiguration des Etikettenformats (Abmessungen, Ränder, Reihen/Spalten)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from models.types import LabelFormat


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

        ttk.Label(f, text="Abmessungen", font=("", 9, "bold")).grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 4))
        row("Breite:",            "width_mm",           1)
        row("Höhe:",              "height_mm",           2)

        ttk.Separator(f, orient=tk.HORIZONTAL).grid(
            row=3, column=0, columnspan=6, sticky=tk.EW, pady=8)
        ttk.Label(f, text="Ränder", font=("", 9, "bold")).grid(
            row=4, column=0, columnspan=3, sticky=tk.W, pady=(0, 4))
        row("Oben:",              "margin_top_mm",       5)
        row("Unten:",             "margin_bottom_mm",    6)
        row("Links:",             "margin_left_mm",      7)
        row("Rechts:",            "margin_right_mm",     8)

        ttk.Separator(f, orient=tk.HORIZONTAL).grid(
            row=9, column=0, columnspan=6, sticky=tk.EW, pady=8)
        ttk.Label(f, text="Mehrfachetiketten", font=("", 9, "bold")).grid(
            row=10, column=0, columnspan=3, sticky=tk.W, pady=(0, 4))

        ttk.Label(f, text="Spalten:").grid(row=11, column=0, sticky=tk.W, padx=4, pady=4)
        var_cols = tk.IntVar(value=self._fmt.cols)
        ttk.Spinbox(f, from_=1, to=20, textvariable=var_cols, width=8).grid(
            row=11, column=1, sticky=tk.W, padx=4)
        self._vars["cols"] = var_cols

        ttk.Label(f, text="Reihen:").grid(row=12, column=0, sticky=tk.W, padx=4, pady=4)
        var_rows = tk.IntVar(value=self._fmt.rows)
        ttk.Spinbox(f, from_=1, to=50, textvariable=var_rows, width=8).grid(
            row=12, column=1, sticky=tk.W, padx=4)
        self._vars["rows"] = var_rows

        row("Spaltenabstand:", "col_gap_mm", 13)
        row("Reihenabstand:",  "row_gap_mm", 14)

        ttk.Separator(f, orient=tk.HORIZONTAL).grid(
            row=15, column=0, columnspan=6, sticky=tk.EW, pady=8)

        btn = ttk.Frame(f)
        btn.grid(row=16, column=0, columnspan=6, sticky=tk.E, pady=4)
        ttk.Button(btn, text="OK",         command=self._ok).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn, text="Abbrechen",  command=self._win.destroy).pack(side=tk.RIGHT)

    def _ok(self) -> None:
        for attr, var in self._vars.items():
            setattr(self._fmt, attr, var.get())
        self.changed = True
        self._win.destroy()
