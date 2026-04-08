"""Einfacher Suchdialog für den Daten-Tab."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from models.types import DataRecord, ProjectField


class SearchDialog:
    def __init__(self, parent: tk.Widget, tree: ttk.Treeview,
                 fields: list[ProjectField], records: list[DataRecord]):
        self._tree    = tree
        self._fields  = fields
        self._records = records

        self._win = tk.Toplevel(parent)
        self._win.title("Suchen")
        self._win.geometry("380x160")
        self._win.resizable(False, False)
        self._build_ui()

    def _build_ui(self) -> None:
        f = ttk.Frame(self._win, padding=10)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="Suchen in:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self._field_var = tk.StringVar(value="(alle Felder)")
        ttk.Combobox(f, textvariable=self._field_var,
                     values=["(alle Felder)"] + [f2.name for f2 in self._fields],
                     width=22).grid(row=0, column=1, sticky=tk.W, padx=4)

        ttk.Label(f, text="Suchbegriff:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self._term_var = tk.StringVar()
        ttk.Entry(f, textvariable=self._term_var, width=26).grid(
            row=1, column=1, sticky=tk.EW, padx=4)

        self._status_var = tk.StringVar()
        ttk.Label(f, textvariable=self._status_var, foreground="blue").grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=4)

        btn_f = ttk.Frame(f)
        btn_f.grid(row=3, column=0, columnspan=2, sticky=tk.E)
        ttk.Button(btn_f, text="Suchen",    command=self._search).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_f, text="Schließen", command=self._win.destroy).pack(side=tk.RIGHT)

        self._win.bind("<Return>", lambda e: self._search())
        f.columnconfigure(1, weight=1)

    def _search(self) -> None:
        term = self._term_var.get().lower()
        if not term:
            return
        field_name = self._field_var.get()

        hits = []
        for rec in self._records:
            if field_name == "(alle Felder)":
                if any(term in v.lower() for v in rec.values.values()):
                    hits.append(str(rec.id))
            else:
                if term in rec.values.get(field_name, "").lower():
                    hits.append(str(rec.id))

        self._tree.selection_set(hits)
        if hits:
            self._tree.see(hits[0])
        self._status_var.set(f"{len(hits)} Treffer")
