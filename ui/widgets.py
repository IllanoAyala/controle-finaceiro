"""Shared widget helpers used across all UI modules."""
import tkinter as tk
from tkinter import ttk


def fmt(v):
    """Format float as Brazilian currency string."""
    return ("R$ " + "{:,.2f}".format(v)).replace(",", "X").replace(".", ",").replace("X", ".")


def entry_widget(parent, app, row=None, col=None, width=None):
    kw = dict(
        bg=app.ENTRY_BG, fg=app.FG, insertbackground=app.FG,
        font=("Segoe UI", 10), relief="flat", bd=4,
    )
    if width:
        kw["width"] = width
    e = tk.Entry(parent, **kw)
    if row is not None:
        e.grid(row=row, column=col, sticky="ew", pady=4, ipady=4)
    return e


def btn(parent, app, text, cmd, bg=None, fg=None):
    if bg is None:
        bg = app.FG
    if fg is None:
        fg = app.BG
    return tk.Button(
        parent, text=text, command=cmd,
        bg=bg, fg=fg, font=("Segoe UI", 10, "bold"),
        relief="flat", cursor="hand2", padx=12, pady=6,
        activebackground=bg, activeforeground=fg,
    )
