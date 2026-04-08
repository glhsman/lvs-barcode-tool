"""
ctypes-Wrapper fuer die Zint Barcode Library (Version 2.12.x).

Zint-Projektseite: https://zint.org.uk
Die struct-Definition entspricht zint.h aus dem 2.12-Branch
auf Windows x64 (unsigned long = 4 Bytes, Pointer = 8 Bytes).
"""
from __future__ import annotations

import ctypes
import ctypes.util
from pathlib import Path
from typing import Optional

# ─── Barcode-Typ-Konstanten aus zint.h ────────────────────────────────────────
BARCODE_CODE11        = 1
BARCODE_C25INTER      = 3    # ITF / Interleaved 2 of 5
BARCODE_CODE39        = 8
BARCODE_EXCODE39      = 9    # Code 39 Extended (Full ASCII)
BARCODE_EANX          = 13   # EAN-8 / EAN-13 / ISBN – Typ automatisch aus Datenlänge
BARCODE_GS1_128       = 16   # GS1-128 (früher EAN-128)
BARCODE_CODABAR       = 18
BARCODE_CODE128       = 20   # Code 128 (automatischer Subset)
BARCODE_CODE93        = 25   # Code 93
BARCODE_UPCA          = 34   # UPC-A
BARCODE_UPCE          = 37   # UPC-E
BARCODE_MSI_PLESSEY   = 47
BARCODE_PDF417        = 55
BARCODE_MAXICODE      = 57
BARCODE_QRCODE        = 58
BARCODE_DATAMATRIX    = 71
BARCODE_AZTEC         = 92

BARCODE_NAMES: dict[str, int] = {
    "Code 128"                : BARCODE_CODE128,
    "Code 39"                 : BARCODE_CODE39,
    "Code 39 Extended"        : BARCODE_EXCODE39,
    "Code 93"                 : BARCODE_CODE93,
    "Code 11"                 : BARCODE_CODE11,
    "Codabar"                 : BARCODE_CODABAR,
    "GTIN-13 / EAN-13"        : BARCODE_EANX,
    "GTIN-8 / EAN-8"          : BARCODE_EANX,
    "UPC-A"                   : BARCODE_UPCA,
    "UPC-E"                   : BARCODE_UPCE,
    "GS1-128 (EAN-128)"       : BARCODE_GS1_128,
    "2 of 5 Interleaved (ITF)": BARCODE_C25INTER,
    "MSI Plessey"             : BARCODE_MSI_PLESSEY,
    "PDF417"                  : BARCODE_PDF417,
    "MaxiCode"                : BARCODE_MAXICODE,
    "QR-Code"                 : BARCODE_QRCODE,
    "Data Matrix"             : BARCODE_DATAMATRIX,
    "Aztec Code"              : BARCODE_AZTEC,
}

# ─── zint_symbol Struktur (zint 2.12.x, Windows x64) ─────────────────────────
# ctypes fügt automatisch Alignment-Padding ein; daher kein manuelles Padding nötig.
_ZINT_MAX_COLOUR_LEN = 10
_ZINT_MAX_HRT_LEN    = 144
_ZINT_MAX_ROWS       = 200
_ZINT_MAX_DATA_LEN   = 144


class ZintSymbol(ctypes.Structure):
    _fields_ = [
        ("symbology",          ctypes.c_int),
        ("height",             ctypes.c_float),
        ("whitespace_width",   ctypes.c_int),
        ("whitespace_height",  ctypes.c_int),
        ("border_width",       ctypes.c_int),
        ("output_options",     ctypes.c_int),
        ("fgcolour",           ctypes.c_char * _ZINT_MAX_COLOUR_LEN),
        ("bgcolour",           ctypes.c_char * _ZINT_MAX_COLOUR_LEN),
        ("fgcolor",            ctypes.c_char * _ZINT_MAX_COLOUR_LEN),   # Alias
        ("bgcolor",            ctypes.c_char * _ZINT_MAX_COLOUR_LEN),   # Alias
        ("outfile",            ctypes.c_char * 256),
        ("scale",              ctypes.c_float),
        ("option_1",           ctypes.c_int),
        ("option_2",           ctypes.c_int),
        ("eci",                ctypes.c_int),
        ("primary",            ctypes.c_char * 128),
        ("option_3",           ctypes.c_int),
        ("show_hrt",           ctypes.c_int),
        ("input_mode",         ctypes.c_int),
        ("debug",              ctypes.c_int),
        ("text",               ctypes.c_ubyte * _ZINT_MAX_HRT_LEN),
        ("rows",               ctypes.c_int),
        ("width",              ctypes.c_int),
        ("encoded_data",       (ctypes.c_ubyte * _ZINT_MAX_DATA_LEN) * _ZINT_MAX_ROWS),
        ("row_height",         ctypes.c_float * _ZINT_MAX_ROWS),
        ("errtxt",             ctypes.c_char * 100),
        # ctypes fügt hier 4 Bytes Padding ein (Pointer-Alignment auf 8 Bytes)
        ("bitmap",             ctypes.c_void_p),       # char* → RGBA-Bitmap
        ("bitmap_width",       ctypes.c_int),
        ("bitmap_height",      ctypes.c_int),
        ("alphamap",           ctypes.c_void_p),       # deprecated
        ("bitmap_byte_length", ctypes.c_ulong),        # 4 Bytes auf Windows!
        ("dot_size",           ctypes.c_float),
        ("text_gap",           ctypes.c_float),
        ("guard_descent",      ctypes.c_float),
        ("vector",             ctypes.c_void_p),
        ("warn_level",         ctypes.c_int),
        ("cap_flag",           ctypes.c_int),
        ("structapp_count",    ctypes.c_int),
        ("structapp_index",    ctypes.c_int),
        ("structapp_id",       ctypes.c_char * 32),
        ("dpmm",               ctypes.c_int),
        ("set_x",              ctypes.c_float),
        ("set_y",              ctypes.c_float),
        ("set_rows",           ctypes.c_int),
        ("set_cols",           ctypes.c_int),
        ("set_data",           (ctypes.c_ubyte * _ZINT_MAX_DATA_LEN) * _ZINT_MAX_ROWS),
    ]


# ─── DLL laden ────────────────────────────────────────────────────────────────

_lib: ctypes.CDLL | None = None
_load_error: str = ""


def _load_library() -> ctypes.CDLL:
    global _lib, _load_error
    if _lib is not None:
        return _lib
    lib_name = ctypes.util.find_library("zint") or "zint"
    try:
        lib = ctypes.CDLL(lib_name)
    except OSError as exc:
        _load_error = str(exc)
        raise RuntimeError(
            f"Zint-Bibliothek konnte nicht geladen werden:\n{exc}\n"
            f"Bibliothek: {lib_name}"
        ) from exc

    # Funktionssignaturen registrieren
    lib.ZBarcode_Version.restype  = ctypes.c_int
    lib.ZBarcode_Version.argtypes = []

    lib.ZBarcode_Create.restype  = ctypes.POINTER(ZintSymbol)
    lib.ZBarcode_Create.argtypes = []

    lib.ZBarcode_Delete.restype  = None
    lib.ZBarcode_Delete.argtypes = [ctypes.POINTER(ZintSymbol)]

    lib.ZBarcode_Encode_and_Buffer.restype  = ctypes.c_int
    lib.ZBarcode_Encode_and_Buffer.argtypes = [
        ctypes.POINTER(ZintSymbol),
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int,
    ]

    _lib = lib
    return lib


def get_zint_version() -> Optional[int]:
    """Gibt Zint-Version als Integer zurück (z.B. 21200 für 2.12.0)."""
    try:
        return _load_library().ZBarcode_Version()
    except RuntimeError:
        return None


def is_available() -> bool:
    return get_zint_version() is not None


# ─── Öffentliche API ──────────────────────────────────────────────────────────

class BarcodeResult:
    """Ergebnis eines Barcode-Render-Aufrufs."""

    def __init__(self, rgba_bytes: bytes, width: int, height: int):
        self.rgba_bytes = rgba_bytes
        self.width  = width
        self.height = height

    def to_pil_image(self):
        """Gibt ein PIL.Image (RGBA) zurück."""
        from PIL import Image
        return Image.frombytes("RGBA", (self.width, self.height), self.rgba_bytes)


def render_barcode(
    data: str,
    barcode_type: int = BARCODE_CODE128,
    scale: float = 1.0,
    show_hrt: bool = True,
    height: float = 50.0,
    fg_color: str = "000000",
    bg_color: str = "FFFFFF",
    option_1: int = -1,
    option_2: int = 0,
    option_3: int = 0,
) -> BarcodeResult:
    """
    Rendert einen Barcode via Zint und gibt ein BarcodeResult zurueck.

    Parameters
    ----------
    data         : Nutzdaten (Klartext)
    barcode_type : Zint-Barcode-Typkonstante
    scale        : Skalierungsfaktor (1.0 = 1 Pixel pro Modul)
    show_hrt     : Klartextzeile anzeigen
    height       : Höhe in X-Dimensionen
    fg_color     : Vordergrundfarbe als RRGGBB-Hex-String
    bg_color     : Hintergrundfarbe als RRGGBB-Hex-String
    option_1/2/3 : Barcode-spezifische Optionen
    """
    lib = _load_library()
    sym_ptr = lib.ZBarcode_Create()
    if not sym_ptr:
        raise RuntimeError("ZBarcode_Create() lieferte NULL.")

    try:
        sym = sym_ptr.contents
        sym.symbology   = barcode_type
        sym.scale       = scale
        sym.show_hrt    = int(show_hrt)
        sym.height      = height
        sym.fgcolour    = fg_color.encode("ascii")[:9]
        sym.bgcolour    = bg_color.encode("ascii")[:9]
        if option_1 >= 0:
            sym.option_1 = option_1
        sym.option_2    = option_2
        sym.option_3    = option_3

        data_bytes = data.encode("utf-8")
        ret = lib.ZBarcode_Encode_and_Buffer(sym_ptr, data_bytes, len(data_bytes), 0)

        if ret >= 5:  # ZINT_ERROR (>= 5 = Fehler, 2/3/4 = Warnings)
            err = sym.errtxt.decode("utf-8", errors="replace")
            raise ValueError(f"Zint-Fehler ({ret}): {err}")

        if not sym.bitmap or sym.bitmap_width <= 0 or sym.bitmap_height <= 0:
            raise RuntimeError("Zint lieferte kein Bitmap.")

        byte_len = sym.bitmap_width * sym.bitmap_height * 4  # RGBA
        raw = ctypes.string_at(sym.bitmap, byte_len)
        return BarcodeResult(raw, sym.bitmap_width, sym.bitmap_height)

    finally:
        lib.ZBarcode_Delete(sym_ptr)
