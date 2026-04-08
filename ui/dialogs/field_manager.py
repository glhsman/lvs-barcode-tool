"""Dialog zur Verwaltung von Tabellenfeldern (Anlegen, Umbenennen, Löschen, Sortieren)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import db.repository as repo
from models.types import Project, ProjectField


class FieldManagerDialog:
    def __init__(self, parent: tk.Widget, project: Project):
        self._project = project
        self._fields: list[ProjectField] = repo.list_fields(project.id)

        self._win = tk.Toplevel(parent)
        self._win.title("Felder bearbeiten")
        self._win.grab_set()
        self._win.geometry("500x550")
        self._win.minsize(400, 400)

        self._build_ui()
        self._populate()
        self._win.wait_window()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self._win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        self._listbox = tk.Listbox(frame, selectmode=tk.SINGLE, activestyle="dotbox")
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self._listbox.yview)
        vsb.pack(side=tk.LEFT, fill=tk.Y)
        self._listbox.config(yscrollcommand=vsb.set)

        btn = ttk.Frame(self._win, padding=(10, 4))
        btn.pack(fill=tk.X)
        ttk.Button(btn, text="Neues Feld",   command=self._new).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn, text="Umbenennen",   command=self._rename).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn, text="Löschen",      command=self._delete).pack(side=tk.LEFT, padx=2)
        ttk.Separator(btn, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)
        ttk.Button(btn, text="↑",            command=lambda: self._move(-1)).pack(side=tk.LEFT)
        ttk.Button(btn, text="↓",            command=lambda: self._move(1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn, text="Schließen",    command=self._win.destroy).pack(side=tk.RIGHT, padx=4)

    def _populate(self) -> None:
        self._listbox.delete(0, tk.END)
        for f in self._fields:
            self._listbox.insert(tk.END, f.name)

    def _selected_idx(self) -> int | None:
        sel = self._listbox.curselection()
        return sel[0] if sel else None

    def _new(self) -> None:
        name = simpledialog.askstring("Neues Feld", "Feldname:", parent=self._win)
        if not name:
            return
        if any(f.name == name for f in self._fields):
            messagebox.showwarning("Doppelt", f"Feld '{name}' existiert bereits.")
            return
        field = repo.add_field(self._project.id, name)
        self._fields.append(field)
        self._populate()
        self._listbox.selection_set(tk.END)

    def _rename(self) -> None:
        idx = self._selected_idx()
        if idx is None:
            return
        old = self._fields[idx].name
        new = simpledialog.askstring("Umbenennen", "Neuer Name:", initialvalue=old,
                                      parent=self._win)
        if not new or new == old:
            return
        repo.rename_field(self._fields[idx].id, new)
        self._fields[idx].name = new
        self._populate()
        self._listbox.selection_set(idx)

    def _delete(self) -> None:
        idx = self._selected_idx()
        if idx is None:
            return
        name = self._fields[idx].name
        if not messagebox.askyesno("Löschen",
                                   f"Feld '{name}' und alle dazugehörigen Werte löschen?",
                                   parent=self._win):
            return
        repo.delete_field(self._fields[idx].id)
        del self._fields[idx]
        self._populate()

    def _move(self, delta: int) -> None:
        idx = self._selected_idx()
        if idx is None:
            return
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(self._fields):
            return
        self._fields[idx], self._fields[new_idx] = (
            self._fields[new_idx], self._fields[idx]
        )
        repo.reorder_fields(self._project.id, [f.id for f in self._fields])
        self._populate()
        self._listbox.selection_set(new_idx)
