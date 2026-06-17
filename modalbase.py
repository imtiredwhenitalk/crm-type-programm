import tkinter as tk
from tkinter import ttk
from uihelper import mk_label, mk_entry, mk_btn, mk_sep
from theme import C

class Modal:
    """A clean, centered modal dialog with a consistent look."""
    def __init__(self, parent, title, width=480, height=None):
        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.configure(bg=C['white'])
        self.win.resizable(False, False)
        self.win.grab_set()
        self.win.transient(parent)

        if width:
            geo = f"{width}x{height}" if height else str(width)
            self.win.geometry(geo)

        tk.Frame(self.win, bg=C['accent'], height=4).pack(fill="x")

        tk.Label(self.win, text=title, font=("Segoe UI", 13, "bold"),
                 bg=C['white'], fg=C['text']).pack(pady=(20, 2), padx=24, anchor="w")
        mk_sep(self.win).pack(fill="x", padx=24, pady=(8, 0))

        self.body = tk.Frame(self.win, bg=C['white'])
        self.body.pack(fill="both", expand=True, padx=24, pady=16)

        self.footer = tk.Frame(self.win, bg=C['ibg'])
        self.footer.pack(fill="x")
        mk_sep(self.footer, color=C['border']).pack(fill="x")

        self.btn_row = tk.Frame(self.footer, bg=C['ibg'])
        self.btn_row.pack(fill="x", padx=16, pady=10)

    def add_ok(self, text="Зберегти", cmd=None, cancel=True):
        if cancel:
            mk_btn(self.btn_row, "Скасувати",
                   self.win.destroy, bg=C['ibg'], fg=C['text'],
                   pady=7).pack(side="right", padx=(6, 0))
        mk_btn(self.btn_row, text, cmd or self.win.destroy,
               pady=7).pack(side="right")

    def field(self, label, key=None, show=None, default='', widget=None):
        """Add a labelled field to the body. Returns the entry widget."""
        mk_label(self.body, label, size=9).pack(anchor="w", pady=(8, 2))
        if widget is not None:
            widget.pack(fill="x", ipady=0)
            return widget
        e = mk_entry(self.body, show=show)
        if default:
            e.insert(0, str(default))
        e.pack(fill="x", ipady=7)
        return e

    def combobox(self, label, values, default='', readonly=True):
        mk_label(self.body, label, size=9).pack(anchor="w", pady=(8, 2))
        v = tk.StringVar(value=default or (values[0] if values else ''))
        cb = ttk.Combobox(self.body, textvariable=v, values=values,
                          state="readonly" if readonly else "normal",
                          font=("Segoe UI", 10))
        cb.pack(fill="x", ipady=5)
        return v

    def textarea(self, label, default='', height=3):
        mk_label(self.body, label, size=9).pack(anchor="w", pady=(8, 2))
        t = tk.Text(self.body, font=("Segoe UI", 10), height=height,
                    relief="flat", bg=C['ibg'], fg=C['text'],
                    insertbackground=C['text'],
                    highlightthickness=1,
                    highlightbackground=C['border'],
                    highlightcolor=C['accent'])
        if default:
            t.insert("1.0", default)
        t.pack(fill="x")
        return t

    def error(self, text=''):
        if not hasattr(self, '_err_lbl'):
            self._err_lbl = tk.Label(self.body, text='', font=("Segoe UI", 9),
                                     bg=C['white'], fg=C['danger'], wraplength=420)
            self._err_lbl.pack(pady=(8, 0))
        self._err_lbl.config(text=text)
