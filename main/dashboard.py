import tkinter as tk
from uihelper import mk_sep
from theme import C
from tkinter import ttk
from db import db_get_analytics
from task import PRIORITY_LEVELS

def pg_dashboard(self):
        canvas = tk.Canvas(self.page, bg=C['bg'], highlightthickness=0)
        scroll = ttk.Scrollbar(self.page, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        inner = tk.Frame(canvas, bg=C['bg'])
        cwin = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.columnconfigure(0, weight=1)

        def on_resize(e):
            canvas.itemconfig(cwin, width=e.width)
        canvas.bind("<Configure>", on_resize)

        def on_frame(e):
            canvas.config(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", on_frame)

        pad = tk.Frame(inner, bg=C['bg'])
        pad.pack(fill="both", expand=True, padx=24, pady=20)

        data = db_get_analytics()
        done_pct = int(data['tasks_done'] / data['tasks'] * 100) if data['tasks'] else 0

        kpi = [
            ("Працівників",        str(data['workers']),       C['accent']),
            ("Всього завдань",      str(data['tasks']),         C['warn']),
            ("Виконано завдань",    f"{data['tasks_done']} ({done_pct}%)", C['success']),
            ("Активних завдань",    str(data['tasks_active']),  C['danger']),
            ("Користувачів",        str(data['users']),         C['info']),
            ("Дій за 24г",          str(data['recent_logs']),   C['muted']),
        ]
        kpi_row = tk.Frame(pad, bg=C['bg'])
        kpi_row.pack(fill="x", pady=(0, 20))
        for i, (lbl, val, color) in enumerate(kpi):
            card = tk.Frame(kpi_row, bg=C['card'],
                            highlightthickness=1, highlightbackground=C['border'])
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i==0 else 8, 0))
            kpi_row.columnconfigure(i, weight=1)
            tk.Frame(card, bg=color, height=3).pack(fill="x")
            inner2 = tk.Frame(card, bg=C['card'])
            inner2.pack(fill="x", padx=14, pady=10)
            tk.Label(inner2, text=val, font=("Segoe UI", 18, "bold"),
                     bg=C['card'], fg=C['text']).pack(anchor="w")
            tk.Label(inner2, text=lbl, font=("Segoe UI", 8),
                     bg=C['card'], fg=C['muted']).pack(anchor="w")

        row2 = tk.Frame(pad, bg=C['bg'])
        row2.pack(fill="x", pady=(0, 20))
        row2.columnconfigure(0, weight=2)
        row2.columnconfigure(1, weight=3)

        sal_card = tk.Frame(row2, bg=C['card'],
                            highlightthickness=1, highlightbackground=C['border'])
        sal_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        tk.Label(sal_card, text="Фінанси (зарплата)",
                 font=("Segoe UI", 10, "bold"), bg=C['card'], fg=C['text']).pack(
            padx=16, pady=(14, 4), anchor="w")
        mk_sep(sal_card).pack(fill="x", padx=16)
        sal_body = tk.Frame(sal_card, bg=C['card'])
        sal_body.pack(fill="x", padx=16, pady=10)
        for lbl, val in [
            ("Сер. зарплата", f"{data['avg_salary']:,.0f} грн"),
            ("Фонд ЗП",       f"{data['total_salary']:,.0f} грн"),
        ]:
            r = tk.Frame(sal_body, bg=C['card'])
            r.pack(fill="x", pady=4)
            tk.Label(r, text=lbl, font=("Segoe UI", 9),
                     bg=C['card'], fg=C['muted']).pack(side="left")
            tk.Label(r, text=val, font=("Segoe UI", 10, "bold"),
                     bg=C['card'], fg=C['success']).pack(side="right")

        pri_card = tk.Frame(row2, bg=C['card'],
                            highlightthickness=1, highlightbackground=C['border'])
        pri_card.grid(row=0, column=1, sticky="nsew")
        tk.Label(pri_card, text="Активні завдання за пріоритетом",
                 font=("Segoe UI", 10, "bold"), bg=C['card'], fg=C['text']).pack(
            padx=16, pady=(14, 4), anchor="w")
        mk_sep(pri_card).pack(fill="x", padx=16)
        pri_body = tk.Frame(pri_card, bg=C['card'])
        pri_body.pack(fill="x", padx=16, pady=10)
        colors = {'Критична': C['danger'], 'Висока': C['warn'],
                  'Середня': '#C08010', 'Низька': C['success']}
        total_pri = sum(data['by_priority'].values()) or 1
        for pri in PRIORITY_LEVELS:
            cnt = data['by_priority'].get(pri, 0)
            pct = int(cnt / total_pri * 100)
            r = tk.Frame(pri_body, bg=C['card'])
            r.pack(fill="x", pady=3)
            tk.Label(r, text=pri, font=("Segoe UI", 9),
                     bg=C['card'], fg=C['text'], width=10, anchor="w").pack(side="left")
            bar_bg = tk.Frame(r, bg=C['ibg'], height=8, width=200)
            bar_bg.pack(side="left", padx=(8, 8))
            bar_bg.pack_propagate(False)
            if pct > 0:
                tk.Frame(bar_bg, bg=colors.get(pri, C['accent']),
                         height=8, width=max(4, pct*2)).pack(side="left")
            tk.Label(r, text=f"{cnt}  ({pct}%)", font=("Segoe UI", 9),
                     bg=C['card'], fg=C['muted']).pack(side="left")

        if data['by_dept']:
            dept_card = tk.Frame(pad, bg=C['card'],
                                 highlightthickness=1, highlightbackground=C['border'])
            dept_card.pack(fill="x")
            tk.Label(dept_card, text="Топ відділи за кількістю співробітників",
                     font=("Segoe UI", 10, "bold"), bg=C['card'], fg=C['text']).pack(
                padx=16, pady=(14, 4), anchor="w")
            mk_sep(dept_card).pack(fill="x", padx=16)
            dept_body = tk.Frame(dept_card, bg=C['card'])
            dept_body.pack(fill="x", padx=16, pady=10)
            max_cnt = max(r[1] for r in data['by_dept']) or 1
            for i, (dept, cnt) in enumerate(data['by_dept']):
                r = tk.Frame(dept_body, bg=C['card'])
                r.pack(fill="x", pady=3)
                tk.Label(r, text=dept or '(без відділу)', font=("Segoe UI", 9),
                         bg=C['card'], fg=C['text'], width=20, anchor="w").pack(side="left")
                bar_bg = tk.Frame(r, bg=C['ibg'], height=8, width=300)
                bar_bg.pack(side="left", padx=8)
                bar_bg.pack_propagate(False)
                pct_w = max(4, int(cnt / max_cnt * 300))
                colors_d = [C['accent'], C['info'], C['success'], C['warn'], C['danger']]
                tk.Frame(bar_bg, bg=colors_d[i % len(colors_d)],
                         height=8, width=pct_w).pack(side="left")
                tk.Label(r, text=str(cnt), font=("Segoe UI", 9, "bold"),
                         bg=C['card'], fg=C['text']).pack(side="left", padx=6)
