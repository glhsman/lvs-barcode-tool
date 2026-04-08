"""Dialog: Zahlenreihe generieren und in die Datentabelle einfügen."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

import db.repository as repo
from models.types import Project, ProjectField
from utils.number_series import generate_series


class NumberSeriesDialog:
    def __init__(self, parent: tk.Widget, fields: list[ProjectField],
                 project_id: int):
        self._fields    = fields
        self._project_id = project_id
        self.generated  = False

        self._win = tk.Toplevel(parent)
        self._win.title("Zahlenreihe generieren")
        self._win.grab_set()
        self._win.resizable(False, False)
        self._build_ui()
        self._win.wait_window()

    def _build_ui(self) -> None:
        f = ttk.Frame(self._win, padding=14)
        f.pack(fill=tk.BOTH)

        def lbl_row(text: str, r: int) -> tk.StringVar:
            ttk.Label(f, text=text).grid(row=r, column=0, sticky=tk.W, pady=4, padx=4)
            var = tk.StringVar()
            ttk.Entry(f, textvariable=var, width=20).grid(
                row=r, column=1, sticky=tk.W, padx=4)
            return var

        ttk.Label(f, text="Zielfeld:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self._field_var = tk.StringVar()
        ttk.Combobox(f, textvariable=self._field_var,
                     values=[field.name for field in self._fields],
                     state="readonly", width=22).grid(row=0, column=1, sticky=tk.W, padx=4)
        if self._fields:
            self._field_var.set(self._fields[0].name)

        self._start_var  = lbl_row("Startwert:",            1)
        self._end_var    = lbl_row("Endwert:",              2)
        self._step_var   = lbl_row("Schrittgröße:",         3)
        self._repeat_var = lbl_row("Wiederholungen:",       4)
        self._start_var.set("1")
        self._end_var.set("100")
        self._step_var.set("1")
        self._repeat_var.set("1")

        self._padzero_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Führende Nullen",
                        variable=self._padzero_var).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=4)

        ttk.Separator(f, orient=tk.HORIZONTAL).grid(
            row=6, column=0, columnspan=2, sticky=tk.EW, pady=6)

        btn_f = ttk.Frame(f)
        btn_f.grid(row=7, column=0, columnspan=2, sticky=tk.E)
        ttk.Button(btn_f, text="Generieren",  command=self._generate).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_f, text="Abbrechen", command=self._win.destroy).pack(side=tk.RIGHT)

    def _generate(self) -> None:
        field_name = self._field_var.get()
        if not field_name:
            messagebox.showwarning("Feld", "Bitte ein Zielfeld wählen.")
            return
        try:
            start  = self._start_var.get()
            end    = self._end_var.get()
            step   = int(self._step_var.get())
            repeat = int(self._repeat_var.get())
        except ValueError as exc:
            messagebox.showerror("Fehler", str(exc))
            return

        values_list = generate_series(start, end, step, repeat,
                                       self._padzero_var.get())
        if not values_list:
            messagebox.showwarning("Leer", "Es wurden keine Werte generiert.")
            return

        for v in values_list:
            repo.add_record(self._project_id, {field_name: v})

        self.generated = True
        messagebox.showinfo("Fertig", f"{len(values_list)} Datensätze angelegt.")
        self._win.destroy()
