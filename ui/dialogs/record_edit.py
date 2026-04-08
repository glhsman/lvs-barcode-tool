"""Dialog zum Anlegen / Bearbeiten eines Datensatzes."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from models.types import DataRecord, ProjectField


class RecordEditDialog:
    """
    Modaler Dialog.  Nach Schließen enthält self.result die geänderten Werte
    als dict {field_name: value} oder None wenn abgebrochen.
    """

    def __init__(
        self,
        parent: tk.Widget,
        fields: list[ProjectField],
        record: DataRecord,
    ):
        self.result: Optional[dict[str, str]] = None
        self._fields = fields
        self._record = record
        self._entries: dict[str, tk.StringVar] = {}

        self._win = tk.Toplevel(parent)
        self._win.title("Datensatz bearbeiten" if record.id else "Datensatz anlegen")
        self._win.grab_set()
        self._win.resizable(True, True)
        self._win.geometry("500x420")

        self._build_ui()
        self._win.wait_window()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self._win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Feldname", font=("", 9, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=4, pady=2)
        ttk.Label(frame, text="Wert",     font=("", 9, "bold")).grid(
            row=0, column=1, sticky=tk.W, padx=4, pady=2)
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=1, column=0, columnspan=2, sticky=tk.EW, pady=4)

        canvas = tk.Canvas(frame, borderwidth=0)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        self._scroll_frame = ttk.Frame(canvas)

        self._scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=self._scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW)
        scrollbar.grid(row=2, column=2, sticky=tk.NS)
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(1, weight=1)

        for i, field in enumerate(self._fields):
            ttk.Label(self._scroll_frame, text=field.name + ":").grid(
                row=i, column=0, sticky=tk.W, padx=6, pady=3)
            var = tk.StringVar(
                value=self._record.values.get(field.name, "")
            )
            self._entries[field.name] = var
            ttk.Entry(self._scroll_frame, textvariable=var, width=40).grid(
                row=i, column=1, sticky=tk.EW, padx=6, pady=3)
        self._scroll_frame.columnconfigure(1, weight=1)

        # Buttons
        btn_frame = ttk.Frame(self._win, padding=(10, 4))
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btn_frame, text="OK",     command=self._ok).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_frame, text="Abbrechen", command=self._win.destroy).pack(side=tk.RIGHT, padx=4)

        self._win.bind("<Return>", lambda e: self._ok())
        self._win.bind("<Escape>", lambda e: self._win.destroy())

    def _ok(self) -> None:
        self.result = {name: var.get() for name, var in self._entries.items()}
        self._win.destroy()
