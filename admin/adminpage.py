import tkinter as tk
from tkinter import ttk, messagebox

from main.uihelper import mk_btn, mk_sep, make_tree, chart_card, draw_hbar, draw_donut_legend
from db.db import db
from db.current_user import current_user
from main.theme import C
from db.usersdb import (
    log_action, db_get_users, db_create_user, db_set_role,
    db_delete_user, db_set_department,
)
from db.workersdb import (
    DEPARTMENTS, db_get_workers, db_delete_workers, db_add_worker, db_get_departments,
)
from main.task import (
    db_get_tasks, db_delete_tasks, db_task_status, db_get_time_sessions,
    db_get_analytics, db_get_task_stats_by_dept, TASK_STATUSES, PRIORITY_LEVELS,
)
from db.modalbase import Modal
from login.lock import reset_attempts


def _all_departments():
    return list(dict.fromkeys(DEPARTMENTS + db_get_departments()))


def pg_admin(self):
    if current_user['role'] != 'admin':
        return
    nb = ttk.Notebook(self.page)
    nb.pack(fill="both", expand=True)
    tu = tk.Frame(nb, bg=C['bg'])
    tw = tk.Frame(nb, bg=C['bg'])
    tt = tk.Frame(nb, bg=C['bg'])
    ta = tk.Frame(nb, bg=C['bg'])
    nb.add(tu, text="  Користувачі  ")
    nb.add(tw, text="  Працівники  ")
    nb.add(tt, text="  Завдання  ")
    nb.add(ta, text="  Аналітика  ")
    self._admin_users(tu)
    self._admin_workers(tw)
    self._admin_tasks(tt)
    self._admin_analytics(ta)


def _admin_users(self, parent):
    utree_h = [None]

    bar = tk.Frame(parent, bg=C['bg'])
    bar.pack(fill="x", padx=20, pady=(16, 8))

    mk_btn(bar, "Створити користувача",
           lambda: self._create_user_dialog(utree_h[0])).pack(side="left")
    mk_btn(bar, "Працівник + акаунт",
           lambda: self._create_worker_user_dialog(utree_h[0]),
           bg=C['success']).pack(side="left", padx=(8, 0))
    mk_btn(bar, "Зробити адміном",
           lambda: self._au_role(utree_h[0], 'admin'),
           bg=C['warn']).pack(side="left", padx=(8, 0))
    mk_btn(bar, "Зробити user",
           lambda: self._au_role(utree_h[0], 'user'),
           bg=C['ibg'], fg=C['text']).pack(side="left", padx=(8, 0))
    mk_btn(bar, "Змінити відділ",
           lambda: self._au_set_dept(utree_h[0]),
           bg=C['info'], fg=C['sidebar']).pack(side="left", padx=(8, 0))
    mk_btn(bar, "Скинути блокування",
           lambda: self._au_reset_lock(utree_h[0]),
           bg=C['ibg'], fg=C['text']).pack(side="left", padx=(8, 0))
    mk_btn(bar, "Видалити",
           lambda: self._au_delete(utree_h[0]),
           bg=C['danger']).pack(side="left", padx=(8, 0))
    mk_btn(bar, "Оновити",
           lambda: self._au_reload(utree_h[0]),
           bg=C['ibg'], fg=C['text']).pack(side="right")

    pad = tk.Frame(parent, bg=C['bg'])
    pad.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    pad.columnconfigure(0, weight=1)
    pad.rowconfigure(0, weight=1)

    tree = make_tree(pad,
                     ["ID", "Логін", "Роль", "Відділ", "Телефон", "Email", "Організація", "Реєстрація", "Останній вхід"],
                     [40, 120, 60, 100, 110, 160, 130, 140, 140])
    utree_h[0] = tree
    self._au_reload(tree)


def _create_user_dialog(self, tree):
    dlg = Modal(self.root, "Створити користувача", width=440, height=460)

    eu = dlg.field("Логін *")
    ep = dlg.field("Пароль *", show="*")
    ep2 = dlg.field("Повторити пароль *", show="*")
    rv = dlg.combobox("Роль", ["user", "admin"], default="user")
    dv = dlg.combobox("Відділ", _all_departments(), default=DEPARTMENTS[0])

    def submit():
        u = eu.get().strip()
        p = ep.get()
        p2 = ep2.get()
        if not u or not p:
            dlg.error("Заповніть всі обов'язкові поля.")
            return
        if len(p) < 4:
            dlg.error("Пароль мінімум 4 символи.")
            return
        if p != p2:
            dlg.error("Паролі не співпадають.")
            return
        dept = dv.get().strip()
        if rv.get() == 'user' and not dept:
            dlg.error("Для user оберіть відділ.")
            return
        if db_create_user(u, p, rv.get(), dept):
            log_action(f"(адмін) створив юзера: {u} роль={rv.get()} відділ={dept}")
            self._au_reload(tree)
            dlg.win.destroy()
        else:
            dlg.error("Логін вже зайнятий.")

    dlg.add_ok("Створити", submit)


def _create_worker_user_dialog(self, tree):
    dlg = Modal(self.root, "Працівник + акаунт", width=520, height=680)

    en = dlg.field("ПІБ працівника *")
    ep = dlg.field("Посада")
    dv = dlg.combobox("Відділ *", _all_departments(), default=DEPARTMENTS[0])
    eu = dlg.field("Логін *")
    epw = dlg.field("Пароль *", show="*")
    epw2 = dlg.field("Повторити пароль *", show="*")
    es = dlg.field("Зарплата (грн)", default="0")
    eh = dlg.field("Дата найму (РРРР-ММ-ДД)")

    def submit():
        name = en.get().strip()
        login = eu.get().strip()
        pw = epw.get()
        pw2 = epw2.get()
        dept = dv.get().strip()
        if not name or not login or not pw or not dept:
            dlg.error("Заповніть обов'язкові поля (*).")
            return
        if len(pw) < 4:
            dlg.error("Пароль мінімум 4 символи.")
            return
        if pw != pw2:
            dlg.error("Паролі не співпадають.")
            return
        try:
            sal = float(es.get().replace(',', '.') or 0)
        except ValueError:
            dlg.error("Зарплата повинна бути числом.")
            return
        if not db_create_user(login, pw, 'user', dept):
            dlg.error("Логін вже зайнятий.")
            return
        db_add_worker({
            'name': name, 'position': ep.get().strip(), 'department': dept,
            'salary': sal, 'hire_date': eh.get().strip(),
            'phone': '', 'email': '', 'note': '', 'status': 'Активний',
        })
        log_action(f"(адмін) створив працівника+акаунт: {name} ({login}) відділ={dept}")
        self._au_reload(tree)
        dlg.win.destroy()
        messagebox.showinfo("Готово", f"Створено працівника «{name}» та акаунт «{login}» у відділі {dept}.")

    dlg.add_ok("Створити", submit)


def _au_reload(self, tree):
    if not tree:
        return
    for r in tree.get_children():
        tree.delete(r)
    for i, row in enumerate(db_get_users()):
        ts   = (row[7] or '')[:19].replace("T", " ")
        last = (row[8] or '')[:19].replace("T", " ")
        tag  = "admin" if row[2] == 'admin' else ("even" if i % 2 == 0 else "odd")
        tree.insert("", "end", iid=str(row[0]),
                    values=(row[0], row[1], row[2], row[6] or '—', row[3] or '',
                            row[4] or '', row[5] or '', ts, last),
                    tags=(tag,))


def _au_set_dept(self, tree):
    if not tree:
        return
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Увага", "Виберіть користувача.")
        return
    dlg = Modal(self.root, "Змінити відділ", width=380, height=220)
    dv = dlg.combobox("Відділ", _all_departments(), default=DEPARTMENTS[0])

    def submit():
        dept = dv.get().strip()
        for s in sel:
            db_set_department(int(s), dept)
            log_action(f"змінив відділ user id={s} -> {dept}")
        self._au_reload(tree)
        dlg.win.destroy()

    dlg.add_ok("Зберегти", submit)


def _au_role(self, tree, role):
    if not tree:
        return
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Увага", "Виберіть користувача.")
        return
    for s in sel:
        db_set_role(int(s), role)
        log_action(f"змінив роль user id={s} на {role}")
    self._au_reload(tree)


def _au_reset_lock(self, tree):
    if not tree:
        return
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Увага", "Виберіть користувача.")
        return
    for s in sel:
        uname = tree.item(s, 'values')[1]
        reset_attempts(uname)
        log_action(f"скинув блокування для: {uname}")
    messagebox.showinfo("Готово", "Блокування скинуто.")


def _au_delete(self, tree):
    if not tree:
        return
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Увага", "Виберіть користувача.")
        return
    for s in sel:
        if int(s) == current_user['id']:
            messagebox.showwarning("Увага", "Неможливо видалити власний акаунт.")
            return
    if not messagebox.askyesno("Підтвердження", f"Видалити {len(sel)} користувача(ів)?"):
        return
    for s in sel:
        db_delete_user(int(s))
        log_action(f"видалив user id={s}")
    self._au_reload(tree)


def _admin_workers(self, parent):
    wh = [None]
    dept_var = tk.StringVar(value='Всі')

    bar = tk.Frame(parent, bg=C['bg'])
    bar.pack(fill="x", padx=20, pady=(16, 8))
    mk_btn(bar, "Додати", self.worker_add).pack(side="left")
    mk_btn(bar, "Працівник + акаунт",
           lambda: self._create_worker_user_dialog(None),
           bg=C['success']).pack(side="left", padx=(8, 0))
    mk_btn(bar, "Редагувати",
           lambda: self._aw_edit(wh[0]),
           bg=C['warn']).pack(side="left", padx=(8, 0))
    mk_btn(bar, "Видалити",
           lambda: self._aw_delete(wh[0]),
           bg=C['danger']).pack(side="left", padx=(8, 0))

    right = tk.Frame(bar, bg=C['bg'])
    right.pack(side="right")
    tk.Label(right, text="Відділ:", font=("Segoe UI", 9),
             bg=C['bg'], fg=C['muted']).pack(side="left", padx=(0, 4))
    cb = ttk.Combobox(right, textvariable=dept_var,
                      values=['Всі'] + _all_departments(),
                      state="readonly", width=16, font=("Segoe UI", 9))
    cb.pack(side="left")
    cb.bind("<<ComboboxSelected>>", lambda e: self._aw_reload(wh[0], dept_var))

    pad = tk.Frame(parent, bg=C['bg'])
    pad.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    pad.columnconfigure(0, weight=1)
    pad.rowconfigure(0, weight=1)

    tree = make_tree(pad,
                     ["#", "Ім'я", "Посада", "Відділ", "Статус", "Зарплата", "Дата найму"],
                     [40, 200, 140, 150, 90, 120, 130])
    wh[0] = tree
    self._aw_reload(tree, dept_var)


def _aw_reload(self, tree, dept_var):
    if not tree:
        return
    for r in tree.get_children():
        tree.delete(r)
    filt = dept_var.get() if dept_var else 'Всі'
    rows = db_get_workers(dept_filter=filt)
    for i, row in enumerate(rows):
        sal = f"{row[3]:,.0f} грн" if row[3] else ""
        tag = "even" if i % 2 == 0 else "odd"
        tree.insert("", "end", iid=str(row[0]),
                    values=(row[0], row[1], row[7], row[2], row[9] if len(row) > 9 else '', sal, row[4]),
                    tags=(tag,))


def _aw_edit(self, tree):
    if not tree:
        return
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Увага", "Виберіть рядок.")
        return
    wid = int(sel[0])
    conn = db()
    row = conn.execute('SELECT * FROM workers WHERE id=?', (wid,)).fetchone()
    conn.close()
    if row:
        data = {
            'id': row[0], 'name': row[1], 'department': row[2], 'salary': row[3],
            'hire_date': row[4], 'phone': row[5], 'email': row[6],
            'position': row[7], 'note': row[8],
            'status': row[9] if len(row) > 9 else 'Активний'
        }
        self._worker_form(data)


def _aw_delete(self, tree):
    if not tree:
        return
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Увага", "Виберіть рядок.")
        return
    if not messagebox.askyesno("Підтвердження", "Видалити?"):
        return
    ids = [int(s) for s in sel]
    db_delete_workers(ids)
    log_action(f"(адмін) видалив працівників id={ids}")
    for s in sel:
        tree.delete(s)


def _admin_tasks(self, parent):
    th = [None]
    dept_var = tk.StringVar(value='Всі')

    bar = tk.Frame(parent, bg=C['bg'])
    bar.pack(fill="x", padx=20, pady=(16, 8))
    mk_btn(bar, "Нове завдання", self.task_add).pack(side="left")
    mk_btn(bar, "Видалити",
           lambda: self._at_delete(th[0]),
           bg=C['danger']).pack(side="left", padx=(8, 0))
    mk_btn(bar, "Виконано",
           lambda: self._at_status(th[0], "Виконано"),
           bg=C['success']).pack(side="left", padx=(8, 0))
    mk_btn(bar, "В роботу",
           lambda: self._at_status(th[0], "В роботі"),
           bg=C['info'], fg=C['sidebar']).pack(side="left", padx=(8, 0))

    right = tk.Frame(bar, bg=C['bg'])
    right.pack(side="right")
    tk.Label(right, text="Відділ:", font=("Segoe UI", 9),
             bg=C['bg'], fg=C['muted']).pack(side="left", padx=(0, 4))
    cb = ttk.Combobox(right, textvariable=dept_var,
                      values=['Всі'] + _all_departments(),
                      state="readonly", width=16, font=("Segoe UI", 9))
    cb.pack(side="left")
    cb.bind("<<ComboboxSelected>>", lambda e: self._at_reload(th[0], dept_var))

    pad = tk.Frame(parent, bg=C['bg'])
    pad.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    pad.columnconfigure(0, weight=1)
    pad.rowconfigure(0, weight=1)

    tree = make_tree(pad,
                     ["#", "Назва", "Відділ", "Відповідальний", "Пріоритет", "Дедлайн", "Статус", "Автор"],
                     [40, 200, 100, 140, 100, 110, 100, 110])
    th[0] = tree
    self._at_reload(tree, dept_var)


def _at_reload(self, tree, dept_var):
    if not tree:
        return
    for r in tree.get_children():
        tree.delete(r)
    filt = dept_var.get() if dept_var else 'Всі'
    dept = None if filt == 'Всі' else filt
    for i, row in enumerate(db_get_tasks(department=dept)):
        done = row[5] == "Виконано"
        tag  = "done" if done else row[3]
        dept_name = row[9] if len(row) > 9 else ''
        tree.insert("", "end", iid=str(row[0]),
                    values=(row[0], row[1], dept_name, row[2], row[3], row[4], row[5], row[6]),
                    tags=(tag,))


def _at_delete(self, tree):
    if not tree:
        return
    sel = tree.selection()
    if not sel:
        return
    if not messagebox.askyesno("Підтвердження", "Видалити вибрані завдання?"):
        return
    ids = [int(s) for s in sel]
    db_delete_tasks(ids)
    for s in sel:
        tree.delete(s)
    log_action(f"(адмін) видалив завдання id={ids}")


def _at_status(self, tree, status):
    if not tree:
        return
    sel = tree.selection()
    if not sel:
        return
    ids = [int(s) for s in sel]
    db_task_status(ids, status)
    for s in sel:
        vals    = list(tree.item(s, 'values'))
        vals[6] = status
        tag = "done" if status == "Виконано" else vals[4]
        tree.item(s, values=vals, tags=(tag,))
    log_action(f"(адмін) статус завдань id={ids} -> {status}")


def _admin_analytics(self, parent):
    canvas = tk.Canvas(parent, bg=C['bg'], highlightthickness=0)
    scroll = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    inner = tk.Frame(canvas, bg=C['bg'])
    cwin = canvas.create_window((0, 0), window=inner, anchor="nw")

    def on_resize(e):
        canvas.itemconfig(cwin, width=e.width)
    canvas.bind("<Configure>", on_resize)

    def on_frame(e):
        canvas.config(scrollregion=canvas.bbox("all"))
    inner.bind("<Configure>", on_frame)

    pad = tk.Frame(inner, bg=C['bg'])
    pad.pack(fill="both", expand=True, padx=24, pady=20)

    tk.Label(pad, text="Аналітика системи",
             font=("Segoe UI", 13, "bold"),
             bg=C['bg'], fg=C['text']).pack(anchor="w", pady=(0, 16))

    data = db_get_analytics()
    done_pct = int(data['tasks_done'] / data['tasks'] * 100) if data['tasks'] else 0

    kpi_row = tk.Frame(pad, bg=C['bg'])
    kpi_row.pack(fill="x", pady=(0, 16))
    for i, (lbl, val, color) in enumerate([
        ("Користувачів", str(data['users']), C['info']),
        ("Працівників", str(data['workers']), C['accent']),
        ("Завдань", f"{data['tasks']} ({done_pct}% вик.)", C['warn']),
        ("Прострочених", str(data['overdue']), C['danger']),
    ]):
        card = tk.Frame(kpi_row, bg=C['card'],
                        highlightthickness=1, highlightbackground=C['border'])
        card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
        kpi_row.columnconfigure(i, weight=1)
        tk.Frame(card, bg=color, height=3).pack(fill="x")
        inner2 = tk.Frame(card, bg=C['card'])
        inner2.pack(fill="x", padx=14, pady=10)
        tk.Label(inner2, text=val, font=("Segoe UI", 16, "bold"),
                 bg=C['card'], fg=C['text']).pack(anchor="w")
        tk.Label(inner2, text=lbl, font=("Segoe UI", 8),
                 bg=C['card'], fg=C['muted']).pack(anchor="w")

    charts_row = tk.Frame(pad, bg=C['bg'])
    charts_row.pack(fill="x", pady=(0, 16))
    charts_row.columnconfigure(0, weight=1)
    charts_row.columnconfigure(1, weight=1)

    status_colors = {
        'Активне': C['accent'], 'В роботі': C['info'],
        'На паузі': C['warn'], 'Виконано': C['success'],
    }
    st_card, st_body = chart_card(charts_row, "Завдання за статусом")
    st_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    max_st = max((data['by_status'].get(s, 0) for s in TASK_STATUSES), default=0) or 1
    for st in TASK_STATUSES:
        draw_hbar(st_body, st, data['by_status'].get(st, 0), max_st,
                  status_colors.get(st, C['muted']), bar_width=180)

    pri_card, pri_body = chart_card(charts_row, "Активні за пріоритетом")
    pri_card.grid(row=0, column=1, sticky="nsew")
    pri_colors = {'Критична': C['danger'], 'Висока': C['warn'],
                  'Середня': '#C08010', 'Низька': C['success']}
    total_pri = sum(data['by_priority'].values()) or 1
    for pri in PRIORITY_LEVELS:
        draw_hbar(pri_body, pri, data['by_priority'].get(pri, 0), total_pri,
                  pri_colors.get(pri, C['accent']), bar_width=180)

    dept_stats = db_get_task_stats_by_dept()
    if dept_stats:
        tcard, tbody = chart_card(pad, "Завдання по відділах (активні / виконані)")
        tcard.pack(fill="x", pady=(0, 16))
        max_t = max(r[3] for r in dept_stats) or 1
        colors_d = [C['accent'], C['info'], C['success'], C['warn'], C['danger']]
        for i, (dept, done, active, total) in enumerate(dept_stats):
            label = f"{dept} ({active}акт/{done}вик)"
            draw_hbar(tbody, label, total, max_t,
                      colors_d[i % len(colors_d)], bar_width=350)

    if data['by_status']:
        donut_card, donut_body = chart_card(pad, "Загальний розподіл завдань")
        donut_card.pack(fill="x", pady=(0, 16))
        segments = [(status_colors.get(st, C['muted']), data['by_status'].get(st, 0), st)
                    for st in TASK_STATUSES]
        draw_donut_legend(donut_body, segments, size=90)

    sessions = db_get_time_sessions()
    total_dur = sum(s[3] or 0 for s in sessions)
    th, tm, ts = 0, 0, 0
    if total_dur:
        th, rem = divmod(total_dur, 3600)
        tm, ts  = divmod(rem, 60)

    info_card = tk.Frame(pad, bg=C['card'],
                         highlightthickness=1, highlightbackground=C['border'])
    info_card.pack(fill="x", pady=(0, 16))
    tk.Label(info_card, text="Облік робочого часу (всі користувачі)",
             font=("Segoe UI", 10, "bold"), bg=C['card'], fg=C['text']).pack(
        padx=16, pady=(14, 4), anchor="w")
    mk_sep(info_card).pack(fill="x", padx=16)
    body2 = tk.Frame(info_card, bg=C['card'])
    body2.pack(fill="x", padx=16, pady=10)
    for lbl, val in [
        ("Всього сесій", str(len(sessions))),
        ("Загальний час", f"{th}г {tm}хв {ts}с"),
    ]:
        r = tk.Frame(body2, bg=C['card'])
        r.pack(fill="x", pady=3)
        tk.Label(r, text=lbl, font=("Segoe UI", 9),
                 bg=C['card'], fg=C['muted']).pack(side="left")
        tk.Label(r, text=val, font=("Segoe UI", 10, "bold"),
                 bg=C['card'], fg=C['text']).pack(side="right")

    tk.Label(pad, text="Останні сесії роботи",
             font=("Segoe UI", 10, "bold"),
             bg=C['bg'], fg=C['text']).pack(anchor="w", pady=(8, 6))

    sess_frame = tk.Frame(pad, bg=C['bg'])
    sess_frame.pack(fill="x")
    sess_tree = make_tree(sess_frame,
                          ["Користувач", "Початок", "Кінець", "Тривалість"],
                          [150, 180, 180, 180])
    sess_tree.configure(height=min(10, max(3, len(sessions))))

    for i, row in enumerate(sessions[:20]):
        started = (row[1] or '')[:19].replace("T", " ")
        ended   = (row[2] or '')[:19].replace("T", " ")
        dur_s   = row[3] or 0
        h, rem  = divmod(dur_s, 3600)
        m, s    = divmod(rem, 60)
        tag = "even" if i % 2 == 0 else "odd"
        sess_tree.insert("", "end",
                         values=(row[0], started, ended, f"{h}г {m}хв {s}с"),
                         tags=(tag,))
