import tkinter as tk
from tkinter import ttk
from theme import C

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