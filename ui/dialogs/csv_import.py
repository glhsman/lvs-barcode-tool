"""CSV-Import-Dialog für den Bereich „Daten"."""
from __future__ import annotations

import csv
import io
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

import db.repository as repo
import app_config
from models.types import Project, ProjectField


class CsvImportDialog:
    def __init__(self, app: "MainWindow", parent: tk.Widget, project: Project,
                 fields: list[ProjectField]):
        self.app = app
        self._project  = project
        self._fields   = fields
        self.imported_count = 0

        self._win = tk.Toplevel(parent)
        self._win.title("Daten importieren – Erweitert")
        self._win.grab_set()
        self._win.geometry("760x720")
        self._win.minsize(600, 500)

        self._headers: list[str] = []
        self._rows: list[list[str]] = []
        self._mapping: dict[str, tk.StringVar] = {}

        self._build_ui()
        
        # Letzten Pfad laden
        last_path = app_config.get_last_csv_path()
        if last_path and os.path.exists(last_path):
            self._file_var.set(last_path)
            # Optional: auto-load wenn Pfad existiert
            self._load()

        self._win.wait_window()

    def _build_ui(self) -> None:
        top = ttk.Frame(self._win, padding=10)
        top.pack(fill=tk.X)

        # Datei wählen
        f_frame = ttk.Frame(top)
        f_frame.grid(row=0, column=0, columnspan=3, sticky=tk.EW, pady=2)
        ttk.Label(f_frame, text="CSV-Datei:").pack(side=tk.LEFT)
        self._file_var = tk.StringVar()
        ttk.Entry(f_frame, textvariable=self._file_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Button(f_frame, text="Durchsuchen …", command=self._browse).pack(side=tk.LEFT)

        # Optionen
        opt_frame = ttk.LabelFrame(top, text=" Import-Optionen ", padding=8)
        opt_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=8)

        ttk.Label(opt_frame, text="Trennzeichen:").grid(row=0, column=0, sticky=tk.W)
        self._sep_var = tk.StringVar(value="Automatisch")
        ttk.Combobox(opt_frame, textvariable=self._sep_var,
                     values=["Automatisch", ",", ";", "Tab", "|"], width=12, state="readonly").grid(row=0, column=1, sticky=tk.W, padx=4, pady=2)

        ttk.Label(opt_frame, text="Zeichensatz:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self._enc_var = tk.StringVar(value="Automatisch")
        ttk.Combobox(opt_frame, textvariable=self._enc_var,
                     values=["Automatisch", "utf-8", "utf-8-sig", "latin-1", "cp1252"],
                     width=12, state="readonly").grid(row=0, column=3, sticky=tk.W, padx=4)

        self._header_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Erste Zeile als Header nutzen",
                        variable=self._header_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)

        self._clear_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="VOR IMPORT ALLE DATENSÄTZE LÖSCHEN",
                        variable=self._clear_var).grid(row=1, column=2, sticky=tk.W)

        self._reset_fields_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="FELDER AUS CSV ÜBERNEHMEN (ALTE LÖSCHEN)",
                        variable=self._reset_fields_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)

        self._session_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="NUR FÜR DIESE SITZUNG LADEN (NICHT IN DB SPEICHERN)",
                        variable=self._session_only_var).grid(row=2, column=2, columnspan=2, sticky=tk.W)

        ttk.Button(top, text="Datei analysieren & Vorschau laden", command=self._load).grid(
            row=2, column=0, columnspan=3, pady=10)

        top.columnconfigure(1, weight=1)

        # Zuordnung Bereich (Scrollable)
        ttk.Label(self._win, text=" Spaltenzuordnung: ", font=("", 9, "bold")).pack(anchor=tk.W, padx=10)
        map_outer = ttk.Frame(self._win, padding=2)
        map_outer.pack(fill=tk.X, padx=10)
        
        self._map_canvas = tk.Canvas(map_outer, height=150, highlightthickness=0)
        vsb_map = ttk.Scrollbar(map_outer, orient=tk.VERTICAL, command=self._map_canvas.yview)
        self._map_inner = ttk.Frame(self._map_canvas)
        
        self._map_canvas.create_window((0,0), window=self._map_inner, anchor=tk.NW)
        self._map_canvas.configure(yscrollcommand=vsb_map.set)
        
        self._map_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb_map.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._map_inner.bind("<Configure>", lambda e: self._map_canvas.configure(scrollregion=self._map_canvas.bbox("all")))

        # Buttons (GANZ UNTEN)
        btn_f = ttk.Frame(self._win, padding=10)
        btn_f.pack(side=tk.BOTTOM, fill=tk.X)
        self._import_btn = ttk.Button(btn_f, text="Jetzt Importieren", state="disabled",
                                      command=self._import)
        self._import_btn.pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_f, text="Abbrechen", command=self._win.destroy).pack(side=tk.RIGHT)

        # Fortschrittsbereich (ÜBER DEN BUTTONS)
        self._prog_frame = ttk.Frame(self._win, padding=(10, 0))
        self._prog_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self._progress_var = tk.DoubleVar(value=0)
        self._progress = ttk.Progressbar(self._prog_frame, variable=self._progress_var, maximum=100)
        self._progress.pack(fill=tk.X, pady=(0, 5))
        self._status_var = tk.StringVar(value="Bereit")
        ttk.Label(self._prog_frame, textvariable=self._status_var).pack(anchor=tk.W)

        # Vorschau (FÜLLT DEN RESTLICHEN PLATZ)
        preview_lf = ttk.LabelFrame(self._win, text=" Daten-Vorschau (erste 5 Zeilen) ", padding=4)
        preview_lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._preview_tree = ttk.Treeview(preview_lf, show="headings")
        vsb_p = ttk.Scrollbar(preview_lf, orient=tk.VERTICAL, command=self._preview_tree.yview)
        self._preview_tree.configure(yscrollcommand=vsb_p.set)
        vsb_p.pack(side=tk.RIGHT, fill=tk.Y)
        self._preview_tree.pack(fill=tk.BOTH, expand=True)

    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title="CSV-Datei öffnen",
            filetypes=[("CSV", "*.csv *.txt"), ("Alle", "*.*")],
        )
        if path:
            self._file_var.set(path)
            self._load() # Auto-load on select

    def _load(self) -> None:
        path = self._file_var.get()
        if not path: return

        # Encoding-Erkennung
        encs = [self._enc_var.get()] if self._enc_var.get() != "Automatisch" else ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
        
        all_rows = []
        used_enc = ""
        for enc in encs:
            try:
                with open(path, newline="", encoding=enc) as f:
                    content = f.read(4096)
                    f.seek(0)
                    
                    # Delimiter-Erkennung
                    sep = self._sep_var.get()
                    if sep == "Automatisch" or not sep:
                        try:
                            dialect = csv.Sniffer().sniff(content, delimiters=",;\t|")
                            sep = dialect.delimiter
                        except:
                            sep = ";" # Fallback
                    elif sep == "Tab":
                        sep = "\t"
                    
                    reader = csv.reader(f, delimiter=sep)
                    all_rows = list(reader)
                    used_enc = enc
                    break
            except (UnicodeDecodeError, csv.Error):
                continue
        
        if not all_rows:
            messagebox.showerror("Fehler", f"Datei konnte nicht gelesen werden oder ist leer.\nGetestete Encodings: {encs}")
            return
        
        # Pfad merken
        app_config.set_last_csv_path(path)

        print(f"Import: Nutze Encoding {used_enc} und Trenner '{sep}'")

        if self._header_var.get():
            self._headers = all_rows[0]
            self._rows    = all_rows[1:]
        else:
            self._headers = [f"Spalte {i+1}" for i in range(len(all_rows[0]))]
            self._rows    = all_rows

        self._build_mapping()
        self._show_preview()
        self._import_btn.configure(state="normal")

    def _build_mapping(self) -> None:
        for w in self._map_inner.winfo_children():
            w.destroy()
        self._mapping = {}
        field_names = ["(ignorieren)"] + [f.name for f in self._fields]
        
        ttk.Label(self._map_inner, text="Spalte in CSV", font=("", 8, "bold")).grid(row=0, column=0, padx=5, sticky=tk.W)
        ttk.Label(self._map_inner, text="→ Feld im Ziel", font=("", 8, "bold")).grid(row=0, column=1, padx=5, sticky=tk.W)
        
        for i, hdr in enumerate(self._headers):
            ttk.Label(self._map_inner, text=hdr[:30] + ("..." if len(hdr)>30 else "")).grid(
                row=i+1, column=0, sticky=tk.W, padx=5, pady=1)
            var = tk.StringVar()
            # Intelligente Vorausswahl
            match = next((f.name for f in self._fields if f.name.lower() == hdr.lower().strip()), "(ignorieren)")
            var.set(match)
            self._mapping[hdr] = var
            ttk.Combobox(self._map_inner, textvariable=var, values=field_names,
                         state="readonly", width=25).grid(row=i+1, column=1, sticky=tk.W, padx=5, pady=1)

    def _show_preview(self) -> None:
        self._preview_tree.delete(*self._preview_tree.get_children())
        self._preview_tree.config(columns=self._headers)
        for h in self._headers:
            self._preview_tree.heading(h, text=h)
            self._preview_tree.column(h, width=120)
        for row in self._rows[:5]:
            self._preview_tree.insert("", tk.END, values=row)

    def _import(self) -> None:
        if not self._rows: return
        
        if self._reset_fields_var.get():
            if messagebox.askyesno("Felder löschen", 
                                   "Sollen wirklich ALLE vorhandenen Felder UND Daten gelöscht werden?\n"
                                   "Die neuen Felder werden direkt aus der CSV-Header-Zeile erstellt."):
                self._status_var.set("Lösche alte Strukturen...")
                self._win.update()
                repo.delete_records_by_project(self._project.id)
                repo.delete_fields_by_project(self._project.id)
                
                # Neue Felder anlegen
                for hdr in self._headers:
                    repo.add_field(self._project.id, hdr)
                
                # Felder-Liste im Dialog-Objekt aktualisieren für den folgenden Import-Schritt
                self._fields = repo.list_fields(self._project.id)
            else:
                return # Abbrechen wenn User Nein sagt

        elif self._clear_var.get():
            if messagebox.askyesno("Löschen", "Sollen wirklich ALLE vorhandenen Daten gelöscht werden?"):
                repo.delete_records_by_project(self._project.id)
        
        # Aktive Mappings sammeln (Spalten-Index -> Field Name)
        self._fields = repo.list_fields(self._project.id) # Sicherstellen dass wir die aktuellen IDs haben
        active_map = {}
        
        if self._reset_fields_var.get():
            # Automatisches 1:1 Mapping bei Feld-Neuerstellung
            active_map = {i: hdr for i, hdr in enumerate(self._headers)}
        else:
            # Manuelles Mapping aus der UI nutzen
            for i, hdr in enumerate(self._headers):
                target = self._mapping.get(hdr)
                if target:
                    val = target.get()
                    if val and val != "(ignorieren)":
                        active_map[i] = val
        
        if not active_map:
            messagebox.showwarning("Import", "Keine Spalten für den Import zugeordnet.")
            return

        self._import_btn.configure(state="disabled")
        valid_records = []
        errors = 0
        
        total_rows = len(self._rows)
        for i, row in enumerate(self._rows):
            if i % 500 == 0:
                perc = (i / total_rows) * 100
                self._progress_var.set(perc)
                self._status_var.set(f"Bereite Daten vor: {i} von {total_rows} ...")
                self._win.update()
            try:
                values = {}
                for idx, field_name in active_map.items():
                    val = row[idx] if idx < len(row) else ""
                    values[field_name] = val.strip()
                
                if any(values.values()):
                    valid_records.append(values)
            except Exception:
                errors += 1

        def update_progress(current, total):
            perc = (current / total) * 100
            self._progress_var.set(perc)
            self._status_var.set(f"In Datenbank speichern: {current} von {total} ...")
            self._win.update()

        try:
            if self._session_only_var.get():
                self._import_session_only(valid_records)
            else:
                self._import_to_db(valid_records, update_progress)
            
            self._win.destroy()
        except Exception as exc:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Import Fehler", f"Ein unerwarteter Fehler ist aufgetreten:\n{exc}")
            self._import_btn.configure(state="normal")

    def _import_session_only(self, valid_records_values: list[dict[str, str]]) -> None:
        from models.types import DataRecord
        self._status_var.set("Übergebe Daten an Hauptfenster...")
        self._win.update()
        
        temp_records = []
        for i, vals in enumerate(valid_records_values):
            temp_records.append(DataRecord(
                id=-(i+1), 
                project_id=self._project.id,
                selected=False,
                position=i,
                values=vals
            ))
        
        import_count = len(temp_records)
        # Aktuellen Stand der Felder übergeben (falls sie gerade neu erstellt wurden)
        self.app.tab_data.set_temporary_records(temp_records, fields=self._fields)
        
        messagebox.showinfo("Session Import", 
                            f"{import_count} Datensätze wurden temporär geladen.\n"
                            "⚠️ Diese Daten werden NICHT in der Datenbank gespeichert und "
                            "gehen beim Schließen oder Projektwechsel verloren.")

    def _import_to_db(self, valid_records, update_progress_cb) -> None:
        try:
            repo.add_records_batch(
                self._project.id, 
                valid_records, 
                progress_callback=update_progress_cb
            )
            self.imported_count = len(valid_records)
            messagebox.showinfo("Import abgeschlossen", f"{self.imported_count} Datensätze erfolgreich importiert.")
        except Exception as exc:
            messagebox.showerror("Fehler", f"Fehler beim Batch-Import:\n{exc}")
            self._import_btn.configure(state="normal")
