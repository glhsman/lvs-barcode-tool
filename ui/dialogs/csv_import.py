"""CSV-Import-Dialog für den Bereich „Daten"."""
from __future__ import annotations

import csv
import io
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

import db.repository as repo
from models.types import Project, ProjectField


class CsvImportDialog:
    def __init__(self, parent: tk.Widget, project: Project,
                 fields: list[ProjectField]):
        self._project  = project
        self._fields   = fields
        self.imported_count = 0

        self._win = tk.Toplevel(parent)
        self._win.title("Daten importieren – CSV")
        self._win.grab_set()
        # Vergrößert für besseres Layout im Dark Mode
        self._win.geometry("720x700")
        self._win.minsize(600, 500)

        self._headers: list[str] = []
        self._rows: list[list[str]] = []
        self._mapping: dict[str, tk.StringVar] = {}

        self._build_ui()
        self._win.wait_window()

    def _build_ui(self) -> None:
        top = ttk.Frame(self._win, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="CSV-Datei:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self._file_var = tk.StringVar()
        ttk.Entry(top, textvariable=self._file_var, width=48).grid(
            row=0, column=1, sticky=tk.EW, padx=4)
        ttk.Button(top, text="…", command=self._browse).grid(row=0, column=2)

        ttk.Label(top, text="Trennzeichen:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self._sep_var = tk.StringVar(value=",")
        sep_combo = ttk.Combobox(top, textvariable=self._sep_var,
                                  values=[",", ";", "Tab", "|"], width=8, state="readonly")
        sep_combo.grid(row=1, column=1, sticky=tk.W, padx=4)

        ttk.Label(top, text="Zeichensatz:").grid(row=2, column=0, sticky=tk.W)
        self._enc_var = tk.StringVar(value="utf-8")
        ttk.Combobox(top, textvariable=self._enc_var,
                     values=["utf-8", "utf-8-sig", "utf-16", "latin-1", "cp1252"],
                     width=12).grid(row=2, column=1, sticky=tk.W, padx=4)

        self._header_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="Erste Zeile enthält Spaltennamen",
                        variable=self._header_var).grid(
            row=3, column=0, columnspan=3, sticky=tk.W, pady=4)

        ttk.Button(top, text="Datei laden", command=self._load).grid(
            row=4, column=1, sticky=tk.W, padx=4, pady=4)
        top.columnconfigure(1, weight=1)

        ttk.Separator(self._win, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)

        # Zuordnung
        self._map_frame = ttk.LabelFrame(self._win, text=" Spaltenzuordnung ", padding=8)
        self._map_frame.pack(fill=tk.X, padx=10)

        # Vorschau
        preview_lf = ttk.LabelFrame(self._win, text=" Vorschau (erste 5 Zeilen) ", padding=4)
        preview_lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        self._preview_tree = ttk.Treeview(preview_lf, show="headings")
        vsb = ttk.Scrollbar(preview_lf, orient=tk.VERTICAL,
                            command=self._preview_tree.yview)
        self._preview_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._preview_tree.pack(fill=tk.BOTH, expand=True)

        # Buttons
        btn_f = ttk.Frame(self._win, padding=(10, 4))
        btn_f.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btn_f, text="Importieren",
                   command=self._import).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_f, text="Abbrechen",
                   command=self._win.destroy).pack(side=tk.RIGHT)

    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title="CSV-Datei öffnen",
            filetypes=[("CSV", "*.csv *.txt"), ("Alle", "*.*")],
        )
        if path:
            self._file_var.set(path)

    def _load(self) -> None:
        path = self._file_var.get()
        if not path:
            messagebox.showwarning("Datei", "Keine Datei gewählt.")
            return
        sep = "\t" if self._sep_var.get() == "Tab" else self._sep_var.get()
        enc = self._enc_var.get()
        try:
            with open(path, newline="", encoding=enc) as f:
                reader = csv.reader(f, delimiter=sep)
                all_rows = list(reader)
        except Exception as exc:
            messagebox.showerror("Fehler", str(exc))
            return

        if not all_rows:
            messagebox.showinfo("Leer", "Datei enthält keine Daten.")
            return

        if self._header_var.get():
            self._headers = all_rows[0]
            self._rows    = all_rows[1:]
        else:
            self._headers = [f"Spalte {i+1}" for i in range(len(all_rows[0]))]
            self._rows    = all_rows

        self._build_mapping()
        self._show_preview()

    def _build_mapping(self) -> None:
        for w in self._map_frame.winfo_children():
            w.destroy()
        self._mapping = {}
        field_names = ["(ignorieren)"] + [f.name for f in self._fields]
        ttk.Label(self._map_frame, text="CSV-Spalte", font=("", 9, "bold")).grid(
            row=0, column=0, padx=6)
        ttk.Label(self._map_frame, text="→ Feld in Projekt", font=("", 9, "bold")).grid(
            row=0, column=1, padx=6)
        for i, hdr in enumerate(self._headers):
            ttk.Label(self._map_frame, text=hdr).grid(
                row=i+1, column=0, sticky=tk.W, padx=6, pady=2)
            var = tk.StringVar()
            match = next((f.name for f in self._fields if f.name.lower() == hdr.lower()), "(ignorieren)")
            var.set(match)
            self._mapping[hdr] = var
            ttk.Combobox(self._map_frame, textvariable=var, values=field_names,
                         state="readonly", width=20).grid(
                row=i+1, column=1, sticky=tk.W, padx=6, pady=2)

    def _show_preview(self) -> None:
        self._preview_tree.delete(*self._preview_tree.get_children())
        self._preview_tree.config(columns=self._headers)
        for h in self._headers:
            self._preview_tree.heading(h, text=h)
            self._preview_tree.column(h, width=100)
        for row in self._rows[:5]:
            self._preview_tree.insert("", tk.END, values=row)

    def _import(self) -> None:
        if not self._rows:
            messagebox.showwarning("Keine Daten", "Bitte zuerst Datei laden.")
            return
        for row in self._rows:
            values: dict[str, str] = {}
            for i, hdr in enumerate(self._headers):
                target = self._mapping.get(hdr, tk.StringVar()).get()
                if target and target != "(ignorieren)":
                    values[target] = row[i] if i < len(row) else ""
            if any(values.values()):
                repo.add_record(self._project.id, values)
                self.imported_count += 1
        messagebox.showinfo("Import abgeschlossen",
                            f"{self.imported_count} Datensätze importiert.")
        self._win.destroy()
