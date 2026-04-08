"""Einfache Dialoge für Projektverwaltung."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, simpledialog


def ask_project_name(
    parent: tk.Widget,
    title: str = "Projektname",
    initial: str = "",
) -> str | None:
    return simpledialog.askstring(
        title, "Projektname:", initialvalue=initial, parent=parent
    )
