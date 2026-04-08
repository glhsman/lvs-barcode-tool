"""Tab „Daten" – Tabellenverwaltung für Druckdaten."""
from __future__ import annotations

import csv
import io
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import TYPE_CHECKING

import db.repository as repo
from models.types import DataRecord, Project, ProjectField

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class DataTab:
    def __init__(self, notebook: ttk.Notebook, app: "MainWindow"):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self._project: Project | None = None
        self._fields: list[ProjectField] = []
        self._records: list[DataRecord] = []
        self._build_ui()

    # ─── UI aufbauen ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Obere Button-Leiste
        btn_frame = ttk.Frame(self.frame, padding=4)
        btn_frame.pack(side=tk.TOP, fill=tk.X)

        self._btn("Hinzufügen",         btn_frame, self._add_record)
        self._btn("Importieren …",      btn_frame, self._import_csv)
        self._btn("Exportieren …",      btn_frame, self._export_csv)
        self._btn("Suchen …",           btn_frame, self._search)
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        self._btn("Alle markieren",     btn_frame, self._select_all)
        self._btn("Bearbeiten",         btn_frame, self._edit_selected)
        self._btn("Anwählen",           btn_frame, lambda: self._set_selected_flag(True))
        self._btn("Abwählen",           btn_frame, lambda: self._set_selected_flag(False))
        self._btn("Löschen",            btn_frame, self._delete_selected)
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)
        self._btn("Felder bearbeiten",  btn_frame, self._manage_fields)
        self._btn("Zahlenreihe …",      btn_frame, self._number_series)

        # Treeview mit Scrollbar
        tree_frame = ttk.Frame(self.frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._tree = ttk.Treeview(tree_frame, selectmode="extended", show="headings")
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,   command=self._tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side=tk.RIGHT,  fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._tree.pack(fill=tk.BOTH, expand=True)

        self._tree.bind("<Double-1>",    self._on_double_click)
        self._tree.bind("<Button-3>",    self._on_right_click)
        self._tree.bind("<<TreeviewSelect>>", self._on_selection_change)

        # Statuszeile
        self._status_var = tk.StringVar(value="")
        ttk.Label(self.frame, textvariable=self._status_var,
                  anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X, padx=4)

        # Kontextmenü
        self._ctx_menu = tk.Menu(self.frame, tearoff=False)
        self._ctx_menu.add_command(label="Bearbeiten",          command=self._edit_selected)
        self._ctx_menu.add_command(label="Kopieren",            command=self._copy_selected)
        self._ctx_menu.add_command(label="Einfügen",            command=self._paste_records)
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(label="Anwählen",            command=lambda: self._set_selected_flag(True))
        self._ctx_menu.add_command(label="Abwählen",            command=lambda: self._set_selected_flag(False))
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(label="Löschen",             command=self._delete_selected)

    @staticmethod
    def _btn(text: str, parent, cmd) -> ttk.Button:
        b = ttk.Button(parent, text=text, command=cmd)
        b.pack(side=tk.LEFT, padx=2)
        return b

    # ─── Daten laden ──────────────────────────────────────────────────────────

    def load_project(self, project: Project) -> None:
        self._project = project
        self._fields  = repo.list_fields(project.id)
        self._records = repo.list_records(project.id)
        self._rebuild_columns()
        self._populate_tree()

    def _rebuild_columns(self) -> None:
        cols = ["#"] + [f.name for f in self._fields]
        self._tree.config(columns=cols)
        self._tree.heading("#", text="✓")
        self._tree.column ("#", width=30, anchor=tk.CENTER, stretch=False)
        for f in self._fields:
            self._tree.heading(f.name, text=f.name,
                               command=lambda fn=f.name: self._sort_by(fn))
            self._tree.column(f.name, width=120, anchor=tk.W)

    def _populate_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for rec in self._records:
            check = "✓" if rec.selected else ""
            values = [check] + [rec.values.get(f.name, "") for f in self._fields]
            tag = "selected" if rec.selected else ""
            self._tree.insert("", tk.END, iid=str(rec.id), values=values, tags=(tag,))
        self._tree.tag_configure("selected", background="#e8f4e8")
        self._update_status()

    def _update_status(self) -> None:
        total  = len(self._records)
        active = sum(1 for r in self._records if r.selected)
        self._status_var.set(
            f"Datensätze gesamt: {total}  |  Zum Drucken angewählt: {active}"
        )

    # ─── Aktionen ─────────────────────────────────────────────────────────────

    def _add_record(self) -> None:
        if not self._project:
            return
        from ui.dialogs.record_edit import RecordEditDialog
        dlg = RecordEditDialog(self.app.root, self._fields, DataRecord(
            id=None, project_id=self._project.id,
        ))
        if dlg.result is None:
            return
        rec = repo.add_record(self._project.id, dlg.result)
        self._records.append(rec)
        self._populate_tree()
        self.app.mark_changed()

    def _edit_selected(self) -> None:
        iids = self._tree.selection()
        if not iids:
            return
        record_id = int(iids[0])
        rec = self._find_record(record_id)
        if rec is None:
            return
        from ui.dialogs.record_edit import RecordEditDialog
        dlg = RecordEditDialog(self.app.root, self._fields, rec)
        if dlg.result is None:
            return
        rec.values.update(dlg.result)
        repo.update_record(rec)
        self._populate_tree()
        self.app.mark_changed()

    def _delete_selected(self) -> None:
        iids = self._tree.selection()
        if not iids:
            return
        if not messagebox.askyesno("Löschen",
                                   f"{len(iids)} Datensatz/Datensätze löschen?"):
            return
        ids = [int(i) for i in iids]
        repo.delete_records(ids)
        self._records = [r for r in self._records if r.id not in ids]
        self._populate_tree()
        self.app.mark_changed()

    def _set_selected_flag(self, flag: bool) -> None:
        iids = self._tree.selection()
        if not iids:
            return
        ids = [int(i) for i in iids]
        repo.set_record_selected(ids, flag)
        for rec in self._records:
            if rec.id in ids:
                rec.selected = flag
        self._populate_tree()
        self.app.mark_changed()

    def _select_all(self) -> None:
        if not self._records:
            return
        all_selected = all(r.selected for r in self._records)
        flag = not all_selected
        ids = [r.id for r in self._records]
        repo.set_record_selected(ids, flag)
        for r in self._records:
            r.selected = flag
        self._populate_tree()

    def _manage_fields(self) -> None:
        if not self._project:
            return
        from ui.dialogs.field_manager import FieldManagerDialog
        FieldManagerDialog(self.app.root, self._project)
        # Reload
        self.load_project(self._project)
        self.app.mark_changed()

    def _number_series(self) -> None:
        if not self._project or not self._fields:
            messagebox.showinfo("Zahlenreihe", "Bitte zuerst Felder anlegen.")
            return
        from ui.dialogs.number_series_dialog import NumberSeriesDialog
        dlg = NumberSeriesDialog(self.app.root, self._fields, self._project.id)
        if dlg.generated:
            self.load_project(self._project)
            self.app.mark_changed()

    def _import_csv(self) -> None:
        if not self._project:
            return
        from ui.dialogs.csv_import import CsvImportDialog
        dlg = CsvImportDialog(self.app.root, self._project, self._fields)
        if dlg.imported_count:
            self.load_project(self._project)
            self.app.mark_changed()

    def _export_csv(self) -> None:
        if not self._records:
            return
        path = filedialog.asksaveasfilename(
            title="CSV exportieren",
            defaultextension=".csv",
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle", "*.*")],
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([field.name for field in self._fields])
            for rec in self._records:
                writer.writerow([rec.values.get(field.name, "") for field in self._fields])
        messagebox.showinfo("Export", f"{len(self._records)} Datensätze exportiert.")

    def _copy_selected(self) -> None:
        iids = self._tree.selection()
        if not iids:
            return
        buf = io.StringIO()
        writer = csv.writer(buf, delimiter="\t")
        for iid in iids:
            rec = self._find_record(int(iid))
            if rec:
                writer.writerow([rec.values.get(f.name, "") for f in self._fields])
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(buf.getvalue())

    def _paste_records(self) -> None:
        if not self._project:
            return
        try:
            raw = self.app.root.clipboard_get()
        except tk.TclError:
            return
        reader = csv.reader(io.StringIO(raw), delimiter="\t")
        added = 0
        for row in reader:
            if not any(row):
                continue
            values = {f.name: (row[i] if i < len(row) else "")
                      for i, f in enumerate(self._fields)}
            repo.add_record(self._project.id, values)
            added += 1
        if added:
            self.load_project(self._project)
            self.app.mark_changed()

    def _search(self) -> None:
        from ui.dialogs.search_dialog import SearchDialog
        SearchDialog(self.app.root, self._tree, self._fields, self._records)

    def _sort_by(self, field_name: str) -> None:
        self._records.sort(key=lambda r: r.values.get(field_name, ""))
        self._populate_tree()

    # ─── Events ───────────────────────────────────────────────────────────────

    def _on_double_click(self, event) -> None:
        self._edit_selected()

    def _on_right_click(self, event) -> None:
        row = self._tree.identify_row(event.y)
        if row:
            if row not in self._tree.selection():
                self._tree.selection_set(row)
            self._ctx_menu.tk_popup(event.x_root, event.y_root)

    def _on_selection_change(self, _event=None) -> None:
        pass

    # ─── Hilfsmethoden ────────────────────────────────────────────────────────

    def _find_record(self, record_id: int) -> DataRecord | None:
        return next((r for r in self._records if r.id == record_id), None)

    @property
    def records(self) -> list[DataRecord]:
        return self._records

    @property
    def fields(self) -> list[ProjectField]:
        return self._fields
