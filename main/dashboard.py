import tkinter as tk
from tkinter import ttk

from main.uihelper import mk_sep, chart_card, draw_hbar, draw_donut_legend
from main.theme import C
from main.task import db_get_analytics, PRIORITY_LEVELS, TASK_STATUSES
from db.current_user import current_user


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

    admin = current_user['role'] == 'admin'
    dept = None if admin else (current_user.get('department') or '')
    data = db_get_analytics(dept if not admin else None)
    done_pct = int(data['tasks_done'] / data['tasks'] * 100) if data['tasks'] else 0

    hdr = tk.Frame(pad, bg=C['bg'])
    hdr.pack(fill="x", pady=(0, 12))
    title = "Панель керування" if admin else f"Панель — {dept or 'без відділу'}"
    tk.Label(hdr, text=title, font=("Segoe UI", 14, "bold"),
             bg=C['bg'], fg=C['text']).pack(side="left")
    if not admin and dept:
        tk.Label(hdr, text="Показано дані лише вашого відділу",
                 font=("Segoe UI", 9), bg=C['bg'], fg=C['muted']).pack(side="left", padx=12)

    kpi = [
        ("Працівників",        str(data['workers']),       C['accent']),
        ("Всього завдань",      str(data['tasks']),         C['warn']),
        ("Виконано завдань",    f"{data['tasks_done']} ({done_pct}%)", C['success']),
        ("Активних завдань",    str(data['tasks_active']),  C['danger']),
        ("Прострочених",        str(data['overdue']),       C['danger']),
        ("Дій за 24г",          str(data['recent_logs']),   C['muted']),
    ]
    if admin:
        kpi[4] = ("Користувачів", str(data['users']), C['info'])

    kpi_row = tk.Frame(pad, bg=C['bg'])
    kpi_row.pack(fill="x", pady=(0, 20))
    for i, (lbl, val, color) in enumerate(kpi):
        card = tk.Frame(kpi_row, bg=C['card'],
                        highlightthickness=1, highlightbackground=C['border'])
        card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
        kpi_row.columnconfigure(i, weight=1)
        tk.Frame(card, bg=color, height=3).pack(fill="x")
        inner2 = tk.Frame(card, bg=C['card'])
        inner2.pack(fill="x", padx=14, pady=10)
        tk.Label(inner2, text=val, font=("Segoe UI", 18, "bold"),
                 bg=C['card'], fg=C['text']).pack(anchor="w")
        tk.Label(inner2, text=lbl, font=("Segoe UI", 8),
                 bg=C['card'], fg=C['muted']).pack(anchor="w")

    row2 = tk.Frame(pad, bg=C['bg'])
    row2.pack(fill="x", pady=(0, 16))
    row2.columnconfigure(0, weight=1)
    row2.columnconfigure(1, weight=1)
    row2.columnconfigure(2, weight=1)

    sal_card, sal_body = chart_card(row2, "Фінанси (зарплата)")
    sal_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
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

    status_colors = {
        'Активне': C['accent'], 'В роботі': C['info'],
        'На паузі': C['warn'], 'Виконано': C['success'],
    }
    st_card, st_body = chart_card(row2, "Завдання за статусом")
    st_card.grid(row=0, column=1, sticky="nsew", padx=(0, 8))
    max_st = max((data['by_status'].get(s, 0) for s in TASK_STATUSES), default=0) or 1
    for st in TASK_STATUSES:
        cnt = data['by_status'].get(st, 0)
        draw_hbar(st_body, st, cnt, max_st, status_colors.get(st, C['muted']), bar_width=160)

    pri_card, pri_body = chart_card(row2, "Активні за пріоритетом")
    pri_card.grid(row=0, column=2, sticky="nsew")
    pri_colors = {'Критична': C['danger'], 'Висока': C['warn'],
                  'Середня': '#C08010', 'Низька': C['success']}
    colors_d = [C['accent'], C['info'], C['success'], C['warn'], C['danger'],
                '#8B5CF6', '#EC4899', '#14B8A6']
    total_pri = sum(data['by_priority'].values()) or 1
    for pri in PRIORITY_LEVELS:
        cnt = data['by_priority'].get(pri, 0)
        draw_hbar(pri_body, pri, cnt, total_pri, pri_colors.get(pri, C['accent']), bar_width=160)

    row3 = tk.Frame(pad, bg=C['bg'])
    row3.pack(fill="x", pady=(0, 16))
    row3.columnconfigure(0, weight=1)
    row3.columnconfigure(1, weight=1)

    if data['by_worker_status']:
        ws_card, ws_body = chart_card(row3, "Працівники за статусом")
        ws_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ws_colors = {'Активний': C['success'], 'Відпустка': C['warn'], 'Звільнений': C['muted']}
        max_ws = max(data['by_worker_status'].values()) or 1
        for st, cnt in data['by_worker_status'].items():
            draw_hbar(ws_body, st, cnt, max_ws, ws_colors.get(st, C['accent']), bar_width=180)

    if data['by_status']:
        donut_card, donut_body = chart_card(row3, "Розподіл завдань (загалом)")
        donut_card.grid(row=0, column=1, sticky="nsew")
        segments = [(status_colors.get(st, C['muted']), data['by_status'].get(st, 0), st)
                    for st in TASK_STATUSES]
        draw_donut_legend(donut_body, segments)

    if data['by_dept']:
        dept_card, dept_body = chart_card(pad, "Працівники за відділами")
        dept_card.pack(fill="x", pady=(0, 16))
        max_cnt = max(r[1] for r in data['by_dept']) or 1
        for i, (dept_name, cnt) in enumerate(data['by_dept']):
            draw_hbar(dept_body, dept_name or '(без)', cnt, max_cnt,
                      colors_d[i % len(colors_d)], bar_width=400)

    if admin and data.get('by_task_dept'):
        tdept_card, tdept_body = chart_card(pad, "Активні завдання за відділами")
        tdept_card.pack(fill="x", pady=(0, 16))
        max_td = max(r[1] for r in data['by_task_dept']) or 1
        for i, (dept_name, cnt) in enumerate(data['by_task_dept']):
            draw_hbar(tdept_body, dept_name, cnt, max_td,
                      colors_d[i % len(colors_d)], bar_width=400)

    if admin and data.get('completion_by_dept'):
        comp_card, comp_body = chart_card(pad, "Виконання завдань по відділах (%)")
        comp_card.pack(fill="x")
        for i, (dept_name, done, total) in enumerate(data['completion_by_dept']):
            pct = int(done / total * 100) if total else 0
            draw_hbar(comp_body, dept_name, pct, 100, C['success'], bar_width=400, suffix='%')
