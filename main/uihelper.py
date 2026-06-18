import tkinter as tk
from tkinter import ttk
from main.theme import C

def mk_entry(parent, show=None, width=None, placeholder=''):
    kw = dict(font=("Segoe UI", 10), relief="flat",
              bg=C['ibg'], fg=C['text'],
              insertbackground=C['text'],
              highlightthickness=1,
              highlightbackground=C['border'],
              highlightcolor=C['accent'])
    if show:
        kw['show'] = show
    if width:
        kw['width'] = width
    e = tk.Entry(parent, **kw)
    return e

def mk_label(parent, text, size=9, color=None, bold=False, anchor='w'):
    font = ("Segoe UI", size, "bold") if bold else ("Segoe UI", size)
    return tk.Label(parent, text=text, font=font,
                    bg=parent.cget('bg'), fg=color or C['muted'], anchor=anchor)

def mk_btn(parent, text, cmd, bg=None, fg='white', padx=14, pady=8, width=None):
    kw = dict(
        text=text, command=cmd,
        font=("Segoe UI", 9, "bold"),
        bg=bg or C['accent'], fg=fg,
        relief="flat", bd=0,
        padx=padx, pady=pady,
        cursor="hand2",
        activebackground=C['accent2'] if (bg is None or bg == C['accent']) else C['border'],
        activeforeground=fg
    )
    if width:
        kw['width'] = width
    return tk.Button(parent, **kw)

def mk_sep(parent, orient='h', color=None):
    if orient == 'h':
        return tk.Frame(parent, bg=color or C['border'], height=1)
    else:
        return tk.Frame(parent, bg=color or C['border'], width=1)

def make_tree(parent, columns, widths, height=None):
    style_name = f"CRM{id(parent)}.Treeview"
    st = ttk.Style()
    st.theme_use("clam")
    st.configure(style_name,
                 background=C['tree_bg'], foreground=C['text'],
                 rowheight=34, fieldbackground=C['tree_bg'],
                 font=("Segoe UI", 9), borderwidth=0,
                 relief="flat")
    st.configure(f"{style_name}.Heading",
                 background=C['ibg'], foreground=C['muted'],
                 font=("Segoe UI", 8, "bold"), relief="flat",
                 padding=(8, 6))
    st.map(style_name,
           background=[("selected", C['tree_sel'])],
           foreground=[("selected", C['tree_sfg'])])
    st.layout(style_name, [('Treeview.treearea', {'sticky': 'nswe'})])

    wrap = tk.Frame(parent, bg=C['white'], highlightthickness=1,
                    highlightbackground=C['border'])
    wrap.pack(fill="both", expand=True)

    kw = dict(columns=columns, show="headings", style=style_name, selectmode="extended")
    if height:
        kw['height'] = height
    tree = ttk.Treeview(wrap, **kw)
    vsb  = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
    hsb  = ttk.Scrollbar(wrap, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    for col, w in zip(columns, widths):
        tree.heading(col, text=col, anchor='w')
        tree.column(col, width=w, minwidth=40, anchor="w", stretch=False)

    tree.tag_configure("even",     background=C['tree_bg'])
    tree.tag_configure("odd",      background=C['tree_alt'])
    tree.tag_configure("done",     foreground=C['muted'])
    tree.tag_configure("Критична", foreground=C['danger'])
    tree.tag_configure("Висока",   foreground=C['warn'])
    tree.tag_configure("Середня",  foreground='#C08010')
    tree.tag_configure("Низька",   foreground=C['success'])
    tree.tag_configure("admin",    foreground=C['accent'])

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    wrap.grid_rowconfigure(0, weight=1)
    wrap.grid_columnconfigure(0, weight=1)

    return tree


def chart_card(parent, title, width=None):
    """Картка для графіка з заголовком."""
    card = tk.Frame(parent, bg=C['card'],
                    highlightthickness=1, highlightbackground=C['border'])
    if width:
        card.configure(width=width)
    tk.Label(card, text=title, font=("Segoe UI", 10, "bold"),
             bg=C['card'], fg=C['text']).pack(padx=16, pady=(14, 4), anchor="w")
    mk_sep(card).pack(fill="x", padx=16)
    body = tk.Frame(card, bg=C['card'])
    body.pack(fill="both", expand=True, padx=16, pady=10)
    return card, body


def draw_hbar(parent, label, value, max_val, color, bar_width=220, suffix=''):
    """Горизонтальний bar-chart рядок."""
    r = tk.Frame(parent, bg=C['card'])
    r.pack(fill="x", pady=3)
    tk.Label(r, text=label, font=("Segoe UI", 9),
             bg=C['card'], fg=C['text'], width=14, anchor="w").pack(side="left")
    bar_bg = tk.Frame(r, bg=C['ibg'], height=10, width=bar_width)
    bar_bg.pack(side="left", padx=(4, 8))
    bar_bg.pack_propagate(False)
    if max_val and value:
        pct_w = max(4, int(value / max_val * bar_width))
        tk.Frame(bar_bg, bg=color, height=10, width=pct_w).pack(side="left")
    pct = int(value / max_val * 100) if max_val else 0
    tk.Label(r, text=f"{value}{suffix}  ({pct}%)", font=("Segoe UI", 9),
             bg=C['card'], fg=C['muted']).pack(side="left")
    return r


def draw_donut_legend(parent, segments, size=80):
    """Спрощена кругова діаграма (canvas) + легенда."""
    wrap = tk.Frame(parent, bg=C['card'])
    wrap.pack(fill="x", pady=4)

    total = sum(v for _, v, _ in segments) or 1
    cv = tk.Canvas(wrap, width=size, height=size, bg=C['card'],
                   highlightthickness=0)
    cv.pack(side="left", padx=(0, 12))

    start = 90
    for color, val, _ in segments:
        if val <= 0:
            continue
        extent = val / total * 360
        cv.create_arc(4, 4, size - 4, size - 4, start=start, extent=-extent,
                      fill=color, outline=C['card'], width=2)
        start -= extent
    if total == 0 or all(v == 0 for _, v, _ in segments):
        cv.create_oval(4, 4, size - 4, size - 4, outline=C['border'], width=2)

    leg = tk.Frame(wrap, bg=C['card'])
    leg.pack(side="left", fill="y")
    for color, val, lbl in segments:
        row = tk.Frame(leg, bg=C['card'])
        row.pack(fill="x", pady=1)
        tk.Frame(row, bg=color, width=10, height=10).pack(side="left", padx=(0, 6))
        pct = int(val / total * 100) if total else 0
        tk.Label(row, text=f"{lbl}: {val} ({pct}%)", font=("Segoe UI", 8),
                 bg=C['card'], fg=C['text']).pack(side="left")
    return wrap