"""Alphanumerische Zahlenreihen-Generator (wie in Barcode Forge "Zahlenreihe generieren")."""
from __future__ import annotations

from typing import Iterator


def generate_series(
    start: str,
    end: str,
    step: int = 1,
    repeat: int = 1,
    pad_zeros: bool = False,
) -> list[str]:
    """
    Erzeugt eine Reihe von alphanumerischen Werten.

    Parameters
    ----------
    start     : Startwert (numerisch oder alphanumerisch)
    end       : Endwert (inklusive, gleicher Typ wie start)
    step      : Schrittgröße (positiv = aufsteigend, negativ = absteigend)
    repeat    : Wie oft jeder Wert wiederholt wird
    pad_zeros : Alle Werte auf die Länge des Startwertes mit führenden Nullen auffüllen
    """
    if _is_numeric(start) and _is_numeric(end):
        return _numeric_series(int(start), int(end), step, repeat, pad_zeros, len(start))
    else:
        return _alpha_series(start, end, step, repeat)


def _is_numeric(s: str) -> bool:
    return s.lstrip("0").isdigit() or s == "0"


def _numeric_series(
    start: int, end: int, step: int, repeat: int, pad: bool, pad_len: int
) -> list[str]:
    if step == 0:
        step = 1
    result: list[str] = []
    current = start
    while (step > 0 and current <= end) or (step < 0 and current >= end):
        value = str(current).zfill(pad_len) if pad else str(current)
        result.extend([value] * repeat)
        current += step
    return result


def _alpha_series(start: str, end: str, step: int, repeat: int) -> list[str]:
    """Vereinfachte alphabetische Reihe für einfache Buchstaben-Strings."""
    if len(start) != len(end):
        return []
    result: list[str] = []
    current = _str_to_int(start)
    target  = _str_to_int(end)
    length  = len(start)
    if step == 0:
        step = 1

    while (step > 0 and current <= target) or (step < 0 and current >= target):
        result.extend([_int_to_str(current, length)] * repeat)
        current += step
        if abs(current - target) > 100_000:
            break
    return result


_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _str_to_int(s: str) -> int:
    result = 0
    for ch in s.upper():
        idx = _CHARSET.find(ch)
        if idx < 0:
            return 0
        result = result * len(_CHARSET) + idx
    return result


def _int_to_str(n: int, length: int) -> str:
    base = len(_CHARSET)
    chars: list[str] = []
    for _ in range(length):
        chars.append(_CHARSET[n % base])
        n //= base
    return "".join(reversed(chars))
