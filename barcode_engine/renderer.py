"""
Label-Renderer: Setzt ein vollständiges Etikett aus LabelObjekten
und einem Datensatz zusammen und gibt ein PIL.Image zurück.
"""
from __future__ import annotations

import base64
import io
import re
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from models.types import LabelFormat, LabelObject
import app_config

# Windows-Systemfonts-Fallback
_FONT_DIRS = [
    Path("C:/Windows/Fonts"),
    Path("/usr/share/fonts"),
    Path("/usr/local/share/fonts"),
]

_FONT_CACHE: dict[tuple, ImageFont.FreeTypeFont] = {}


def _find_font(family: str, size_pt: int, bold: bool, italic: bool
               ) -> ImageFont.FreeTypeFont:
    key = (family.lower(), size_pt, bold, italic)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    candidates: list[str] = []
    suffix = ""
    if bold and italic:
        suffix = "bi"
    elif bold:
        suffix = "b"
    elif italic:
        suffix = "i"

    fam_lower = family.lower().replace(" ", "")
    for d in _FONT_DIRS:
        if not d.exists():
            continue
        for f in d.glob("*.ttf"):
            name = f.stem.lower()
            if fam_lower in name:
                if suffix and suffix in name:
                    candidates.insert(0, str(f))
                else:
                    candidates.append(str(f))

    font: ImageFont.FreeTypeFont
    if candidates:
        try:
            font = ImageFont.truetype(candidates[0], size_pt)
            _FONT_CACHE[key] = font
            return font
        except Exception:
            pass

    font = ImageFont.load_default()
    return font


def mm_to_px(mm: float, dpi: int) -> int:
    return int(round(mm / 25.4 * dpi))


def resolve_placeholders(template: str, record_values: dict[str, str]) -> str:
    """Ersetzt [~Feldname~] durch den Wert aus dem Datensatz (Case-Insensitive)."""
    # Erstelle eine Map mit kleingeschriebenen Keys für die Suche
    lookup = {k.lower(): v for k, v in record_values.items()}
    
    def _replace(m: re.Match) -> str:
        key = m.group(1).lower()
        return str(lookup.get(key, f"[~{m.group(1)}~]")) # Falls nicht gefunden, Platzhalter stehen lassen
    
    return re.sub(r"\[~([^~]+)~\]", _replace, template)


def render_label(
    fmt: LabelFormat,
    objects: list[LabelObject],
    record_values: dict[str, str],
    dpi: int | None = None,
) -> Image.Image:
    """
    Rendert ein Etikett und gibt ein PIL.Image (RGB) zurück.

    Parameters
    ----------
    fmt           : Etikettenformat (Abmessungen, Ränder)
    objects       : Etikettenobjekte (sortiert nach z_order)
    record_values : Feldname → Wert für Platzhalterersetzung
    dpi           : Ausgabeauflösung (Standard: config default_dpi)
    """
    if dpi is None:
        dpi = app_config.get_default_dpi()

    w_px = mm_to_px(fmt.width_mm, dpi)
    h_px = mm_to_px(fmt.height_mm, dpi)

    img = Image.new("RGB", (w_px, h_px), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    for obj in sorted(objects, key=lambda o: o.z_order):
        x_px = mm_to_px(obj.x_mm, dpi)
        y_px = mm_to_px(obj.y_mm, dpi)
        w_obj = mm_to_px(obj.width_mm, dpi)
        h_obj = mm_to_px(obj.height_mm, dpi)

        if obj.type == "text":
            _render_text(draw, img, obj, x_px, y_px, w_obj, h_obj, record_values, dpi)
        elif obj.type == "barcode":
            _render_barcode(img, obj, x_px, y_px, w_obj, h_obj, record_values, dpi)
        elif obj.type == "image":
            _render_image(img, obj, x_px, y_px, w_obj, h_obj, record_values)
        elif obj.type == "rect":
            _render_rect(draw, obj, x_px, y_px, w_obj, h_obj, dpi)
        elif obj.type == "ellipse":
            _render_ellipse(draw, obj, x_px, y_px, w_obj, h_obj, dpi)
        elif obj.type == "line":
            _render_line(draw, obj, x_px, y_px, w_obj, h_obj, dpi)

    return img


# ─── Einzelne Objekt-Renderer ─────────────────────────────────────────────────

def _render_text(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    obj: LabelObject,
    x: int, y: int, w: int, h: int,
    record_values: dict[str, str],
    dpi: int,
) -> None:
    p = obj.properties
    text = resolve_placeholders(p.get("text", ""), record_values)
    color = p.get("color", "#000000")
    bg_color = p.get("bg_color", "")
    align = p.get("align", "left")
    font_size_pt = int(p.get("font_size", 10))
    font_size_px = mm_to_px(font_size_pt * 0.3528, dpi)  # pt → mm → px
    bold = p.get("bold", False)
    italic = p.get("italic", False)
    family = p.get("font_family", "Arial")

    if bg_color:
        draw.rectangle([x, y, x + w, y + h], fill=bg_color)

    font = _find_font(family, max(font_size_px, 8), bold, italic)

    if align == "center":
        anchor = "mm"
        tx = x + w // 2
        ty = y + h // 2
    elif align == "right":
        anchor = "rm"
        tx = x + w
        ty = y + h // 2
    else:
        anchor = "lm"
        tx = x
        ty = y + h // 2

    draw.text((tx, ty), text, fill=color, font=font, anchor=anchor)


def _render_barcode(
    img: Image.Image,
    obj: LabelObject,
    x: int, y: int, w: int, h: int,
    record_values: dict[str, str],
    dpi: int,
) -> None:
    """Rendert einen Barcode ohne externe DLL (nutzt python-barcode und qrcode)."""
    p = obj.properties
    raw_data = p.get("barcode_number", "")
    data = resolve_placeholders(raw_data, record_values)
    
    if not data:
        _draw_placeholder(img, x, y, w, h, "Barcode\n(keine Daten)")
        return

    bc_type_id = int(p.get("barcode_type", 20))  # Default 20 = Code 128
    
    # Farben normalisieren (müssen für Pillow mit # beginnen)
    fg_color = p.get("fg_color", "#000000")
    if fg_color and not fg_color.startswith("#"):
        fg_color = f"#{fg_color}"
        
    bg_color = p.get("bg_color", "#FFFFFF")
    if bg_color and not bg_color.startswith("#"):
        bg_color = f"#{bg_color}"

    show_hrt = bool(p.get("show_hrt", True))

    try:
        bc_img: Optional[Image.Image] = None

        # ─── QR-Code (Zint 58) ───────────────────────────────────────────────
        # ─── Standard Barcodes (python-barcode) ──────────────────────────────
            text_height_needed = 0
        
            # ─── QR-Code (Zint 58) ───────────────────────────────────────────────
            if bc_type_id == 58:
                import qrcode
                qr = qrcode.QRCode(box_size=10, border=1)
                qr.add_data(data)
                qr.make(fit=True)
                bc_img = qr.make_image(fill_color=fg_color, back_color=bg_color).convert("RGB")
        
            # ─── Standard Barcodes (python-barcode) ──────────────────────────────
            else:
                import barcode
                from barcode.writer import ImageWriter
            
                mapping = {
                    20: 'code128',
                    8:  'code39',
                    13: 'ean13',
                    34: 'upca',
                    3:  'itf',
                }
            
                bc_name = mapping.get(bc_type_id, 'code128')
            
                # EAN/UPC brauchen exakt 12/13 Stellen, wir füllen ggf. mit Nullen
                if bc_name == 'ean13':
                    data = data.zfill(13)[:13]
                elif bc_name == 'upca':
                    data = data.zfill(12)[:12]
        
                bc_class = barcode.get_barcode_class(bc_name)
            
                # Wenn Klartext angezeigt werden soll, rendern wir OHNE Text im Bild
                # und fügen ihn separat darunter hinzu (verhindert Überlagerung)
                writer = ImageWriter()
                options = {
                    "write_text": False,  # WICHTIG: Text separat rendern!
                    "background": bg_color,
                    "foreground": fg_color,
                    "module_height": 15.0,
                    "module_width": 0.2,
                    "font_size": 10,
                    "text_distance": 1.0,
                }
            
                try:
                    bc_inst = bc_class(data, writer=writer)
                    bc_img = bc_inst.render(writer_options=options)
                
                    # Wenn Klartext gewünscht: separaten Space berechnen
                    if show_hrt:
                        # Grobe Schätzung: ~15px für Textzeile + Abstand
                        text_height_needed = max(20, int(h * 0.25))
                except Exception as e:
                    _draw_placeholder(img, x, y, w, h, f"Format-Fehler:\n{e}")
                    return
        
            if bc_img:
                # Höhe für Barcode ggf. reduzieren, wenn Klartext nötig
                bc_height = h - text_height_needed
            
                # Barcode skalieren
                bc_img = bc_img.resize((w, bc_height), Image.LANCZOS)
                img.paste(bc_img, (x, y))
            
                # Klartext separat unten rendern
                if show_hrt and text_height_needed > 0:
                    text_y = y + bc_height
                        # Text-Rendering
                        draw_inst = ImageDraw.Draw(img)
                        text_font_size = int(max(7, text_height_needed - 3))
                        text_font = _find_font("Courier New", text_font_size, False, False)
                        text_color = fg_color if fg_color.startswith("#") else f"#{fg_color}"
                        text_y = y + bc_height + (text_height_needed // 2)
                        draw_inst.text(
                            ((x + w // 2), text_y),
                            data,
                            fill=text_color,
                            font=text_font,
                            anchor="mm",
                        )

    except Exception as exc:
        _draw_placeholder(img, x, y, w, h, f"Render-Fehler:\n{exc}")


def _render_image(
    img: Image.Image,
    obj: LabelObject,
    x: int, y: int, w: int, h: int,
    record_values: dict[str, str],
) -> None:
    p = obj.properties
    source_type = p.get("source_type", "embedded")

    src_img: Optional[Image.Image] = None

    if source_type == "embedded":
        b64 = p.get("image_data_b64")
        if b64:
            try:
                data = base64.b64decode(b64)
                src_img = Image.open(io.BytesIO(data)).convert("RGBA")
            except Exception:
                pass
    elif source_type == "file_path":
        file_path = resolve_placeholders(p.get("file_path", ""), record_values)
        if file_path:
            try:
                src_img = Image.open(file_path).convert("RGBA")
            except Exception:
                pass

    # Fallback: eingebettete Grafik wenn Datei fehlt
    if src_img is None:
        b64 = p.get("image_data_b64")
        if b64:
            try:
                data = base64.b64decode(b64)
                src_img = Image.open(io.BytesIO(data)).convert("RGBA")
            except Exception:
                pass

    if src_img is None:
        _draw_placeholder(img, x, y, w, h, "Bild\nnicht gefunden")
        return

    if p.get("keep_aspect", True):
        src_img.thumbnail((w, h), Image.LANCZOS)
        paste_x = x + (w - src_img.width) // 2
        paste_y = y + (h - src_img.height) // 2
        img.paste(src_img, (paste_x, paste_y), mask=src_img.split()[3])
    else:
        src_img = src_img.resize((w, h), Image.LANCZOS)
        img.paste(src_img, (x, y), mask=src_img.split()[3])


def _render_rect(
    draw: ImageDraw.ImageDraw, obj: LabelObject,
    x: int, y: int, w: int, h: int, dpi: int,
) -> None:
    p = obj.properties
    fill   = p.get("fill_color") or None
    border = p.get("border_color", "#000000")
    bw     = mm_to_px(p.get("border_width_mm", 0.3), dpi)
    radius = mm_to_px(p.get("corner_radius_mm", 0.0), dpi)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius,
                           fill=fill, outline=border, width=max(bw, 1))


def _render_ellipse(
    draw: ImageDraw.ImageDraw, obj: LabelObject,
    x: int, y: int, w: int, h: int, dpi: int,
) -> None:
    p = obj.properties
    fill   = p.get("fill_color") or None
    border = p.get("border_color", "#000000")
    bw     = mm_to_px(p.get("border_width_mm", 0.3), dpi)
    draw.ellipse([x, y, x + w, y + h], fill=fill, outline=border, width=max(bw, 1))


def _render_line(
    draw: ImageDraw.ImageDraw, obj: LabelObject,
    x: int, y: int, w: int, h: int, dpi: int,
) -> None:
    p = obj.properties
    color = p.get("color", "#000000")
    bw    = mm_to_px(p.get("width_mm", 0.3), dpi)
    draw.line([x, y, x + w, y + h], fill=color, width=max(bw, 1))


def _draw_placeholder(
    img: Image.Image, x: int, y: int, w: int, h: int, text: str
) -> None:
    draw = ImageDraw.Draw(img)
    draw.rectangle([x, y, x + w, y + h], outline="#aaaaaa", width=1)
    draw.line([x, y, x + w, y + h], fill="#aaaaaa", width=1)
    draw.line([x + w, y, x, y + h], fill="#aaaaaa", width=1)
    font = ImageFont.load_default()
    draw.text((x + 2, y + 2), text, fill="#888888", font=font)


def label_to_bytes(
    fmt: LabelFormat,
    objects: list[LabelObject],
    record_values: dict[str, str],
    dpi: int | None = None,
    fmt_str: str = "PNG",
) -> bytes:
    """Rendert ein Etikett und gibt die komprimierten Bytes zurück."""
    pil_img = render_label(fmt, objects, record_values, dpi)
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt_str)
    return buf.getvalue()
