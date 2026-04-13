"""Dialog für den Seriendruck von mehreren Etiketten."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, List

from barcode_engine.renderer import render_label
from utils.printer import list_printers, print_pil_images, show_printer_properties

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class BatchPrintDialog:
    def __init__(self, parent: tk.Widget, app: "MainWindow"):
        self.app = app
        self._win = tk.Toplevel(parent)
        self._win.title("Seriendruck (Batch Print)")
        self._win.geometry("450x550")
        self._win.grab_set()

        self._project = app.current_project
        self._records = app.tab_data.records
        self._selected_indices = [i for i, r in enumerate(self._records) if r.selected]

        self._selection_var = tk.StringVar(value="selected" if self._selected_indices else "all")
        self._printer_var = tk.StringVar()
        
        self._build_ui()

    def _build_ui(self) -> None:
        main = ttk.Frame(self._win, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # 1. Auswahl
        group_sel = ttk.LabelFrame(main, text=" Datensätze auswählen ", padding=8)
        group_sel.pack(fill=tk.X, pady=(0, 10))

        ttk.Radiobutton(group_sel, text=f"Alle Datensätze ({len(self._records)})",
                        variable=self._selection_var, value="all").pack(anchor=tk.W)
        
        rb_sel = ttk.Radiobutton(group_sel, text=f"Nur für Druck markierte Datensätze ({len(self._selected_indices)})",
                                 variable=self._selection_var, value="selected")
        rb_sel.pack(anchor=tk.W)
        if not self._selected_indices:
            rb_sel.configure(state="disabled")

        # 2. Drucker
        group_prn = ttk.LabelFrame(main, text=" Drucker wählen ", padding=8)
        group_prn.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self._printer_list = tk.Listbox(group_prn, font=("Arial", 10))
        self._printer_list.pack(fill=tk.BOTH, expand=True)
        
        printers = list_printers()
        for p in printers:
            self._printer_list.insert(tk.END, p)
        
        # Default Drucker vorselektieren
        try:
            import win32print
            default = win32print.GetDefaultPrinter()
            if default in printers:
                idx = printers.index(default)
                self._printer_list.selection_set(idx)
                self._printer_list.see(idx)
        except Exception:
            pass

        ttk.Button(group_prn, text="Druckereigenschaften …", 
                   command=self._on_printer_props).pack(fill=tk.X, pady=(4, 0))

        # 3. Fortschritt
        self._progress_var = tk.DoubleVar(value=0)
        self._progress = ttk.Progressbar(main, variable=self._progress_var, maximum=100)
        self._progress.pack(fill=tk.X, pady=10)
        
        self._status_var = tk.StringVar(value="Bereit zum Drucken")
        ttk.Label(main, textvariable=self._status_var).pack(anchor=tk.W)

        # 4. Buttons
        btns = ttk.Frame(main)
        btns.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        self._start_btn = ttk.Button(btns, text="SERIENDRUCK STARTEN", command=self._start_print)
        self._start_btn.pack(side=tk.RIGHT, padx=4)
        ttk.Button(btns, text="Abbrechen", command=self._win.destroy).pack(side=tk.RIGHT)

    def _on_printer_props(self) -> None:
        sel = self._printer_list.curselection()
        if not sel:
            return
        printer = self._printer_list.get(sel[0])
        show_printer_properties(printer, self._win.winfo_id())

    def _start_print(self) -> None:
        sel = self._printer_list.curselection()
        if not sel:
            messagebox.showwarning("Drucker", "Bitte wählen Sie einen Drucker aus.")
            return
        
        printer = self._printer_list.get(sel[0])
        fmt = self.app.tab_label.label_format
        objs = self.app.tab_label.label_objects
        
        if not fmt:
            messagebox.showerror("Fehler", "Kein Etikettenformat definiert.")
            return

        # Datensätze sammeln
        if self._selection_var.get() == "all":
            to_print = self._records
        else:
            to_print = [self._records[i] for i in self._selected_indices]
        
        if not to_print:
            messagebox.showinfo("Druck", "Keine Datensätze zum Drucken vorhanden.")
            return

        self._start_btn.configure(state="disabled")
        self._status_var.set(f"Rendern: 0 von {len(to_print)}")
        self._win.update_idletasks()

        images = []
        try:
            for i, rec in enumerate(to_print):
                self._status_var.set(f"Rende: {i+1} von {len(to_print)}")
                self._progress_var.set((i / len(to_print)) * 100)
                self._win.update() # UI aktuell halten
                
                # Hohe Qualität für Druck (300 DPI)
                img = render_label(fmt, objs, rec.values, dpi=300)
                images.append(img)
            
            self._status_var.set("Sende an Drucker ...")
            self._progress_var.set(95)
            self._win.update()
            
            print_pil_images(images, printer, title=f"Drinkport-Batch - {self._project.name}")
            
            self._progress_var.set(100)
            self._status_var.set("Druck abgeschlossen.")
            messagebox.showinfo("Erfolg", f"{len(images)} Etiketten wurden an den Drucker gesendet.")
            self._win.destroy()

        except Exception as exc:
            messagebox.showerror("Druckfehler", str(exc))
            self._start_btn.configure(state="normal")
            self._status_var.set("Fehler beim Drucken.")
