"""Datenmodelle (Dataclasses) für Barcode Forge."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Project:
    id: Optional[int]
    name: str
    description: str = ""

    def __str__(self) -> str:
        return self.name


@dataclass
class ProjectField:
    id: Optional[int]
    project_id: int
    name: str
    position: int = 0


@dataclass
class DataRecord:
    id: Optional[int]
    project_id: int
    selected: bool = True
    position: int = 0
    values: dict[str, str] = field(default_factory=dict)


@dataclass
class LabelFormat:
    id: Optional[int]
    project_id: int
    manufacturer: str = ""
    product_name: str = ""
    width_mm: float = 100.0
    height_mm: float = 50.0
    margin_top_mm: float = 2.0
    margin_bottom_mm: float = 2.0
    margin_left_mm: float = 2.0
    margin_right_mm: float = 2.0
    cols: int = 1
    rows: int = 1
    col_gap_mm: float = 0.0
    row_gap_mm: float = 0.0


@dataclass
class LabelObject:
    id: Optional[int]
    project_id: int
    type: str           # 'text' | 'barcode' | 'image' | 'rect' | 'ellipse' | 'line'
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    rotation: float = 0.0
    z_order: int = 0
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class SavedLabel:
    id: Optional[int]
    project_id: int
    record_id: Optional[int]
    name: str
    image_data: bytes
    image_format: str = "PNG"
    dpi: int = 300
    created_by: Optional[str] = None


# ─── Standard-Properties pro Objekt-Typ ──────────────────────────────────────

def default_text_properties() -> dict[str, Any]:
    return {
        "text"       : "Text",
        "font_family": "Arial",
        "font_size"  : 10,
        "bold"       : False,
        "italic"     : False,
        "underline"  : False,
        "color"      : "#000000",
        "bg_color"   : "",
        "align"      : "left",
        "valign"     : "top",
        "word_wrap"  : False,
    }


def default_barcode_properties() -> dict[str, Any]:
    from barcode_engine.zint_wrapper import BARCODE_CODE128
    return {
        "barcode_type"     : BARCODE_CODE128,
        "barcode_number"   : "",
        "show_hrt"         : True,
        "auto_complete"    : False,
        "optional_checkdigit": False,
        "fixed_module_width": 0,
        "ratio"            : 2.5,
        "fg_color"         : "000000",
        "bg_color"         : "FFFFFF",
    }


def default_image_properties() -> dict[str, Any]:
    return {
        "source_type"    : "embedded",
        "file_path"      : "",
        "image_data_b64" : None,
        "keep_aspect"    : True,
        "stretch"        : False,
    }


def default_rect_properties() -> dict[str, Any]:
    return {
        "fill_color"      : "",
        "border_color"    : "#000000",
        "border_width_mm" : 0.3,
        "corner_radius_mm": 0.0,
    }


def default_ellipse_properties() -> dict[str, Any]:
    return {
        "fill_color"     : "",
        "border_color"   : "#000000",
        "border_width_mm": 0.3,
    }


def default_line_properties() -> dict[str, Any]:
    return {
        "color"   : "#000000",
        "width_mm": 0.3,
    }


DEFAULT_PROPERTIES = {
    "text"   : default_text_properties,
    "barcode": default_barcode_properties,
    "image"  : default_image_properties,
    "rect"   : default_rect_properties,
    "ellipse": default_ellipse_properties,
    "line"   : default_line_properties,
}
