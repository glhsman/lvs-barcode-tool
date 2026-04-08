"""Hauptfenster der Anwendung mit Notebook (Daten / Etikett / Druck)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

import db.repository as repo
from models.types import Project
from db.connection import test_connection
import app_config


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Drinkport-Barcode – Python Edition")
        
        # Icon setzen (falls vorhanden)
        import os
        if os.path.exists("icon.ico"):
            try:
                self.root.iconbitmap("icon.ico")
            except Exception:
                pass

        self.root.geometry("1200x780")
        self.root.minsize(900, 600)

        self.current_project: Project | None = None
        self._projects: list[Project] = []

        self._build_menu()
        self._build_toolbar()
        self._build_notebook()
        self._build_statusbar()

        self._check_db_connection()
        self._refresh_project_list()

    # ─── Menü ─────────────────────────────────────────────────────────────────

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        m_project = tk.Menu(menubar, tearoff=False)
        m_project.add_command(label="Neu …",           command=self._project_new)
        m_project.add_command(label="Umbenennen …",    command=self._project_rename)
        m_project.add_separator()
        m_project.add_command(label="Löschen …",       command=self._project_delete)
        m_project.add_separator()
        m_project.add_command(label="Beenden",         command=self.root.quit)
        menubar.add_cascade(label="Projekt", menu=m_project)

        m_settings = tk.Menu(menubar, tearoff=False)
        m_settings.add_command(label="Optionen …",     command=self._show_options)
        menubar.add_cascade(label="Einstellungen", menu=m_settings)

        m_help = tk.Menu(menubar, tearoff=False)
        m_help.add_command(label="Über …",             command=self._show_about)
        menubar.add_cascade(label="Hilfe", menu=m_help)

        self.root.config(menu=menubar)

    # ─── Toolbar (Projektauswahl) ──────────────────────────────────────────────

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self.root, padding=4)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(toolbar, text="Projekt:").pack(side=tk.LEFT, padx=(0, 4))

        self._project_var = tk.StringVar()
        self._project_combo = ttk.Combobox(
            toolbar, textvariable=self._project_var, width=35, state="readonly"
        )
        self._project_combo.pack(side=tk.LEFT, padx=(0, 6))
        self._project_combo.bind("<<ComboboxSelected>>", self._on_project_selected)

        ttk.Button(toolbar, text="Neu",        command=self._project_new,    width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Umbenennen", command=self._project_rename, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Löschen",    command=self._project_delete, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="↻ Aktualisieren", command=self._refresh_all, width=14).pack(side=tk.LEFT, padx=10)

        self._changed_label = ttk.Label(toolbar, text="", foreground="red")
        self._changed_label.pack(side=tk.RIGHT, padx=8)

    # ─── Notebook (3 Tabs) ────────────────────────────────────────────────────

    def _build_notebook(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        from ui.tab_data  import DataTab
        from ui.tab_label import LabelTab
        from ui.tab_print import PrintTab

        self.tab_data  = DataTab(self.notebook,  self)
        self.tab_label = LabelTab(self.notebook, self)
        self.tab_print = PrintTab(self.notebook, self)

        self.notebook.add(self.tab_data.frame,  text="  Daten  ")
        self.notebook.add(self.tab_label.frame, text="  Etikett  ")
        self.notebook.add(self.tab_print.frame, text="  Druck  ")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # ─── Statusleiste ─────────────────────────────────────────────────────────

    def _build_statusbar(self) -> None:
        self._status_var = tk.StringVar(value="Bereit")
        bar = ttk.Label(self.root, textvariable=self._status_var,
                        relief=tk.SUNKEN, anchor=tk.W, padding=(4, 1))
        bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ─── DB-Verbindungstest ───────────────────────────────────────────────────

    def _check_db_connection(self) -> None:
        try:
            version = test_connection()
            self.set_status(f"MariaDB verbunden – Server: {version}")
        except Exception as exc:
            messagebox.showerror(
                "Datenbankfehler",
                f"Verbindung fehlgeschlagen:\n{exc}\n\n"
                "Bitte config.ini prüfen und ggf. python db_setup.py ausführen.",
            )

    # ─── Projektverwaltung ────────────────────────────────────────────────────

    def _refresh_project_list(self) -> None:
        try:
            self._projects = repo.list_projects()
        except Exception as exc:
            self.set_status(f"Fehler beim Laden der Projekte: {exc}")
            return
        names = [p.name for p in self._projects]
        self._project_combo["values"] = names
        if self.current_project:
            if self.current_project.name in names:
                self._project_var.set(self.current_project.name)
            else:
                self.current_project = None
                self._project_var.set("")
        elif names:
            self._project_var.set(names[0])
            self._load_project_by_name(names[0])

    def _on_project_selected(self, _event=None) -> None:
        name = self._project_var.get()
        self._load_project_by_name(name)

    def _load_project_by_name(self, name: str) -> None:
        project = next((p for p in self._projects if p.name == name), None)
        if project is None:
            return
        self.current_project = project
        self._load_all_tabs()

    def _load_all_tabs(self) -> None:
        if self.current_project is None:
            return
        self.tab_data.load_project(self.current_project)
        self.tab_label.load_project(self.current_project)
        self.tab_print.load_project(self.current_project)
        self.set_status(f"Projekt geladen: {self.current_project.name}")

    def _refresh_all(self) -> None:
        try:
            self._refresh_project_list()
            if self.current_project:
                self._load_all_tabs()
            else:
                self._changed_label.config(text="")
        except Exception:
            self.set_status("⚠️ Datenbank-Fehler bei Aktualisierung.")
        self.mark_changed(False)

    def _project_new(self) -> None:
        from ui.dialogs.project_dialogs import ask_project_name
        name = ask_project_name(self.root, title="Neues Projekt")
        if not name:
            return
        try:
            project = repo.create_project(name)
        except Exception as exc:
            messagebox.showerror("Fehler", str(exc))
            return
        self._refresh_project_list()
        self._project_var.set(project.name)
        self._load_project_by_name(project.name)

    def _project_rename(self) -> None:
        if not self.current_project:
            return
        from ui.dialogs.project_dialogs import ask_project_name
        name = ask_project_name(self.root, title="Umbenennen",
                                initial=self.current_project.name)
        if not name or name == self.current_project.name:
            return
        try:
            repo.rename_project(self.current_project.id, name)
            self.current_project.name = name
        except Exception as exc:
            messagebox.showerror("Fehler", str(exc))
            return
        self._refresh_project_list()

    def _project_delete(self) -> None:
        if not self.current_project:
            return
        if not messagebox.askyesno(
            "Projekt löschen",
            f"Projekt «{self.current_project.name}» wirklich löschen?\n"
            "Alle Daten, Etiketten und gespeicherte Etiketten werden entfernt.",
        ):
            return
        try:
            repo.delete_project(self.current_project.id)
        except Exception as exc:
            messagebox.showerror("Fehler", str(exc))
            return
        self.current_project = None
        self._refresh_project_list()

    # ─── Tab-Wechsel ──────────────────────────────────────────────────────────

    def _on_tab_changed(self, _event=None) -> None:
        tab = self.notebook.index(self.notebook.select())
        if tab == 2:  # Druck-Tab
            self.tab_print.refresh_preview()

    # ─── Hilfsmethoden ────────────────────────────────────────────────────────

    def set_status(self, msg: str) -> None:
        self._status_var.set(msg)

    def mark_changed(self, changed: bool = True) -> None:
        self._changed_label.config(
            text="● Projekt wurde verändert" if changed else ""
        )

    def _show_options(self) -> None:
        messagebox.showinfo("Optionen", "Konfiguration via config.ini (im Programmordner).")

    def _show_about(self) -> None:
        messagebox.showinfo(
            "Über Drinkport-Barcode – Python Edition",
            "Drinkport-Barcode – Python Edition\n"
            "Moderne Lösung für Lagerbeschriftungen\n\n"
            "Barcode-Engine: Python Native (barcode/qrcode)\n"
            "Datenbank: MariaDB\n"
            f"Benutzer: {app_config.get_username()}",
        )
