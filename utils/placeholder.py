"""Platzhalter-Auflösung: [~Feldname~] → Wert."""
from __future__ import annotations

import re


_PATTERN = re.compile(r"\[~([^~\[\]]+)~\]")


def resolve(template: str, values: dict[str, str]) -> str:
    """Ersetzt alle [~Feldname~]-Vorkommen im Template durch values[Feldname]."""
    return _PATTERN.sub(lambda m: values.get(m.group(1), ""), template)


def extract_field_names(template: str) -> list[str]:
    """Gibt alle in einem Template verwendeten Feldnamen zurück."""
    return _PATTERN.findall(template)


def validate_all_fields_exist(template: str, known_fields: list[str]) -> list[str]:
    """Gibt Feldnamen zurück, die im Template, aber nicht in known_fields stehen."""
    return [f for f in extract_field_names(template) if f not in known_fields]
