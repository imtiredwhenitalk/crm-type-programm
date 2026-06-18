import tkinter as tk
from tkinter import ttk, messagebox

from main.uihelper import mk_label, mk_entry, mk_btn, make_tree, mk_sep
from db.modalbase import Modal
from main.task import (
    db_get_tasks, db_add_task, db_update_task, db_delete_tasks,
    db_task_status, TASK_STATUSES, PRIORITY_LEVELS,
)
from db.db import db
from db.current_user import current_user
from db.usersdb import log_action
from db.workersdb import DEPARTMENTS, db_get_workers, db_get_departments
from main.theme import C


def _user_department():
    if current_user['role'] == 'admin':
        return None
    return current_user.get('department') or ''


def _all_departments():
    return list(dict.fromkeys(DEPARTMENTS + db_get_departments()))


def pg_tasks(self):
    bar   = tk.Frame(self.page, bg=C['bg'])
    bar.pack(fill="x", padx=20, pady=(16, 8))
    admin = current_user['role'] == 'admin'
    dept  = _user_department()

    left_f = tk.Frame(bar, bg=C['bg'])
    left_f.pack(side="left")

    if admin:
        mk_btn(left_f, "Нове завдання", self.task_add).pack(side="left")
        mk_btn(left_f, "Редагувати", self.task_edit,
               bg=C['warn']).pack(side="left", padx=(8, 0))
        mk_btn(left_f, "Видалити", self.task_del,
               bg=C['danger']).pack(side="left", padx=(8, 0))

    mk_btn(left_f, "В роботу", lambda: self.task_set_status("В роботі"),
           bg=C['info'], fg=C['sidebar']).pack(side="left", padx=(8, 0))
    mk_btn(left_f, "Виконано", lambda: self.task_set_status("Виконано"),
           bg=C['success']).pack(side="left", padx=(8, 0))
    mk_btn(left_f, "Пауза", lambda: self.task_set_status("На паузі"),
           bg=C['ibg'], fg=C['text']).pack(side="left", padx=(8, 0))

    right_f = tk.Frame(bar, bg=C['bg'])
    right_f.pack(side="right")

    if dept:
        tk.Label(right_f, text=f"Відділ: {dept}",
                 font=("Segoe UI", 9, "bold"), bg=C['bg'], fg=C['accent']).pack(side="right", padx=(12, 0))

    mk_label(right_f, "Пошук:", size=9).pack(side="left", padx=(0, 4))
    self.tsearch = tk.StringVar()
    self.tsearch.trace("w", lambda *a: self.task_reload())
    e = mk_entry(right_f, width=16)
    e.configure(textvariable=self.tsearch)
    e.pack(side="left", ipady=6)

    mk_label(right_f, "Фільтр:", size=9).pack(side="left", padx=(12, 4))
    self.tfilter = tk.StringVar(value="Всі")
    cb = ttk.Combobox(right_f, textvariable=self.tfilter,
                      values=["Всі", "Виконані"] + PRIORITY_LEVELS + TASK_STATUSES,
                      state="readonly", width=14, font=("Segoe UI", 9))
    cb.pack(side="left")
    cb.bind("<<ComboboxSelected>>", lambda e: self.task_reload())

    pad = tk.Frame(self.page, bg=C['bg'])
    pad.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    pad.columnconfigure(0, weight=1)
    pad.rowconfigure(0, weight=1)

    cols = ["#", "Назва", "Відповідальний", "Категорія", "Пріоритет", "Дедлайн", "Статус", "Автор"]
    widths = [40, 210, 140, 110, 100, 110, 100, 110]
    if admin:
        cols = ["#", "Назва", "Відділ", "Відповідальний", "Категорія", "Пріоритет", "Дедлайн", "Статус", "Автор"]
        widths = [40, 180, 90, 130, 100, 90, 100, 90, 100]

    self.ttree = make_tree(pad, cols, widths)
    self.ttree.bind("<Double-1>", lambda e: self.task_edit() if admin else None)
    self.task_reload()


def task_reload(self):
    if not self.ttree:
        return
    filt   = self.tfilter.get() if self.tfilter else "Всі"
    search = self.tsearch.get() if hasattr(self, 'tsearch') and self.tsearch else ''
    dept   = _user_department()
    admin  = current_user['role'] == 'admin'
    for r in self.ttree.get_children():
        self.ttree.delete(r)
    for i, row in enumerate(db_get_tasks(filt, search, department=dept)):
        done = row[5] == "Виконано"
        tag  = "done" if done else row[3]
        dept_name = row[9] if len(row) > 9 else ''
        if admin:
            values = (row[0], row[1], dept_name, row[2], row[8], row[3], row[4], row[5], row[6])
        else:
            values = (row[0], row[1], row[2], row[8], row[3], row[4], row[5], row[6])
        self.ttree.insert("", "end", iid=str(row[0]), values=values, tags=(tag,))


def task_del(self):
    sel = self.ttree.selection()
    if not sel:
        messagebox.showwarning("Увага", "Виберіть завдання.")
        return
    if not messagebox.askyesno("Підтвердження", f"Видалити {len(sel)} завдання(нь)?"):
        return
    ids = [int(s) for s in sel]
    db_delete_tasks(ids)
    log_action(f"видалив завдання id={ids}")
    self.task_reload()


def task_set_status(self, status):
    sel = self.ttree.selection()
    if not sel:
        messagebox.showwarning("Увага", "Виберіть завдання.")
        return
    ids = [int(s) for s in sel]
    db_task_status(ids, status)
    log_action(f"змінив статус завдань id={ids} -> {status}")
    self.task_reload()


def task_add(self):
    self._task_form(None)


def task_edit(self):
    if current_user['role'] != 'admin':
        return
    sel = self.ttree.selection()
    if not sel:
        messagebox.showwarning("Увага", "Виберіть завдання.")
        return
    tid = int(sel[0])
    conn = db()
    row = conn.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
    conn.close()
    if row:
        data = {
            'id': row[0], 'title': row[1], 'assignee': row[2],
            'priority': row[3], 'deadline': row[4], 'status': row[5],
            'author': row[6], 'note': row[8] if len(row) > 8 else '',
            'category': row[9] if len(row) > 9 else '',
            'department': row[10] if len(row) > 10 else '',
        }
        self._task_form(data)


def _task_form(self, existing):
    title = "Редагувати завдання" if existing else "Нове завдання"
    dlg = Modal(self.root, title, width=500, height=580)
    admin = current_user['role'] == 'admin'
    user_dept = current_user.get('department') or ''

    title_e = dlg.field("Назва завдання *",
                         default=existing.get('title', '') if existing else '')

    dept_vals = _all_departments()
    default_dept = (existing.get('department', '') if existing else user_dept)
    dv = dlg.combobox("Відділ *", dept_vals, default=default_dept or dept_vals[0])
    if not admin:
        dv.configure(state='disabled')

    assignee_vals = [w[1] for w in db_get_workers(dept_filter=default_dept or user_dept or 'Всі')]
    assignee_e = dlg.combobox("Відповідальний", [''] + assignee_vals,
                              default=existing.get('assignee', '') if existing else '')

    def on_dept_change(event=None):
        dept = dv.get().strip()
        workers = [w[1] for w in db_get_workers(dept_filter=dept or 'Всі')]
        assignee_e.configure(values=[''] + workers)

    if admin:
        dv.bind("<<ComboboxSelected>>", on_dept_change)

    deadline_e = dlg.field("Дедлайн (РРРР-ММ-ДД)",
                            default=existing.get('deadline', '') if existing else '')
    category_e = dlg.field("Категорія",
                            default=existing.get('category', '') if existing else '')

    pv = dlg.combobox("Пріоритет", PRIORITY_LEVELS,
                      default=existing.get('priority', 'Середня') if existing else 'Середня')

    sv = None
    if existing:
        sv = dlg.combobox("Статус", TASK_STATUSES,
                          default=existing.get('status', 'Активне'))

    note_t = dlg.textarea("Нотатки", default=existing.get('note', '') if existing else '')

    def submit():
        t = title_e.get().strip()
        if not t:
            dlg.error("Назва обов'язкова.")
            return
        dept = dv.get().strip() if admin else user_dept
        if not dept:
            dlg.error("Відділ обов'язковий.")
            return
        data = {
            'title':    t,
            'assignee': assignee_e.get().strip(),
            'priority': pv.get(),
            'deadline': deadline_e.get().strip(),
            'status':   sv.get() if sv else 'Активне',
            'author':   current_user['username'],
            'note':     note_t.get("1.0", "end-1c").strip(),
            'category': category_e.get().strip(),
            'department': dept,
        }
        if existing:
            db_update_task(existing['id'], data)
            log_action(f"редагував завдання: {t} [{dept}]")
        else:
            db_add_task(data)
            log_action(f"додав завдання: {t} [{dept}]")
        self.task_reload()
        dlg.win.destroy()

    dlg.add_ok("Зберегти", submit)
