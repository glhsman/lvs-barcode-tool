"""
Objekt-Eigenschaften-Dialog.
Zeigt je nach Objekttyp einen anderen Satz von Eingabefeldern an.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog
from typing import TYPE_CHECKING

from models.types import LabelObject, ProjectField
from barcode_engine.zint_wrapper import BARCODE_NAMES

if TYPE_CHECKING:
    pass


class ObjectPropertiesDialog:
    def __init__(
        self,
        parent: tk.Widget,
        obj: LabelObject,
        fields: list[ProjectField],
    ):
        self._obj = obj
        self._fields = fields
        self.changed = False

        self._win = tk.Toplevel(parent)
        self._win.title(f"Eigenschaften – {obj.type.capitalize()}")
        self._win.grab_set()
        # Mehr Platz für modernere Designs
        self._win.geometry("640x680")
        self._win.minsize(580, 600)
        self._win.resizable(True, True)

        self._notebook = ttk.Notebook(self._win)
        self._notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._build_geometry_tab()
        self._build_type_tab()

        btn = ttk.Frame(self._win, padding=(10, 4))
        btn.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(btn, text="OK",        command=self._ok).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn, text="Abbrechen", command=self._win.destroy).pack(side=tk.RIGHT)

        self._win.wait_window()

    # ─── Geometrie-Tab ────────────────────────────────────────────────────────

    def _build_geometry_tab(self) -> None:
        tab = ttk.Frame(self._notebook, padding=10)
        self._notebook.add(tab, text=" Position / Größe ")

        self._geo_vars: dict[str, tk.DoubleVar] = {}
        fields = [
            ("X (mm):",       "x_mm",       0.0,  2000.0),
            ("Y (mm):",       "y_mm",       0.0,  2000.0),
            ("Breite (mm):",  "width_mm",   0.1,  2000.0),
            ("Höhe (mm):",    "height_mm",  0.1,  2000.0),
            ("Rotation °:",   "rotation",   0.0,  360.0),
            ("Z-Reihenfolge:","z_order",    None, None),
        ]
        for r, (lbl, attr, lo, hi) in enumerate(fields):
            ttk.Label(tab, text=lbl).grid(row=r, column=0, sticky=tk.W, pady=4, padx=4)
            if attr == "z_order":
                var = tk.IntVar(value=getattr(self._obj, attr))
                ttk.Spinbox(tab, from_=0, to=999, textvariable=var, width=10).grid(
                    row=r, column=1, sticky=tk.W, padx=4)
                self._geo_vars["z_order"] = var
            else:
                var = tk.DoubleVar(value=getattr(self._obj, attr))
                ttk.Spinbox(tab, from_=lo, to=hi, increment=0.5,
                            textvariable=var, width=10, format="%.2f").grid(
                    row=r, column=1, sticky=tk.W, padx=4)
                self._geo_vars[attr] = var

    # ─── Typ-spezifischer Tab ─────────────────────────────────────────────────

    def _build_type_tab(self) -> None:
        if self._obj.type == "text":
            self._build_text_tab()
        elif self._obj.type in ("barcode",):
            self._build_barcode_tab()
        elif self._obj.type == "image":
            self._build_image_tab()
        elif self._obj.type in ("rect", "ellipse"):
            self._build_shape_tab()
        elif self._obj.type == "line":
            self._build_line_tab()

    def _build_text_tab(self) -> None:
        tab = ttk.Frame(self._notebook, padding=10)
        self._notebook.add(tab, text=" Text ")
        p = self._obj.properties

        # Textinhalt
        ttk.Label(tab, text="Text-Inhalt:").grid(row=0, column=0, sticky=tk.NW, pady=4)
        self._text_var = tk.StringVar(value=p.get("text", ""))
        text_frame = ttk.Frame(tab)
        text_frame.grid(row=0, column=1, sticky=tk.EW, columnspan=2, pady=4)
        txt = tk.Text(text_frame, height=3, width=38, wrap=tk.WORD)
        txt.insert("1.0", self._text_var.get())
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._text_widget = txt

        # Datenfeld einfügen
        if self._fields:
            ttk.Label(tab, text="Datenfeld:").grid(row=1, column=0, sticky=tk.W, pady=4)
            field_var = tk.StringVar()
            combo = ttk.Combobox(tab, textvariable=field_var,
                                 values=[f.name for f in self._fields], width=20)
            combo.grid(row=1, column=1, sticky=tk.W, padx=4)
            ttk.Button(tab, text="Einfügen",
                       command=lambda: self._insert_field(txt, field_var.get())
                       ).grid(row=1, column=2, padx=4)

        # Schrift
        ttk.Label(tab, text="Schriftart:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self._font_var = tk.StringVar(value=p.get("font_family", "Arial"))
        ttk.Entry(tab, textvariable=self._font_var, width=22).grid(
            row=2, column=1, sticky=tk.W, padx=4)

        ttk.Label(tab, text="Größe (pt):").grid(row=3, column=0, sticky=tk.W)
        self._fontsize_var = tk.IntVar(value=int(p.get("font_size", 10)))
        ttk.Spinbox(tab, from_=4, to=200, textvariable=self._fontsize_var, width=8).grid(
            row=3, column=1, sticky=tk.W, padx=4)

        # Farbe
        ttk.Label(tab, text="Textfarbe:").grid(row=4, column=0, sticky=tk.W, pady=4)
        self._color_var = tk.StringVar(value=p.get("color", "#000000"))
        color_btn = tk.Button(tab, textvariable=self._color_var, width=14,
                              command=lambda: self._pick_color(self._color_var, color_btn))
        color_btn.grid(row=4, column=1, sticky=tk.W, padx=4)
        self._apply_color_btn(color_btn, self._color_var.get())

        # Hintergrundfarbe
        ttk.Label(tab, text="Hintergrund:").grid(row=5, column=0, sticky=tk.W)
        self._bg_var = tk.StringVar(value=p.get("bg_color", ""))
        bg_btn = tk.Button(tab, textvariable=self._bg_var, width=14,
                           command=lambda: self._pick_color(self._bg_var, bg_btn))
        bg_btn.grid(row=5, column=1, sticky=tk.W, padx=4)

        # Fett / Kursiv
        self._bold_var   = tk.BooleanVar(value=p.get("bold", False))
        self._italic_var = tk.BooleanVar(value=p.get("italic", False))
        style_f = ttk.Frame(tab)
        style_f.grid(row=6, column=0, columnspan=3, sticky=tk.W, pady=4)
        ttk.Checkbutton(style_f, text="Fett",     variable=self._bold_var).pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(style_f, text="Kursiv",   variable=self._italic_var).pack(side=tk.LEFT)

        # Ausrichtung
        ttk.Label(tab, text="Ausrichtung:").grid(row=7, column=0, sticky=tk.W)
        self._align_var = tk.StringVar(value=p.get("align", "left"))
        align_f = ttk.Frame(tab)
        align_f.grid(row=7, column=1, sticky=tk.W)
        for txt2, val in [("Links", "left"), ("Mitte", "center"), ("Rechts", "right")]:
            ttk.Radiobutton(align_f, text=txt2, variable=self._align_var,
                            value=val).pack(side=tk.LEFT, padx=4)
        tab.columnconfigure(1, weight=1)

    def _build_barcode_tab(self) -> None:
        tab = ttk.Frame(self._notebook, padding=10)
        self._notebook.add(tab, text=" Barcode ")
        p = self._obj.properties

        # Barcode-Typ
        ttk.Label(tab, text="Barcode-Typ:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self._bc_type_var = tk.StringVar()
        bc_combo = ttk.Combobox(tab, textvariable=self._bc_type_var,
                                 values=list(BARCODE_NAMES.keys()), state="readonly", width=28)
        bc_combo.grid(row=0, column=1, columnspan=2, sticky=tk.W, padx=4)
        # Aktuellen Typ finden
        cur_type_id = int(p.get("barcode_type", 20))
        self._bc_type_map = BARCODE_NAMES
        rev = {v: k for k, v in BARCODE_NAMES.items()}
        bc_combo.set(rev.get(cur_type_id, "Code 128"))

        # Barcode-Nummer
        ttk.Label(tab, text="Barcode-Nummer:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self._bc_num_var = tk.StringVar(value=p.get("barcode_number", ""))
        ttk.Entry(tab, textvariable=self._bc_num_var, width=32).grid(
            row=1, column=1, sticky=tk.EW, padx=4)
        if self._fields:
            field_var2 = tk.StringVar()
            combo2 = ttk.Combobox(tab, textvariable=field_var2,
                                  values=[f.name for f in self._fields], width=16)
            combo2.grid(row=2, column=0, sticky=tk.W, padx=4, pady=2)
            ttk.Button(tab, text="Datenfeld einfügen",
                       command=lambda: self._bc_num_var.set(
                           self._bc_num_var.get() + f"[~{field_var2.get()}~]")
                       ).grid(row=2, column=1, sticky=tk.W, padx=4)

        # Optionen
        self._show_hrt_var  = tk.BooleanVar(value=bool(p.get("show_hrt", True)))
        self._autocomplete_var = tk.BooleanVar(value=bool(p.get("auto_complete", False)))
        ttk.Checkbutton(tab, text="Klartextzeile anzeigen",
                        variable=self._show_hrt_var).grid(
            row=3, column=0, columnspan=3, sticky=tk.W, pady=2)
        ttk.Checkbutton(tab, text="Barcode-Nummer ggf. vervollständigen",
                        variable=self._autocomplete_var).grid(
            row=4, column=0, columnspan=3, sticky=tk.W, pady=2)

        # Farben
        ttk.Label(tab, text="Strichfarbe:").grid(row=5, column=0, sticky=tk.W, pady=4)
        self._bc_fg_var = tk.StringVar(value=p.get("fg_color", "000000"))
        ttk.Entry(tab, textvariable=self._bc_fg_var, width=12).grid(
            row=5, column=1, sticky=tk.W, padx=4)

        ttk.Label(tab, text="Hintergrund:").grid(row=6, column=0, sticky=tk.W)
        self._bc_bg_var = tk.StringVar(value=p.get("bg_color", "FFFFFF"))
        ttk.Entry(tab, textvariable=self._bc_bg_var, width=12).grid(
            row=6, column=1, sticky=tk.W, padx=4)
        tab.columnconfigure(1, weight=1)

    def _build_image_tab(self) -> None:
        tab = ttk.Frame(self._notebook, padding=10)
        self._notebook.add(tab, text=" Grafik ")
        p = self._obj.properties

        self._img_source_var = tk.StringVar(
            value=p.get("source_type", "embedded"))

        ttk.Radiobutton(tab, text="Grafik einbetten",
                        variable=self._img_source_var, value="embedded").grid(
            row=0, column=0, sticky=tk.W, pady=4)
        ttk.Radiobutton(tab, text="Dateipfad zur Druckzeit laden",
                        variable=self._img_source_var, value="file_path").grid(
            row=1, column=0, sticky=tk.W)

        ttk.Label(tab, text="Dateipfad:").grid(row=2, column=0, sticky=tk.W, pady=8)
        self._img_path_var = tk.StringVar(value=p.get("file_path", ""))
        path_f = ttk.Frame(tab)
        path_f.grid(row=2, column=1, sticky=tk.EW)
        ttk.Entry(path_f, textvariable=self._img_path_var, width=28).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_f, text="…", width=3,
                   command=self._browse_image).pack(side=tk.LEFT, padx=2)

        if self._fields:
            field_var = tk.StringVar()
            combo = ttk.Combobox(tab, textvariable=field_var,
                                 values=[f.name for f in self._fields], width=18)
            combo.grid(row=3, column=0, sticky=tk.W, padx=4, pady=4)
            ttk.Button(tab, text="Datenfeld einfügen",
                       command=lambda: self._img_path_var.set(
                           self._img_path_var.get() + f"[~{field_var.get()}~]")
                       ).grid(row=3, column=1, sticky=tk.W, padx=4)

        self._img_aspect_var = tk.BooleanVar(value=bool(p.get("keep_aspect", True)))
        ttk.Checkbutton(tab, text="Seitenverhältnis beibehalten",
                        variable=self._img_aspect_var).grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=4)
        tab.columnconfigure(1, weight=1)

    def _build_shape_tab(self) -> None:
        tab = ttk.Frame(self._notebook, padding=10)
        self._notebook.add(tab, text=" Form ")
        p = self._obj.properties

        ttk.Label(tab, text="Füllfarbe:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self._fill_var = tk.StringVar(value=p.get("fill_color", ""))
        fill_btn = tk.Button(tab, textvariable=self._fill_var, width=14,
                             command=lambda: self._pick_color(self._fill_var, fill_btn))
        fill_btn.grid(row=0, column=1, sticky=tk.W, padx=4)

        ttk.Label(tab, text="Randfarbe:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self._border_color_var = tk.StringVar(value=p.get("border_color", "#000000"))
        border_btn = tk.Button(tab, textvariable=self._border_color_var, width=14,
                               command=lambda: self._pick_color(self._border_color_var, border_btn))
        border_btn.grid(row=1, column=1, sticky=tk.W, padx=4)

        ttk.Label(tab, text="Randbreite (mm):").grid(row=2, column=0, sticky=tk.W, pady=4)
        self._border_w_var = tk.DoubleVar(value=float(p.get("border_width_mm", 0.3)))
        ttk.Spinbox(tab, from_=0.0, to=10.0, increment=0.1,
                    textvariable=self._border_w_var, width=8, format="%.2f").grid(
            row=2, column=1, sticky=tk.W, padx=4)

        if self._obj.type == "rect":
            ttk.Label(tab, text="Eckenradius (mm):").grid(row=3, column=0, sticky=tk.W, pady=4)
            self._radius_var = tk.DoubleVar(value=float(p.get("corner_radius_mm", 0.0)))
            ttk.Spinbox(tab, from_=0.0, to=50.0, increment=0.5,
                        textvariable=self._radius_var, width=8, format="%.2f").grid(
                row=3, column=1, sticky=tk.W, padx=4)

    def _build_line_tab(self) -> None:
        tab = ttk.Frame(self._notebook, padding=10)
        self._notebook.add(tab, text=" Linie ")
        p = self._obj.properties

        ttk.Label(tab, text="Linienfarbe:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self._line_color_var = tk.StringVar(value=p.get("color", "#000000"))
        btn = tk.Button(tab, textvariable=self._line_color_var, width=14,
                        command=lambda: self._pick_color(self._line_color_var, btn))
        btn.grid(row=0, column=1, sticky=tk.W, padx=4)

        ttk.Label(tab, text="Breite (mm):").grid(row=1, column=0, sticky=tk.W, pady=4)
        self._line_w_var = tk.DoubleVar(value=float(p.get("width_mm", 0.3)))
        ttk.Spinbox(tab, from_=0.1, to=10.0, increment=0.1,
                    textvariable=self._line_w_var, width=8, format="%.2f").grid(
            row=1, column=1, sticky=tk.W, padx=4)

    # ─── OK / Hilfsmethoden ───────────────────────────────────────────────────

    def _ok(self) -> None:
        # Geometrie
        for attr, var in self._geo_vars.items():
            setattr(self._obj, attr, var.get())

        # Typ-spezifische Eigenschaften
        p = self._obj.properties
        t = self._obj.type

        if t == "text":
            p["text"]        = self._text_widget.get("1.0", tk.END).rstrip("\n")
            p["font_family"] = self._font_var.get()
            p["font_size"]   = self._fontsize_var.get()
            p["color"]       = self._color_var.get()
            p["bg_color"]    = self._bg_var.get()
            p["bold"]        = self._bold_var.get()
            p["italic"]      = self._italic_var.get()
            p["align"]       = self._align_var.get()

        elif t == "barcode":
            name = self._bc_type_var.get()
            p["barcode_type"]    = self._bc_type_map.get(name, 20)
            p["barcode_number"]  = self._bc_num_var.get()
            p["show_hrt"]        = self._show_hrt_var.get()
            p["auto_complete"]   = self._autocomplete_var.get()
            p["fg_color"]        = self._bc_fg_var.get()
            p["bg_color"]        = self._bc_bg_var.get()

        elif t == "image":
            p["source_type"]  = self._img_source_var.get()
            p["file_path"]    = self._img_path_var.get()
            p["keep_aspect"]  = self._img_aspect_var.get()

        elif t in ("rect", "ellipse"):
            p["fill_color"]      = self._fill_var.get()
            p["border_color"]    = self._border_color_var.get()
            p["border_width_mm"] = self._border_w_var.get()
            if t == "rect":
                p["corner_radius_mm"] = self._radius_var.get()

        elif t == "line":
            p["color"]    = self._line_color_var.get()
            p["width_mm"] = self._line_w_var.get()

        self.changed = True
        self._win.destroy()

    def _pick_color(self, var: tk.StringVar, btn: tk.Button) -> None:
        init = var.get() or "#ffffff"
        color = colorchooser.askcolor(color=init, parent=self._win)[1]
        if color:
            var.set(color)
            self._apply_color_btn(btn, color)

    @staticmethod
    def _apply_color_btn(btn: tk.Button, color: str) -> None:
        try:
            btn.config(bg=color, fg="white" if _is_dark(color) else "black")
        except tk.TclError:
            pass

    @staticmethod
    def _insert_field(text_widget: tk.Text, field_name: str) -> None:
        if field_name:
            text_widget.insert(tk.INSERT, f"[~{field_name}~]")

    def _browse_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Grafikdatei wählen",
            filetypes=[("Bilder", "*.png *.jpg *.jpeg *.bmp *.gif"),
                       ("Alle",   "*.*")],
        )
        if path:
            self._img_path_var.set(path)


def _is_dark(hex_color: str) -> bool:
    h = hex_color.lstrip("#")
    if len(h) < 6:
        return False
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r * 299 + g * 587 + b * 114) / 1000 < 128
