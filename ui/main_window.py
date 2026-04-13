"""Hauptfenster der Anwendung mit Notebook (Daten / Etikett / Druck)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

import db.repository as repo
from models.types import Project
from db.connection import test_connection
import app_config


class MainWindow:
    def __init__(self, root: tk.Tk, admin_mode: bool = False):
        self.root = root
        self.admin_mode = admin_mode
        self.root.title("Drinkport-Barcode – Python Edition")
        self._theme_var = tk.StringVar(value=getattr(self.root, "theme_profile", "soft_plus"))
        
        # Icon setzen (falls vorhanden)
        import os
        if os.path.exists("icon.ico"):
            try:
                self.root.iconbitmap("icon.ico")
            except Exception:
                pass

        min_w, min_h = 1100, 680
        self.root.minsize(min_w, min_h)
        pref_w, pref_h = 1233, 800
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        init_w = min(pref_w, max(min_w, screen_w - 60))
        init_h = min(pref_h, max(min_h, screen_h - 90))
        self.root.geometry(f"{init_w}x{init_h}")

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
        
        # Einstellungen (Theme immer, Vorlagen nur für Admin)
        m_settings = tk.Menu(menubar, tearoff=False)
        if self.admin_mode:
            m_settings.add_command(label="Vorlagen verwalten …", command=self._manage_templates)
        
        m_theme = tk.Menu(m_settings, tearoff=False)
        m_theme.add_radiobutton(label="Heller (Soft Plus)", variable=self._theme_var, value="soft_plus", command=self._apply_theme_from_menu)
        m_theme.add_radiobutton(label="Mittel (Soft)",      variable=self._theme_var, value="soft",      command=self._apply_theme_from_menu)
        m_theme.add_radiobutton(label="Dunkel (Standard)",  variable=self._theme_var, value="dark",      command=self._apply_theme_from_menu)

        m_settings.add_cascade(label="Theme", menu=m_theme)
        menubar.add_cascade(label="Einstellungen", menu=m_settings)

        m_help = tk.Menu(menubar, tearoff=False)
        m_help.add_command(label="Handbuch (HTML)",    command=self._show_manual)
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

        # Globale Suche (für Print-Tab Navigation)
        self._search_var = tk.StringVar()
        ttk.Button(toolbar, text="Suchen", command=self._on_search_btn, width=8).pack(side=tk.RIGHT, padx=(0, 10))
        search_entry = ttk.Entry(toolbar, textvariable=self._search_var, width=20)
        search_entry.pack(side=tk.RIGHT, padx=4)
        search_entry.bind("<Return>", lambda e: self._on_search_btn())
        ttk.Label(toolbar, text="🔍 Datensatz suchen:").pack(side=tk.RIGHT, padx=(20, 0))

    def _on_search_btn(self) -> None:
        term = self._search_var.get().strip()
        if not term:
            return
        # Zum Print-Tab wechseln und suchen
        self.notebook.select(2)
        self.tab_print.search_and_jump(term)

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
        self._window_size_var = tk.StringVar(value="")

        bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(4, 1))
        bar.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Label(bar, textvariable=self._status_var, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(bar, textvariable=self._window_size_var, anchor=tk.E).pack(side=tk.RIGHT)

        self.root.bind("<Configure>", self._on_root_configure)
        self._window_size_var.set(f"Fenster: {self.root.winfo_width()} x {self.root.winfo_height()}")

    def _on_root_configure(self, event) -> None:
        if event.widget is self.root:
            self._window_size_var.set(f"Fenster: {event.width} x {event.height}")

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

    def _apply_theme_from_menu(self) -> None:
        profile = self._theme_var.get()
        applier = getattr(self.root, "apply_theme_profile", None)
        if callable(applier):
            try:
                applier(profile)
                self.set_status(f"Theme aktiv: {profile}")
            except Exception as exc:
                messagebox.showerror("Theme", f"Theme konnte nicht gesetzt werden:\n{exc}")

    def _manage_templates(self) -> None:
        from ui.dialogs.template_manager import TemplateManagerDialog
        TemplateManagerDialog(self.root)

    def _show_about(self) -> None:
        messagebox.showinfo(
            "Über Drinkport-Barcode – Python Edition",
            "Drinkport-Barcode – Python Edition\n"
            "Version 1.6\n"
            "Moderne Lösung für Lagerbeschriftungen\n\n"
            "Barcode-Engine: Python Native (barcode/qrcode)\n"
            "Datenbank: MariaDB\n"
            f"Benutzer: {app_config.get_username()}",
        )

    def _show_manual(self) -> None:
        """Öffnet das Benutzerhandbuch (HANDBUCH.html) im Browser."""
        import webbrowser
        import os
        import sys

        # Pfad zum Handbuch ermitteln (PyInstaller-kompatibel)
        if getattr(sys, 'frozen', False):
            # Wenn als exe eingefroren, ist der Pfad in sys._MEIPASS (onedir/onefile)
            base_path = sys._MEIPASS
        else:
            # Im Entwicklungsmodus
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        manual_path = os.path.join(base_path, "HANDBUCH.html")

        if os.path.exists(manual_path):
            webbrowser.open(f"file:///{os.path.abspath(manual_path)}")
        else:
            messagebox.showerror(
                "Fehler",
                f"Handbuch nicht gefunden unter:\n{manual_path}"
            )
