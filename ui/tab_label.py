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
_GRID_MM = 5.0


class LabelTab:
    def __init__(self, notebook: ttk.Notebook, app: "MainWindow"):
        self.app = app
        self.frame = ttk.Frame(notebook)
        self._project: Project | None = None
        self._fmt: LabelFormat | None = None
        self._objects: list[LabelObject] = []
        self._selected: list[LabelObject] = []
        self._zoom = 1.0
        self._tool = "select"
        self._clipboard: list[LabelObject] = []

        self._drag_start_canvas: tuple[float, float] | None = None
        self._drag_start_mm: tuple[float, float] | None = None
        self._drag_obj_origin: dict = {}
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
        sidebar_canvas.bind_all("<MouseWheel>", _on_mousewheel)

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

        ttk.Button(tool_frame, text="Format …", width=14,
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
        self._zoom_label = ttk.Label(zoom_frame, text="100%", width=6, anchor=tk.CENTER)
        self._zoom_label.pack(side=tk.LEFT, expand=True)
        ttk.Button(zoom_frame, text="+", width=3,
                   command=lambda: self._set_zoom(self._zoom + 0.25)).pack(side=tk.LEFT, expand=True)

        # Canvas mit Scrollbars
        canvas_container = ttk.Frame(self.frame)
        canvas_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(canvas_container, bg="#1e1e1e",
                                 highlightthickness=0, borderwidth=0,
                                 cursor="crosshair")
        vsb = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL,
                            command=self._canvas.yview)
        hsb = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL,
                            command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._canvas.pack(fill=tk.BOTH, expand=True)

        # Canvas-Events
        self._canvas.bind("<ButtonPress-1>",   self._on_mouse_press)
        self._canvas.bind("<B1-Motion>",        self._on_mouse_drag)
        self._canvas.bind("<ButtonRelease-1>",  self._on_mouse_release)
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

    def _update_scroll_region(self) -> None:
        if not self._fmt:
            return
        ox, oy = self._label_origin()
        w = ox + self._to_px(self._fmt.width_mm) + 30
        h = oy + self._to_px(self._fmt.height_mm) + 30
        self._canvas.config(scrollregion=(0, 0, w, h))

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
            self._canvas.create_rectangle(cx0, cy0, cx1, cy1,
                                          fill="#ffffc0", outline=outline,
                                          width=2 if is_sel else 1, tags=tag)
            self._canvas.create_text(
                cx0 + 4, (cy0 + cy1) / 2, text=text[:40],
                anchor=tk.W, fill=p.get("color", "#000000"),
                font=("Arial", max(8, int(9 * self._zoom))), tags=tag,
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
                font=("Courier", max(7, int(8 * self._zoom))), tags=tag,
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
            self._draw_handles(cx0, cy0, cx1, cy1, tag)

    def _draw_handles(self, x0: float, y0: float, x1: float, y1: float,
                      parent_tag: str) -> None:
        hs = _HANDLE_SIZE
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        for hx, hy, hname in [
            (x0, y0, "tl"), (xm, y0, "tm"), (x1, y0, "tr"),
            (x0, ym, "ml"),                  (x1, ym, "mr"),
            (x0, y1, "bl"), (xm, y1, "bm"), (x1, y1, "br"),
        ]:
            htag = f"{parent_tag}_h_{hname}"
            self._canvas.create_rectangle(
                hx - hs/2, hy - hs/2, hx + hs/2, hy + hs/2,
                fill="white", outline=_HANDLE_COLOR, width=2,
                tags=(htag, "handle"),
            )

    # ─── Mouse-Events ──────────────────────────────────────────────────────────

    def _on_mouse_move(self, event) -> None:
        x_mm, y_mm = self._canvas_to_mm(event.x, event.y)
        self._coord_var.set(f"X: {x_mm:.1f} mm   Y: {y_mm:.1f} mm")

    def _on_mouse_press(self, event) -> None:
        self._canvas.focus_set()
        cx, cy = float(event.x), float(event.y)
        x_mm, y_mm = self._canvas_to_mm(cx, cy)

        if self._tool == "select":
            hit = self._hit_test(cx, cy)
            if hit:
                if event.state & 0x0001:  # Shift
                    if hit in self._selected:
                        self._selected.remove(hit)
                    else:
                        self._selected.append(hit)
                else:
                    if hit not in self._selected:
                        self._selected = [hit]
                self._drag_start_canvas = (cx, cy)
                self._drag_obj_origin = {
                    o.id: (o.x_mm, o.y_mm) for o in self._selected
                }
            else:
                self._selected = []
                self._drag_start_canvas = (cx, cy)
            self._repaint()
        else:
            # Erstellen eines neuen Objekts
            self._drag_start_canvas = (cx, cy)
            self._creating_rect_id = self._canvas.create_rectangle(
                cx, cy, cx, cy, outline=_HANDLE_COLOR, dash=(4, 4), width=2,
            )

    def _on_mouse_drag(self, event) -> None:
        cx, cy = float(event.x), float(event.y)

        if self._tool == "select" and self._drag_start_canvas:
            if self._selected and self._drag_obj_origin:
                dx_mm = self._to_mm(cx - self._drag_start_canvas[0])
                dy_mm = self._to_mm(cy - self._drag_start_canvas[1])
                for obj in self._selected:
                    ox, oy = self._drag_obj_origin[obj.id]
                    obj.x_mm = max(0.0, round(ox + dx_mm, 1))
                    obj.y_mm = max(0.0, round(oy + dy_mm, 1))
                self._repaint()
        elif self._tool != "select" and self._creating_rect_id:
            self._canvas.coords(
                self._creating_rect_id,
                self._drag_start_canvas[0], self._drag_start_canvas[1], cx, cy,
            )

    def _on_mouse_release(self, event) -> None:
        cx, cy = float(event.x), float(event.y)

        if self._tool == "select":
            # Speichern verschobener Objekte
            for obj in self._selected:
                if obj.id is not None:
                    repo.update_label_object(obj)
            self.app.mark_changed()
            self._drag_start_canvas = None

        elif self._tool != "select" and self._drag_start_canvas:
            sx, sy = self._drag_start_canvas
            x0_mm, y0_mm = self._canvas_to_mm(min(sx, cx), min(sy, cy))
            x1_mm, y1_mm = self._canvas_to_mm(max(sx, cx), max(sy, cy))
            w_mm = max(5.0, x1_mm - x0_mm)
            h_mm = max(3.0, y1_mm - y0_mm)

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

    def _on_double_click(self, _event) -> None:
        self._edit_properties()

    def _on_right_click(self, event) -> None:
        cx, cy = float(event.x), float(event.y)
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
        ref = self._selected[0]
        for obj in self._selected:
            if how == "left":
                obj.x_mm = ref.x_mm if len(self._selected) > 1 else 0.0
            elif how == "right":
                obj.x_mm = ref.x_mm + ref.width_mm - obj.width_mm if len(self._selected) > 1 \
                           else self._fmt.width_mm - obj.width_mm
            elif how == "top":
                obj.y_mm = ref.y_mm if len(self._selected) > 1 else 0.0
            elif how == "bottom":
                obj.y_mm = ref.y_mm + ref.height_mm - obj.height_mm if len(self._selected) > 1 \
                           else self._fmt.height_mm - obj.height_mm
            elif how == "hcenter":
                obj.x_mm = (self._fmt.width_mm - obj.width_mm) / 2
            elif how == "vcenter":
                obj.y_mm = (self._fmt.height_mm - obj.height_mm) / 2
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
