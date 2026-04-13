import sys
import os
import configparser
from pathlib import Path

# Wenn wir als PyInstaller-EXE laufen, liegt die config.ini NEBEN der .exe Datei
# Wenn wir als Skript laufen, liegt sie im Projekt-Ordner
if getattr(sys, 'frozen', False):
    _BASE_DIR = Path(sys.executable).parent
else:
    _BASE_DIR = Path(__file__).parent

_CFG_FILE = _BASE_DIR / "config.ini"

_cfg = configparser.ConfigParser()
if _CFG_FILE.exists():
    try:
        # Erst UTF-8 versuchen
        _cfg.read(_CFG_FILE, encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback auf Windows-ANSI (fuer Umlaute etc.)
        _cfg.read(_CFG_FILE, encoding="cp1252")


def get_db_config() -> dict:
    db = _cfg["database"] if "database" in _cfg else {}
    return {
        "host"       : db.get("host", "localhost").strip(' "\''),
        "port"       : int(db.get("port", "3306")),
        "user"       : db.get("user", "root").strip(' "\''),
        "password"   : db.get("password", "").strip(' "\''),
        "database"   : db.get("database", "drinkport_barcode").strip(' "\''),
        "charset"    : "utf8mb4",
        "use_unicode": True,
    }


def get_default_dpi() -> int:
    if _cfg.has_section("app"):
        return int(_cfg.get("app", "default_dpi", fallback="203").strip(' "\''))
    return 203


def get_username() -> str:
    name = ""
    if _cfg.has_section("app"):
        name = _cfg.get("app", "username", fallback="").strip(' "\'')

    return name or os.getenv("USERNAME") or os.getenv("USER") or "unknown"


def get_templates_file() -> Path:
    return _BASE_DIR / "label_templates.json"


def get_last_csv_path() -> str:
    if _cfg.has_section("history"):
        return _cfg.get("history", "last_csv", fallback="").strip(' "\'')
    return ""


def set_last_csv_path(path: str) -> None:
    if not _cfg.has_section("history"):
        _cfg.add_section("history")
    _cfg.set("history", "last_csv", path)
    _save_cfg()


def _save_cfg() -> None:
    try:
        with open(_CFG_FILE, "w", encoding="utf-8") as f:
            _cfg.write(f)
    except Exception as e:
        print(f"Fehler beim Speichern der Konfiguration: {e}")
