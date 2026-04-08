"""Tab „Druck" – Etiketten-Vorschau, Navigation und Export/Speicherung in DB."""
from __future__ import annotations

import io
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import TYPE_CHECKING, Optional

from PIL import Image, ImageTk

import db.repository as repo
import app_config
from models.types import Project, SavedLabel
from barcode_engine.renderer import render_label, label_to_bytes

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class PrintTab:
    def __init__(self, notebook: ttk.Notebook, app: "MainWindow"):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self._project: Optional[Project] = None
        self._current_record_idx: int = 0
        self._preview_image: Optional[ImageTk.PhotoImage] = None
        self._build_ui()

    # ─── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Obere Steuerleiste
        ctrl = ttk.Frame(self.frame, padding=6)
        ctrl.pack(side=tk.TOP, fill=tk.X)

        # Datensatz-Navigation
        ttk.Label(ctrl, text="Vorschau mit Datensatz Nr.:").pack(side=tk.LEFT)
        self._use_record_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(ctrl, variable=self._use_record_var,
                        command=self.refresh_preview).pack(side=tk.LEFT, padx=4)

        ttk.Button(ctrl, text="◀◀", width=4,
                   command=lambda: self._goto(0)).pack(side=tk.LEFT)
        ttk.Button(ctrl, text="◀",  width=3,
                   command=lambda: self._goto(self._current_record_idx - 1)).pack(side=tk.LEFT)

        self._record_var = tk.StringVar(value="1")
        rec_entry = ttk.Entry(ctrl, textvariable=self._record_var, width=5)
        rec_entry.pack(side=tk.LEFT, padx=2)
        rec_entry.bind("<Return>", lambda e: self._goto_str(self._record_var.get()))

        self._record_total_label = ttk.Label(ctrl, text="/ 0")
        self._record_total_label.pack(side=tk.LEFT)

        ttk.Button(ctrl, text="▶",  width=3,
                   command=lambda: self._goto(self._current_record_idx + 1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="▶▶", width=4,
                   command=lambda: self._goto(9999)).pack(side=tk.LEFT)

        ttk.Separator(ctrl, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # DPI
        ttk.Label(ctrl, text="Auflösung (dpi):").pack(side=tk.LEFT)
        self._dpi_var = tk.StringVar(value=str(app_config.get_default_dpi()))
        ttk.Spinbox(ctrl, from_=72, to=1200, textvariable=self._dpi_var,
                    width=6, command=self.refresh_preview).pack(side=tk.LEFT, padx=4)

        # Aktionen (rechts, zweizeilig)
        action_wrap = ttk.Frame(ctrl)
        action_wrap.pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Separator(ctrl, orient=tk.VERTICAL).pack(side=tk.RIGHT, fill=tk.Y, padx=8)

        action_btns = [
            ("In DB speichern", self._save_to_db),
            ("Als PNG exportieren", lambda: self._export("PNG")),
            ("Als PDF exportieren", lambda: self._export("PDF")),
            ("Drucken …", self._print_current),
            ("↻ Aktualisieren", self.refresh_preview),
        ]
        for i, (label, cmd) in enumerate(action_btns):
            r = 0 if i < 3 else 1
            c = i if i < 3 else i - 3
            ttk.Button(action_wrap, text=label, command=cmd).grid(
                row=r, column=c, padx=2, pady=1, sticky="ew"
            )
        for col in range(3):
            action_wrap.grid_columnconfigure(col, weight=1)

        # Hauptbereich: links Vorschau, rechts Liste gespeicherter Etiketten
        main = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Vorschau-Canvas
        preview_frame = ttk.LabelFrame(main, text=" Vorschau ")
        main.add(preview_frame, weight=3)

        self._canvas = tk.Canvas(preview_frame, bg="#1e1e1e", highlightthickness=0)
        vsb = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL,
                            command=self._canvas.yview)
        hsb = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL,
                            command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT,  fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._canvas.pack(fill=tk.BOTH, expand=True)

        # Gespeicherte Etiketten
        saved_frame = ttk.LabelFrame(main, text=" Gespeicherte Etiketten ")
        main.add(saved_frame, weight=1)

        self._saved_tree = ttk.Treeview(
            saved_frame,
            columns=("name", "date", "by"),
            show="headings",
            selectmode="browse",
        )
        self._saved_tree.heading("name", text="Name")
        self._saved_tree.heading("date", text="Datum")
        self._saved_tree.heading("by",   text="Benutzer")
        self._saved_tree.column("name", width=120)
        self._saved_tree.column("date", width=120)
        self._saved_tree.column("by",   width=80)

        vsb2 = ttk.Scrollbar(saved_frame, orient=tk.VERTICAL,
                             command=self._saved_tree.yview)
        self._saved_tree.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side=tk.RIGHT, fill=tk.Y)
        self._saved_tree.pack(fill=tk.BOTH, expand=True)
        self._saved_tree.bind("<<TreeviewSelect>>", self._show_saved_label)

        btn_saved = ttk.Frame(saved_frame)
        btn_saved.pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(btn_saved, text="Anzeigen",  command=self._show_saved_label).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_saved, text="Exportieren", command=self._export_saved).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_saved, text="Löschen",   command=self._delete_saved).pack(side=tk.LEFT, padx=2)

        # Statuszeile
        self._status_var = tk.StringVar(value="")
        ttk.Label(self.frame, textvariable=self._status_var,
                  relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    # ─── Projekt laden ────────────────────────────────────────────────────────

    def load_project(self, project: Project) -> None:
        self._project = project
        self._current_record_idx = 0
        self._refresh_record_count()
        self._load_saved_labels()

    def _refresh_record_count(self) -> None:
        if not self._project:
            return
        records = self.app.tab_data.records
        total = len(records)
        self._record_total_label.config(text=f"/ {total}")

    # ─── Vorschau ─────────────────────────────────────────────────────────────

    def refresh_preview(self, _event=None) -> None:
        if not self._project:
            return
        fmt = self.app.tab_label.label_format
        objs = self.app.tab_label.label_objects
        if not fmt:
            return

        records = self.app.tab_data.records
        if not records or not self._use_record_var.get():
            values: dict[str, str] = {}
        else:
            idx = max(0, min(self._current_record_idx, len(records) - 1))
            values = records[idx].values

        try:
            dpi = int(self._dpi_var.get())
        except ValueError:
            dpi = app_config.get_default_dpi()

        try:
            pil_img = render_label(fmt, objs, values, dpi=min(dpi, 300))
            # Auf Bildschirmauflösung herunterskalieren für die Vorschau
            max_w, max_h = 800, 600
            ratio = min(max_w / max(pil_img.width, 1), max_h / max(pil_img.height, 1))
            if ratio < 1.0:
                new_w = int(pil_img.width  * ratio)
                new_h = int(pil_img.height * ratio)
                pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)

            self._preview_image = ImageTk.PhotoImage(pil_img)
            self._canvas.delete("all")
            ox, oy = 10, 10
            self._canvas.create_image(ox, oy, anchor=tk.NW, image=self._preview_image)
            self._canvas.config(scrollregion=(0, 0,
                                              ox + pil_img.width + 10,
                                              oy + pil_img.height + 10))
            self._status_var.set(
                f"Vorschau: {pil_img.width}×{pil_img.height} px  "
                f"(Etikett: {fmt.width_mm:.1f}×{fmt.height_mm:.1f} mm)"
            )
        except Exception as exc:
            self._canvas.delete("all")
            self._canvas.create_text(20, 20, anchor=tk.NW,
                                     text=f"Fehler beim Rendern:\n{exc}",
                                     fill="red")

    def _goto(self, idx: int) -> None:
        records = self.app.tab_data.records
        if not records:
            return
        self._current_record_idx = max(0, min(idx, len(records) - 1))
        self._record_var.set(str(self._current_record_idx + 1))
        self.refresh_preview()

    def _goto_str(self, s: str) -> None:
        try:
            n = int(s) - 1
        except ValueError:
            return
        self._goto(n)

    # ─── In DB speichern ──────────────────────────────────────────────────────

    def _save_to_db(self) -> None:
        if not self._project:
            return
        fmt = self.app.tab_label.label_format
        objs = self.app.tab_label.label_objects
        if not fmt:
            messagebox.showwarning("Speichern", "Kein Etikettenformat definiert.")
            return

        records = self.app.tab_data.records
        if not records:
            messagebox.showwarning("Speichern", "Keine Datensätze vorhanden.")
            return

        idx = max(0, min(self._current_record_idx, len(records) - 1))
        record = records[idx]
        name = f"{self._project.name} – DS #{record.id}"

        try:
            dpi = int(self._dpi_var.get())
        except ValueError:
            dpi = app_config.get_default_dpi()

        try:
            img_bytes = label_to_bytes(fmt, objs, record.values, dpi=dpi, fmt_str="PNG")
        except Exception as exc:
            messagebox.showerror("Fehler", f"Rendern fehlgeschlagen:\n{exc}")
            return

        label = SavedLabel(
            id=None,
            project_id=self._project.id,
            record_id=record.id,
            name=name,
            image_data=img_bytes,
            image_format="PNG",
            dpi=dpi,
            created_by=app_config.get_username(),
        )
        repo.save_label(label)
        self._load_saved_labels()
        self.app.mark_changed(False)
        messagebox.showinfo("Gespeichert",
                            f"Etikett «{name}» in der Datenbank gespeichert.")

    # ─── Exportieren ──────────────────────────────────────────────────────────

    def _export(self, fmt_str: str) -> None:
        if not self._project:
            return
        fmt = self.app.tab_label.label_format
        objs = self.app.tab_label.label_objects
        if not fmt:
            return

        records = self.app.tab_data.records
        values: dict[str, str] = {}
        if records and self._use_record_var.get():
            idx = max(0, min(self._current_record_idx, len(records) - 1))
            values = records[idx].values

        try:
            dpi = int(self._dpi_var.get())
        except ValueError:
            dpi = app_config.get_default_dpi()

        if fmt_str == "PDF":
            ext = ".pdf"
            filetypes = [("PDF", "*.pdf")]
        else:
            ext = ".png"
            filetypes = [("PNG-Bild", "*.png")]

        path = filedialog.asksaveasfilename(
            title=f"Etikett als {fmt_str} speichern",
            defaultextension=ext,
            filetypes=filetypes,
        )
        if not path:
            return

        try:
            pil_img = render_label(fmt, objs, values, dpi=dpi)
            if fmt_str == "PDF":
                pil_img.save(path, "PDF", resolution=dpi)
            else:
                pil_img.save(path, "PNG")
            messagebox.showinfo("Export", f"Etikett gespeichert:\n{path}")
        except Exception as exc:
            messagebox.showerror("Fehler", str(exc))

    # ─── Gespeicherte Etiketten ───────────────────────────────────────────────

    def _load_saved_labels(self) -> None:
        if not self._project:
            return
        self._saved_tree.delete(*self._saved_tree.get_children())
        try:
            rows = repo.list_saved_labels(self._project.id)
        except Exception:
            return
        for row in rows:
            created = row["created_at"].strftime("%d.%m.%Y %H:%M") \
                if hasattr(row["created_at"], "strftime") else str(row["created_at"])
            self._saved_tree.insert(
                "", tk.END, iid=str(row["id"]),
                values=(row["name"] or "", created, row["created_by"] or ""),
            )

    def _show_saved_label(self, _event=None) -> None:
        sel = self._saved_tree.selection()
        if not sel:
            return
        label_id = int(sel[0])
        data = repo.load_saved_label(label_id)
        if not data:
            return
        try:
            pil_img = Image.open(io.BytesIO(data))
            max_w, max_h = 800, 600
            ratio = min(max_w / max(pil_img.width, 1), max_h / max(pil_img.height, 1))
            if ratio < 1.0:
                pil_img = pil_img.resize((int(pil_img.width * ratio),
                                          int(pil_img.height * ratio)), Image.LANCZOS)
            self._preview_image = ImageTk.PhotoImage(pil_img)
            self._canvas.delete("all")
            self._canvas.create_image(10, 10, anchor=tk.NW, image=self._preview_image)
            self._canvas.config(scrollregion=(0, 0,
                                              pil_img.width + 20,
                                              pil_img.height + 20))
        except Exception as exc:
            messagebox.showerror("Fehler", str(exc))

    def _export_saved(self) -> None:
        sel = self._saved_tree.selection()
        if not sel:
            return
        label_id = int(sel[0])
        data = repo.load_saved_label(label_id)
        if not data:
            return
        path = filedialog.asksaveasfilename(
            title="Gespeichertes Etikett exportieren",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("Alle", "*.*")],
        )
        if path:
            with open(path, "wb") as f:
                f.write(data)
            messagebox.showinfo("Export", f"Gespeichert:\n{path}")

    def _delete_saved(self) -> None:
        sel = self._saved_tree.selection()
        if not messagebox.askyesno("Löschen", "Gespeichertes Etikett löschen?"):
            return
        repo.delete_saved_label(int(sel[0]))
        self._load_saved_labels()

    def _print_current(self) -> None:
        if not self._project:
            return
        from utils.printer import list_printers, print_pil_image, show_printer_properties
        printers = list_printers()
        if not printers:
            messagebox.showerror("Drucken", "Keine Drucker gefunden.")
            return

        choice_win = tk.Toplevel(self.app.root)
        choice_win.title("Drucker wählen")
        choice_win.geometry("380x480")
        choice_win.grab_set()

        ttk.Label(choice_win, text="Wähle den Etikettendrucker:", padding=10).pack()
        
        listbox = tk.Listbox(choice_win, font=("Arial", 10))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        for p in printers:
            listbox.insert(tk.END, p)
        
        try:
            import win32print
            default = win32print.GetDefaultPrinter()
            if default in printers:
                idx = printers.index(default)
                listbox.selection_set(idx)
                listbox.see(idx)
        except Exception:
            pass

        def on_configure():
            sel = listbox.curselection()
            if not sel:
                return
            printer = printers[sel[0]]
            show_printer_properties(printer, choice_win.winfo_id())

        def do_print():
            sel = listbox.curselection()
            if not sel:
                return
            printer = printers[sel[0]]
            fmt = self.app.tab_label.label_format
            objs = self.app.tab_label.label_objects
            records = self.app.tab_data.records
            values: dict[str, str] = {}
            if records and self._use_record_var.get():
                idx = max(0, min(self._current_record_idx, len(records) - 1))
                values = records[idx].values
            
            try:
                # Rendern mit hoher DPI für den Druck (300)
                img = render_label(fmt, objs, values, dpi=300)
                print_pil_image(img, printer, title=f"Drinkport-Barcode - {self._project.name}")
                choice_win.destroy()
            except Exception as exc:
                messagebox.showerror("Fehler", str(exc))

        btn_grid = ttk.Frame(choice_win, padding=10)
        btn_grid.pack(fill=tk.X)
        
        ttk.Button(btn_grid, text="Druckereigenschaften …", command=on_configure).pack(fill=tk.X, pady=2)
        ttk.Button(btn_grid, text="JETZT DRUCKEN", command=do_print).pack(fill=tk.X, pady=5)
        ttk.Button(btn_grid, text="Abbrechen", command=choice_win.destroy).pack(fill=tk.X)
