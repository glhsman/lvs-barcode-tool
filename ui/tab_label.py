"""Tab „Etikett" – WYSIWYG-Canvas-Editor für Etikettenobjekte."""
from __future__ import annotations

import copy
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Optional

import db.repository as repo
from models.types import (
    LabelFormat, LabelObject, Project,
    DEFAULT_PROPERTIES, default_barcode_properties,
    default_text_properties, default_rect_properties,
    default_ellipse_properties, default_image_properties,
    default_line_properties,
)

if TYPE_CHECKING:
    from ui.main_window import MainWindow

# Pixel pro Millimeter beim Standard-Zoom-Level 1.0
_BASE_PX_PER_MM = 3.0
_HANDLE_SIZE = 6
_HANDLE_COLOR = "#3399FF"
_HANDLE_HOVER_FILL = "#DDF0FF"
_HANDLE_HOVER_OUTLINE = "#67B7FF"
_GRID_MM = 5.0
_DEFAULT_EDITOR_ZOOM = 2.75
_RULER_SIZE = 26
_RULER_BG = "#252526"
_RULER_FG = "#969696"
_RULER_TICK = "#555555"


class LabelTab:
    def __init__(self, notebook: ttk.Notebook, app: "MainWindow"):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self._project: Project | None = None
        self._fmt: LabelFormat | None = None
        self._objects: list[LabelObject] = []
        self._selected: list[LabelObject] = []
        self._zoom = _DEFAULT_EDITOR_ZOOM
        self._tool = "select"
        self._clipboard: list[LabelObject] = []

        self._drag_start_canvas: tuple[float, float] | None = None
        self._drag_start_mm: tuple[float, float] | None = None
        self._drag_obj_origin: dict = {}
        self._drag_mode: str | None = None  # move | resize
        self._active_handle: str | None = None
        self._resize_origin: dict[str, float] = {}
        self._hover_handle_obj: LabelObject | None = None
        self._hover_handle_name: str | None = None
        self._creating_rect_id: int | None = None

        self._build_ui()

    # ─── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Linke Sidebar: Scrollbox für Werkzeuge
        sidebar_outer = ttk.Frame(self.frame)
        sidebar_outer.pack(side=tk.LEFT, fill=tk.Y)
        
        # Wir nutzen ein Canvas, um den tool_frame scrollbar zu machen
        sidebar_canvas = tk.Canvas(sidebar_outer, width=130, highlightthickness=0, bg="#1e1e1e")
        sidebar_scrollbar = ttk.Scrollbar(sidebar_outer, orient=tk.VERTICAL, command=sidebar_canvas.yview)
        
        # Der eigentliche Container für die Buttons
        tool_frame = ttk.Frame(sidebar_canvas, padding=4)
        
        # Fenstermanager im Canvas
        canvas_window = sidebar_canvas.create_window((0, 0), window=tool_frame, anchor=tk.NW)
        
        def _on_sidebar_configure(event):
            # Scrollregion aktualisieren, sobald sich der Frame ändert
            sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all"))
            # Breite des Canvas auf den Frame im Inneren fixieren
            sidebar_canvas.itemconfig(canvas_window, width=event.width)

        tool_frame.bind("<Configure>", _on_sidebar_configure)
        sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)
        
        sidebar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sidebar_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mausrad-Support für die Sidebar
        def _on_mousewheel(event):
            sidebar_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        sidebar_canvas.bind("<MouseWheel>", _on_mousewheel)

        tools = [
            ("↖ Auswahl",  "select"),
            ("T  Text",    "text"),
            ("▐  Barcode", "barcode"),
            ("▦  2D-Code", "barcode2d"),
            ("☐  Rechteck","rect"),
            ("○  Ellipse", "ellipse"),
            ("╱  Linie",   "line"),
            ("🖼  Grafik",  "image"),
        ]
        self._tool_buttons: dict[str, ttk.Button] = {}
        for label, tool in tools:
            b = ttk.Button(tool_frame, text=label, width=14,
                           command=lambda t=tool: self._set_tool(t))
            b.pack(pady=2, fill=tk.X)
            self._tool_buttons[tool] = b

        ttk.Separator(tool_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)

        ttk.Button(tool_frame, text="Etikett …", width=14,
                   command=self._edit_format).pack(pady=2, fill=tk.X)
        ttk.Button(tool_frame, text="Löschen",  width=14,
                   command=self._delete_selected).pack(pady=2, fill=tk.X)
        ttk.Button(tool_frame, text="Kopieren", width=14,
                   command=self._copy_selected).pack(pady=2, fill=tk.X)
        ttk.Button(tool_frame, text="Einfügen", width=14,
                   command=self._paste).pack(pady=2, fill=tk.X)

        ttk.Separator(tool_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)

        ttk.Label(tool_frame, text="Ausrichten:").pack()
        for lbl, cmd in [
            ("← Links",   lambda: self._align("left")),
            ("→ Rechts",  lambda: self._align("right")),
            ("↑ Oben",    lambda: self._align("top")),
            ("↓ Unten",   lambda: self._align("bottom")),
            ("↔ Mitte H", lambda: self._align("hcenter")),
            ("↕ Mitte V", lambda: self._align("vcenter")),
        ]:
            ttk.Button(tool_frame, text=lbl, width=14, command=cmd).pack(pady=1, fill=tk.X)

        ttk.Separator(tool_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)
        ttk.Label(tool_frame, text="Zoom:").pack()
        zoom_frame = ttk.Frame(tool_frame)
        zoom_frame.pack(fill=tk.X)
        ttk.Button(zoom_frame, text="−", width=3,
                   command=lambda: self._set_zoom(self._zoom - 0.25)).pack(side=tk.LEFT, expand=True)
        self._zoom_label = ttk.Label(zoom_frame, text=f"{int(self._zoom * 100)}%", width=6, anchor=tk.CENTER)
        self._zoom_label.pack(side=tk.LEFT, expand=True)
        ttk.Button(zoom_frame, text="+", width=3,
                   command=lambda: self._set_zoom(self._zoom + 0.25)).pack(side=tk.LEFT, expand=True)

        # Canvas mit Scrollbars und Linealen
        canvas_container = ttk.Frame(self.frame)
        canvas_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas_container.grid_rowconfigure(1, weight=1)
        canvas_container.grid_columnconfigure(1, weight=1)

        # Eck-Füllsel (oben links)
        self._ruler_corner = tk.Canvas(canvas_container, width=_RULER_SIZE, height=_RULER_SIZE,
                                       bg=_RULER_BG, highlightthickness=0)
        self._ruler_corner.grid(row=0, column=0, sticky="nsew")

        # Top Ruler
        self._ruler_top = tk.Canvas(canvas_container, height=_RULER_SIZE,
                                    bg=_RULER_BG, highlightthickness=0)
        self._ruler_top.grid(row=0, column=1, sticky="ew")

        # Left Ruler
        self._ruler_left = tk.Canvas(canvas_container, width=_RULER_SIZE,
                                     bg=_RULER_BG, highlightthickness=0)
        self._ruler_left.grid(row=1, column=0, sticky="ns")

        self._canvas = tk.Canvas(canvas_container, bg="#1e1e1e",
                                 highlightthickness=0, borderwidth=0,
                                 cursor="crosshair")
        self._canvas.grid(row=1, column=1, sticky="nsew")

        vsb = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL,
                            command=self._on_vsync)
        vsb.grid(row=1, column=2, sticky="ns")

        hsb = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL,
                            command=self._on_hsync)
        hsb.grid(row=2, column=1, sticky="ew")

        self._vsb = vsb
        self._hsb = hsb

        def _set_v_scroll(*args):
            vsb.set(*args)
            self._ruler_left.yview_moveto(args[0])

        def _set_h_scroll(*args):
            hsb.set(*args)
            self._ruler_top.xview_moveto(args[0])

        self._canvas.configure(yscrollcommand=_set_v_scroll, xscrollcommand=_set_h_scroll)

        # Canvas-Events
        self._canvas.bind("<ButtonPress-1>",   self._on_mouse_press)
        self._canvas.bind("<B1-Motion>",        self._on_mouse_drag)
        self._canvas.bind("<ButtonRelease-1>",  self._on_mouse_release)
        self._canvas.bind("<Control-MouseWheel>", self._on_ctrl_mousewheel)
        self._canvas.bind("<Control-Button-4>",  self._on_ctrl_mousewheel)  # Linux
        self._canvas.bind("<Control-Button-5>",  self._on_ctrl_mousewheel)  # Linux
        self._canvas.bind("<Double-Button-1>",  self._on_double_click)
        self._canvas.bind("<Button-3>",         self._on_right_click)
        self._canvas.bind("<Delete>",           lambda e: self._delete_selected())
        self._canvas.bind("<Control-c>",        lambda e: self._copy_selected())
        self._canvas.bind("<Control-v>",        lambda e: self._paste())
        self._canvas.bind("<Configure>",        lambda e: self._repaint())

        # Koordinatenanzeige unten
        self._coord_var = tk.StringVar(value="")
        ttk.Label(self.frame, textvariable=self._coord_var,
                  anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X, padx=6)
        self._canvas.bind("<Motion>", self._on_mouse_move)

        # Kontextmenü
        self._ctx = tk.Menu(self._canvas, tearoff=False)
        self._ctx.add_command(label="Eigenschaften …", command=self._edit_properties)
        self._ctx.add_command(label="Kopieren",        command=self._copy_selected)
        self._ctx.add_command(label="Löschen",         command=self._delete_selected)
        self._ctx.add_separator()
        self._ctx.add_command(label="Nach vorne",  command=lambda: self._change_z(1))
        self._ctx.add_command(label="Nach hinten", command=lambda: self._change_z(-1))

        self._set_tool("select")

    # ─── Projekt laden ────────────────────────────────────────────────────────

    def load_project(self, project: Project) -> None:
        self._project = project
        self._fmt     = repo.get_label_format(project.id)
        self._objects = repo.list_label_objects(project.id)
        self._selected = []
        self._repaint()

    # ─── Werkzeug ─────────────────────────────────────────────────────────────

    def _set_tool(self, tool: str) -> None:
        self._tool = tool
        for t, btn in self._tool_buttons.items():
            btn.state(["pressed" if t == tool else "!pressed"])
        cursor = "arrow" if tool == "select" else "crosshair"
        self._canvas.config(cursor=cursor)

    # ─── Zoom ─────────────────────────────────────────────────────────────────

    def _set_zoom(self, zoom: float) -> None:
        self._zoom = max(0.25, min(5.0, round(zoom * 4) / 4))
        self._zoom_label.config(text=f"{int(self._zoom * 100)}%")
        self._repaint()

    def _px_per_mm(self) -> float:
        return _BASE_PX_PER_MM * self._zoom

    def _to_px(self, mm: float) -> float:
        return mm * self._px_per_mm()

    def _to_mm(self, px: float) -> float:
        return px / self._px_per_mm()

    def _label_origin(self) -> tuple[float, float]:
        """Obere linke Ecke des weißen Etikettenbereichs in Canvas-Pixeln."""
        return 20.0, 20.0

    def _canvas_to_mm(self, cx: float, cy: float) -> tuple[float, float]:
        ox, oy = self._label_origin()
        return self._to_mm(cx - ox), self._to_mm(cy - oy)

    def _mm_to_canvas(self, x_mm: float, y_mm: float) -> tuple[float, float]:
        ox, oy = self._label_origin()
        return ox + self._to_px(x_mm), oy + self._to_px(y_mm)

    # ─── Repaint ──────────────────────────────────────────────────────────────

    def _repaint(self) -> None:
        if not self._fmt:
            self._canvas.delete("all")
            return
        self._canvas.delete("all")
        self._draw_label_background()
        self._draw_grid()
        for obj in sorted(self._objects, key=lambda o: o.z_order):
            self._draw_object(obj)
        self._update_scroll_region()
        self._draw_rulers()

    def _update_scroll_region(self) -> None:
        if not self._fmt:
            return
        ox, oy = self._label_origin()
        w = ox + self._to_px(self._fmt.width_mm) + 30
        h = oy + self._to_px(self._fmt.height_mm) + 30
        self._canvas.config(scrollregion=(0, 0, w, h))
        self._ruler_top.config(scrollregion=(0, 0, w, h))
        self._ruler_left.config(scrollregion=(0, 0, w, h))

    def _on_vsync(self, *args) -> None:
        self._canvas.yview(*args)
        self._ruler_left.yview(*args)

    def _on_hsync(self, *args) -> None:
        self._canvas.xview(*args)
        self._ruler_top.xview(*args)

    def _draw_rulers(self) -> None:
        if not self._fmt:
            return
        
        self._ruler_top.delete("all")
        self._ruler_left.delete("all")
        
        ox, oy = self._label_origin()
        w_mm = self._fmt.width_mm
        h_mm = self._fmt.height_mm
        ppm = self._px_per_mm()
        
        font = ("Arial", 7)
        
        # Horizontale Skala
        for i in range(int(w_mm) + 1):
            cx = ox + i * ppm
            if i % 10 == 0:
                self._ruler_top.create_line(cx, 10, cx, _RULER_SIZE, fill=_RULER_FG)
                self._ruler_top.create_text(cx + 2, 2, text=str(i), anchor=tk.NW, fill=_RULER_FG, font=font)
            elif i % 5 == 0:
                self._ruler_top.create_line(cx, 15, cx, _RULER_SIZE, fill=_RULER_FG)
            else:
                if self._zoom >= 1.5: # Ticks nur bei ausreichend Zoom
                    self._ruler_top.create_line(cx, 20, cx, _RULER_SIZE, fill=_RULER_TICK)

        # Vertikale Skala
        for i in range(int(h_mm) + 1):
            cy = oy + i * ppm
            if i % 10 == 0:
                self._ruler_left.create_line(10, cy, _RULER_SIZE, cy, fill=_RULER_FG)
                self._ruler_left.create_text(2, cy + 2, text=str(i), anchor=tk.NW, fill=_RULER_FG, font=font)
            elif i % 5 == 0:
                self._ruler_left.create_line(15, cy, _RULER_SIZE, cy, fill=_RULER_FG)
            else:
                if self._zoom >= 1.5:
                    self._ruler_left.create_line(20, cy, _RULER_SIZE, cy, fill=_RULER_TICK)

    def _draw_label_background(self) -> None:
        ox, oy = self._label_origin()
        w = self._to_px(self._fmt.width_mm)
        h = self._to_px(self._fmt.height_mm)
        # Schatten
        self._canvas.create_rectangle(ox + 3, oy + 3, ox + w + 3, oy + h + 3,
                                      fill="#888888", outline="")
        # Weißes Etikett
        self._canvas.create_rectangle(ox, oy, ox + w, oy + h,
                                      fill="white", outline="#333333", width=1)
        # Ränder-Linie (gestrichelt)
        ml = self._to_px(self._fmt.margin_left_mm)
        mr = self._to_px(self._fmt.margin_right_mm)
        mt = self._to_px(self._fmt.margin_top_mm)
        mb = self._to_px(self._fmt.margin_bottom_mm)
        self._canvas.create_rectangle(
            ox + ml, oy + mt, ox + w - mr, oy + h - mb,
            outline="#aaaaff", dash=(4, 4), width=1,
        )

    def _draw_grid(self) -> None:
        if not self._fmt or self._zoom < 0.5:
            return
        ox, oy = self._label_origin()
        ppm = self._px_per_mm()
        step_mm = _GRID_MM
        w_mm = self._fmt.width_mm
        h_mm = self._fmt.height_mm

        x = step_mm
        while x < w_mm:
            cx = ox + self._to_px(x)
            self._canvas.create_line(cx, oy, cx, oy + self._to_px(h_mm),
                                     fill="#333333", tags="grid")
            x += step_mm
        y = step_mm
        while y < h_mm:
            cy = oy + self._to_px(y)
            self._canvas.create_line(ox, cy, ox + self._to_px(w_mm), cy,
                                     fill="#333333", tags="grid")
            y += step_mm

    def _draw_object(self, obj: LabelObject) -> None:
        cx0, cy0 = self._mm_to_canvas(obj.x_mm, obj.y_mm)
        cx1 = cx0 + self._to_px(obj.width_mm)
        cy1 = cy0 + self._to_px(obj.height_mm)
        is_sel = obj in self._selected
        sel_color = _HANDLE_COLOR if is_sel else ""
        outline = _HANDLE_COLOR if is_sel else "#666666"
        tag = f"obj_{obj.id}"

        if obj.type == "text":
            p = obj.properties
            text = p.get("text", "Text")
            bg_color = p.get("bg_color") or "#ffffc0"
            self._canvas.create_rectangle(cx0, cy0, cx1, cy1,
                                          fill=bg_color, outline=outline,
                                          width=2 if is_sel else 1, tags=tag)
            
            # Font-Formatierung
            family = p.get("font_family", "Arial")
            size_pt = p.get("font_size", 10)
            # Umrechnung pt -> mm -> px im Editor
            # Wir nutzen einen negativen Wert, damit Tkinter die Groesse in Pixeln interpretiert (wichtig fuer WYSIWYG/Zoom)
            size_px = max(4, int(size_pt * 0.3528 * _BASE_PX_PER_MM * self._zoom))
            
            font_mods = []
            if p.get("bold"): font_mods.append("bold")
            if p.get("italic"): font_mods.append("italic")
            if p.get("underline"): font_mods.append("underline")
            
            font_spec: tuple
            if font_mods:
                font_spec = (family, -size_px, " ".join(font_mods))
            else:
                font_spec = (family, -size_px)

            # Ausrichtung
            align = p.get("align", "left")
            if align == "center":
                anchor = tk.CENTER
                tx = (cx0 + cx1) / 2
            elif align == "right":
                anchor = tk.E
                tx = cx1 - 2
            else:
                anchor = tk.W
                tx = cx0 + 2
            
            self._canvas.create_text(
                tx, (cy0 + cy1) / 2, text=text[:100],
                anchor=anchor, fill=p.get("color", "#000000"),
                font=font_spec, tags=tag,
            )
        elif obj.type in ("barcode", "barcode2d"):
            self._canvas.create_rectangle(cx0, cy0, cx1, cy1,
                                          fill="#f0f8ff", outline=outline,
                                          width=2 if is_sel else 1, tags=tag)
            bc_num = obj.properties.get("barcode_number", "")
            self._canvas.create_text(
                (cx0 + cx1) / 2, (cy0 + cy1) / 2,
                text=f"▌▐▌▌▐▌\n{bc_num[:20]}",
                anchor=tk.CENTER, fill="#333333",
                font=("Courier", -max(7, int(8 * self._zoom))), tags=tag,
            )
        elif obj.type == "image":
            self._canvas.create_rectangle(cx0, cy0, cx1, cy1,
                                          fill="#f5f5f5", outline=outline,
                                          width=2 if is_sel else 1, tags=tag)
            self._canvas.create_line(cx0, cy0, cx1, cy1, fill="#bbbbbb", tags=tag)
            self._canvas.create_line(cx0, cy1, cx1, cy0, fill="#bbbbbb", tags=tag)
            self._canvas.create_text(
                (cx0 + cx1) / 2, (cy0 + cy1) / 2, text="🖼",
                anchor=tk.CENTER, tags=tag,
            )
        elif obj.type == "rect":
            p = obj.properties
            fill = p.get("fill_color") or ""
            self._canvas.create_rectangle(cx0, cy0, cx1, cy1,
                                          fill=fill, outline=outline,
                                          width=2 if is_sel else 1, tags=tag)
        elif obj.type == "ellipse":
            p = obj.properties
            fill = p.get("fill_color") or ""
            self._canvas.create_oval(cx0, cy0, cx1, cy1,
                                     fill=fill, outline=outline,
                                     width=2 if is_sel else 1, tags=tag)
        elif obj.type == "line":
            self._canvas.create_line(cx0, cy0, cx1, cy1,
                                     fill=outline, width=2 if is_sel else 1, tags=tag)

        # Selektions-Handles
        if is_sel:
            self._draw_handles(obj, cx0, cy0, cx1, cy1, tag)

    def _draw_handles(self, obj: LabelObject, x0: float, y0: float, x1: float, y1: float,
                      parent_tag: str) -> None:
        hs = _HANDLE_SIZE
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        for hx, hy, hname in [
            (x0, y0, "tl"), (xm, y0, "tm"), (x1, y0, "tr"),
            (x0, ym, "ml"),                  (x1, ym, "mr"),
            (x0, y1, "bl"), (xm, y1, "bm"), (x1, y1, "br"),
        ]:
            htag = f"{parent_tag}_h_{hname}"
            is_hovered = obj is self._hover_handle_obj and hname == self._hover_handle_name
            self._canvas.create_rectangle(
                hx - hs/2, hy - hs/2, hx + hs/2, hy + hs/2,
                fill=_HANDLE_HOVER_FILL if is_hovered else "white",
                outline=_HANDLE_HOVER_OUTLINE if is_hovered else _HANDLE_COLOR,
                width=2,
                tags=(htag, "handle"),
            )

    # ─── Mouse-Events ──────────────────────────────────────────────────────────

    def _on_mouse_move(self, event) -> None:
        cx = self._canvas.canvasx(event.x)
        cy = self._canvas.canvasy(event.y)
        x_mm, y_mm = self._canvas_to_mm(cx, cy)
        self._coord_var.set(f"X: {x_mm:.1f} mm   Y: {y_mm:.1f} mm")
        self._update_canvas_cursor(cx, cy)
        self._update_ruler_markers(cx, cy)

    def _update_ruler_markers(self, cx: float, cy: float) -> None:
        self._ruler_top.delete("marker")
        self._ruler_left.delete("marker")
        self._ruler_top.create_line(cx, 0, cx, _RULER_SIZE, fill="white", tags="marker", width=1)
        self._ruler_left.create_line(0, cy, _RULER_SIZE, cy, fill="white", tags="marker", width=1)

    def _update_canvas_cursor(self, cx: float, cy: float) -> None:
        """Setzt kontextabhaengig den Mauszeiger im Canvas."""
        if self._tool != "select":
            self._set_hover_handle(None, None)
            self._canvas.config(cursor="crosshair")
            return

        # Beim aktiven Resize Cursor am Handle festhalten.
        if self._drag_mode == "resize" and self._active_handle:
            obj = self._selected[0] if self._selected else None
            self._set_hover_handle(obj, self._active_handle)
            self._canvas.config(cursor=self._cursor_for_handle(self._active_handle))
            return

        handle_hit = self._hit_handle(cx, cy)
        if handle_hit:
            obj, handle = handle_hit
            self._set_hover_handle(obj, handle)
            self._canvas.config(cursor=self._cursor_for_handle(handle))
            return

        self._set_hover_handle(None, None)
        hit = self._hit_test(cx, cy)
        self._canvas.config(cursor="fleur" if hit else "arrow")

    def _set_hover_handle(self, obj: LabelObject | None, handle_name: str | None) -> None:
        """Aktualisiert den aktuell hervorgehobenen Handle und repainted nur bei Aenderung."""
        if self._hover_handle_obj is obj and self._hover_handle_name == handle_name:
            return
        self._hover_handle_obj = obj
        self._hover_handle_name = handle_name
        self._repaint()

    @staticmethod
    def _cursor_for_handle(handle: str) -> str:
        """Ordnet Handles passenden Resize-Cursoren zu."""
        return {
            "tl": "top_left_corner",
            "br": "bottom_right_corner",
            "tr": "top_right_corner",
            "bl": "bottom_left_corner",
            "ml": "sb_h_double_arrow",
            "mr": "sb_h_double_arrow",
            "tm": "sb_v_double_arrow",
            "bm": "sb_v_double_arrow",
        }.get(handle, "arrow")

    def _on_ctrl_mousewheel(self, event) -> str:
        """Zoomt mit Strg + Mausrad in den Etikett-Canvas."""
        direction = 0
        if hasattr(event, "delta") and event.delta:
            direction = 1 if event.delta > 0 else -1
        elif getattr(event, "num", None) == 4:
            direction = 1
        elif getattr(event, "num", None) == 5:
            direction = -1

        if direction != 0:
            self._set_zoom(self._zoom + (0.25 * direction))
            return "break"
        return ""

    def _on_mouse_press(self, event) -> None:
        self._canvas.focus_set()
        cx = float(self._canvas.canvasx(event.x))
        cy = float(self._canvas.canvasy(event.y))
        x_mm, y_mm = self._canvas_to_mm(cx, cy)

        if self._tool == "select":
            handle_hit = self._hit_handle(cx, cy)
            if handle_hit:
                obj, handle = handle_hit
                if obj not in self._selected:
                    self._selected = [obj]
                self._drag_mode = "resize"
                self._active_handle = handle
                self._drag_start_canvas = (cx, cy)
                self._resize_origin = {
                    "x_mm": obj.x_mm,
                    "y_mm": obj.y_mm,
                    "width_mm": obj.width_mm,
                    "height_mm": obj.height_mm,
                }
                self._repaint()
                self._update_canvas_cursor(cx, cy)
                return

            hit = self._hit_test(cx, cy)
            if hit:
                if event.state & 0x0001 or event.state & 0x0004:  # Shift oder Strg (Windows/Linux)
                    if hit in self._selected:
                        self._selected.remove(hit)
                    else:
                        self._selected.append(hit)
                else:
                    if hit not in self._selected:
                        self._selected = [hit]
                self._drag_mode = "move"
                self._drag_start_canvas = (cx, cy)
                self._drag_obj_origin = {
                    o.id: (o.x_mm, o.y_mm) for o in self._selected
                }
            else:
                self._selected = []
                self._drag_mode = None
                self._drag_start_canvas = (cx, cy)
            self._repaint()
            self._update_canvas_cursor(cx, cy)
        else:
            # Erstellen eines neuen Objekts
            self._drag_start_canvas = (cx, cy)
            self._creating_rect_id = self._canvas.create_rectangle(
                cx, cy, cx, cy, outline=_HANDLE_COLOR, dash=(4, 4), width=2,
            )

    def _on_mouse_drag(self, event) -> None:
        cx = float(self._canvas.canvasx(event.x))
        cy = float(self._canvas.canvasy(event.y))
        
        self._update_ruler_markers(cx, cy)

        if self._tool == "select" and self._drag_start_canvas:
            if self._drag_mode == "resize" and self._selected and self._active_handle and self._resize_origin:
                obj = self._selected[0]
                dx_mm = self._to_mm(cx - self._drag_start_canvas[0])
                dy_mm = self._to_mm(cy - self._drag_start_canvas[1])
                self._apply_resize(obj, self._active_handle, dx_mm, dy_mm)
                self._repaint()
                self._update_canvas_cursor(cx, cy)
            elif self._drag_mode == "move" and self._selected and self._drag_obj_origin:
                dx_mm = self._to_mm(cx - self._drag_start_canvas[0])
                dy_mm = self._to_mm(cy - self._drag_start_canvas[1])
                for obj in self._selected:
                    ox, oy = self._drag_obj_origin[obj.id]
                    obj.x_mm = max(0.0, round(ox + dx_mm, 1))
                    obj.y_mm = max(0.0, round(oy + dy_mm, 1))
                self._repaint()
                self._update_canvas_cursor(cx, cy)
        elif self._tool != "select" and self._creating_rect_id:
            if self._tool == "barcode2d":
                cx, cy = self._square_drag_endpoint(
                    self._drag_start_canvas[0], self._drag_start_canvas[1], cx, cy
                )
            self._canvas.coords(
                self._creating_rect_id,
                self._drag_start_canvas[0], self._drag_start_canvas[1], cx, cy,
            )

    def _on_mouse_release(self, event) -> None:
        cx = float(self._canvas.canvasx(event.x))
        cy = float(self._canvas.canvasy(event.y))

        if self._tool == "select":
            # Speichern verschobener oder skalierter Objekte
            for obj in self._selected:
                if obj.id is not None:
                    repo.update_label_object(obj)
            if self._drag_mode in ("move", "resize"):
                self.app.mark_changed()
            self._drag_start_canvas = None
            self._drag_mode = None
            self._active_handle = None
            self._resize_origin = {}
            self._drag_obj_origin = {}
            self._update_canvas_cursor(cx, cy)

        elif self._tool != "select" and self._drag_start_canvas:
            sx, sy = self._drag_start_canvas
            if self._tool == "barcode2d":
                cx, cy = self._square_drag_endpoint(sx, sy, cx, cy)
            x0_mm, y0_mm = self._canvas_to_mm(min(sx, cx), min(sy, cy))
            x1_mm, y1_mm = self._canvas_to_mm(max(sx, cx), max(sy, cy))
            w_mm = max(5.0, x1_mm - x0_mm)
            h_mm = max(3.0, y1_mm - y0_mm)

            if self._tool == "barcode2d":
                side_mm = max(5.0, max(w_mm, h_mm))
                w_mm = side_mm
                h_mm = side_mm

            if self._creating_rect_id:
                self._canvas.delete(self._creating_rect_id)
                self._creating_rect_id = None

            tool = "barcode" if self._tool == "barcode2d" else self._tool
            props_fn = DEFAULT_PROPERTIES.get(tool)
            props = props_fn() if props_fn else {}

            # 2D-Code: Default auf QR-Code
            if self._tool == "barcode2d":
                from barcode_engine.zint_wrapper import BARCODE_QRCODE
                props["barcode_type"] = BARCODE_QRCODE

            new_obj = LabelObject(
                id=None, project_id=self._project.id,
                type=tool,
                x_mm=x0_mm, y_mm=y0_mm, width_mm=w_mm, height_mm=h_mm,
                z_order=len(self._objects),
                properties=props,
            )
            saved = repo.add_label_object(new_obj)
            self._objects.append(saved)
            self._selected = [saved]
            self._drag_start_canvas = None
            self._set_tool("select")
            self.app.mark_changed()
            self._repaint()
            # Direkt Eigenschaften öffnen
            self._edit_properties()

    @staticmethod
    def _square_drag_endpoint(sx: float, sy: float, cx: float, cy: float) -> tuple[float, float]:
        """Zwingt das Aufziehen auf ein Quadrat (fuer 2D-Barcodes)."""
        dx = cx - sx
        dy = cy - sy
        side = max(abs(dx), abs(dy))
        ex = sx + (side if dx >= 0 else -side)
        ey = sy + (side if dy >= 0 else -side)
        return ex, ey

    def _on_double_click(self, _event) -> None:
        self._edit_properties()

    def _on_right_click(self, event) -> None:
        cx = float(self._canvas.canvasx(event.x))
        cy = float(self._canvas.canvasy(event.y))
        hit = self._hit_test(cx, cy)
        if hit and hit not in self._selected:
            self._selected = [hit]
            self._repaint()
        if self._selected:
            self._ctx.tk_popup(event.x_root, event.y_root)

    # ─── Hit-Test ─────────────────────────────────────────────────────────────

    def _hit_test(self, cx: float, cy: float) -> Optional[LabelObject]:
        """Gibt das oberste Objekt an Position (cx, cy) zurück."""
        for obj in reversed(sorted(self._objects, key=lambda o: o.z_order)):
            x0, y0 = self._mm_to_canvas(obj.x_mm, obj.y_mm)
            x1 = x0 + self._to_px(obj.width_mm)
            y1 = y0 + self._to_px(obj.height_mm)
            if x0 - 3 <= cx <= x1 + 3 and y0 - 3 <= cy <= y1 + 3:
                return obj
        return None

    def _hit_handle(self, cx: float, cy: float) -> tuple[LabelObject, str] | None:
        """Prueft, ob ein Selektions-Handle getroffen wurde."""
        if len(self._selected) != 1:
            return None
        obj = self._selected[0]
        x0, y0 = self._mm_to_canvas(obj.x_mm, obj.y_mm)
        x1 = x0 + self._to_px(obj.width_mm)
        y1 = y0 + self._to_px(obj.height_mm)
        hs = _HANDLE_SIZE
        tol = max(3.0, hs / 2 + 1)
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        for hx, hy, name in [
            (x0, y0, "tl"), (xm, y0, "tm"), (x1, y0, "tr"),
            (x0, ym, "ml"),                  (x1, ym, "mr"),
            (x0, y1, "bl"), (xm, y1, "bm"), (x1, y1, "br"),
        ]:
            if abs(cx - hx) <= tol and abs(cy - hy) <= tol:
                return obj, name
        return None

    def _apply_resize(self, obj: LabelObject, handle: str, dx_mm: float, dy_mm: float) -> None:
        """Skaliert ein Objekt anhand des angefassten Handle-Namens."""
        min_w = 1.0
        min_h = 1.0
        ox = self._resize_origin["x_mm"]
        oy = self._resize_origin["y_mm"]
        ow = self._resize_origin["width_mm"]
        oh = self._resize_origin["height_mm"]

        x = ox
        y = oy
        w = ow
        h = oh

        if "l" in handle:
            x = ox + dx_mm
            w = ow - dx_mm
        if "r" in handle:
            w = ow + dx_mm
        if "t" in handle:
            y = oy + dy_mm
            h = oh - dy_mm
        if "b" in handle:
            h = oh + dy_mm

        if w < min_w:
            if "l" in handle:
                x = ox + (ow - min_w)
            w = min_w
        if h < min_h:
            if "t" in handle:
                y = oy + (oh - min_h)
            h = min_h

        if self._is_square_2d_barcode(obj):
            min_side = 5.0
            side = max(min_side, max(w, h))

            left = ox
            top = oy
            right = ox + ow
            bottom = oy + oh

            if handle == "tl":
                x = right - side
                y = bottom - side
            elif handle == "tm":
                x = left
                y = bottom - side
            elif handle == "tr":
                x = left
                y = bottom - side
            elif handle == "ml":
                x = right - side
                y = top
            elif handle == "mr":
                x = left
                y = top
            elif handle == "bl":
                x = right - side
                y = top
            elif handle == "bm":
                x = left
                y = top
            elif handle == "br":
                x = left
                y = top

            w = side
            h = side

        obj.x_mm = max(0.0, round(x, 1))
        obj.y_mm = max(0.0, round(y, 1))
        obj.width_mm = round(w, 1)
        obj.height_mm = round(h, 1)

    @staticmethod
    def _is_square_2d_barcode(obj: LabelObject) -> bool:
        """Erkennt 2D-Barcodes, die beim Resizen quadratisch bleiben sollen."""
        if obj.type != "barcode":
            return False
        from barcode_engine.zint_wrapper import (
            BARCODE_QRCODE,
            BARCODE_DATAMATRIX,
            BARCODE_AZTEC,
            BARCODE_MAXICODE,
        )
        btype = int(obj.properties.get("barcode_type", 0))
        return btype in {BARCODE_QRCODE, BARCODE_DATAMATRIX, BARCODE_AZTEC, BARCODE_MAXICODE}

    # ─── Aktionen ─────────────────────────────────────────────────────────────

    def _delete_selected(self) -> None:
        if not self._selected:
            return
        for obj in self._selected:
            if obj.id is not None:
                repo.delete_label_object(obj.id, self._project.id)
            if obj in self._objects:
                self._objects.remove(obj)
        self._selected = []
        self.app.mark_changed()
        self._repaint()

    def _copy_selected(self) -> None:
        self._clipboard = [copy.deepcopy(o) for o in self._selected]

    def _paste(self) -> None:
        if not self._clipboard or not self._project:
            return
        new_objs = []
        for orig in self._clipboard:
            o = copy.deepcopy(orig)
            o.id = None
            o.project_id = self._project.id
            o.x_mm += 3.0
            o.y_mm += 3.0
            o.z_order = len(self._objects)
            saved = repo.add_label_object(o)
            self._objects.append(saved)
            new_objs.append(saved)
        self._selected = new_objs
        self.app.mark_changed()
        self._repaint()

    def _edit_properties(self) -> None:
        if not self._selected:
            return
        obj = self._selected[0]
        from ui.dialogs.object_properties import ObjectPropertiesDialog
        dlg = ObjectPropertiesDialog(self.app.root, obj,
                                     self.app.tab_data.fields)
        if dlg.changed:
            repo.update_label_object(obj)
            self.app.mark_changed()
            self._repaint()

    def _edit_format(self) -> None:
        if not self._project or not self._fmt:
            return
        from ui.dialogs.label_format import LabelFormatDialog
        dlg = LabelFormatDialog(self.app.root, self._fmt)
        if dlg.changed:
            repo.save_label_format(self._fmt)
            self.app.mark_changed()
            self._repaint()

    def _align(self, how: str) -> None:
        if not self._selected or not self._fmt:
            return
        
        multi = len(self._selected) > 1
        
        # Extremwerte der Selektion ermitteln (für relatives Ausrichten)
        min_x = min(o.x_mm for o in self._selected)
        max_x = max(o.x_mm + o.width_mm for o in self._selected)
        min_y = min(o.y_mm for o in self._selected)
        max_y = max(o.y_mm + o.height_mm for o in self._selected)
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2

        for obj in self._selected:
            if how == "left":
                obj.x_mm = min_x if multi else 0.0
            elif how == "right":
                obj.x_mm = (max_x - obj.width_mm) if multi else (self._fmt.width_mm - obj.width_mm)
            elif how == "top":
                obj.y_mm = min_y if multi else 0.0
            elif how == "bottom":
                obj.y_mm = (max_y - obj.height_mm) if multi else (self._fmt.height_mm - obj.height_mm)
            elif how == "hcenter":
                obj.x_mm = (mid_x - obj.width_mm / 2) if multi else (self._fmt.width_mm - obj.width_mm) / 2
            elif how == "vcenter":
                obj.y_mm = (mid_y - obj.height_mm / 2) if multi else (self._fmt.height_mm - obj.height_mm) / 2
            
            if obj.id is not None:
                repo.update_label_object(obj)
        
        self.app.mark_changed()
        self._repaint()

    def _change_z(self, delta: int) -> None:
        for obj in self._selected:
            obj.z_order = max(0, obj.z_order + delta)
            if obj.id is not None:
                repo.update_label_object(obj)
        self._repaint()

    # ─── Accessor ─────────────────────────────────────────────────────────────

    @property
    def label_format(self) -> Optional[LabelFormat]:
        return self._fmt

    @property
    def label_objects(self) -> list[LabelObject]:
        return self._objects
