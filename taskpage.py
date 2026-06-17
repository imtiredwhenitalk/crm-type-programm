import tkinter as tk
from tkinter import ttk, messagebox
from uihelper import mk_label, mk_entry, mk_btn, make_tree
from modalbase import Modal
from task import db_get_tasks, db_add_task, db_update_task, db_delete_tasks, db_task_status, TASK_STATUSES, PRIORITY_LEVELS
from login import current_user
from crm import log_action
from theme import C
import db

def pg_tasks(self):
        bar   = tk.Frame(self.page, bg=C['bg'])
        bar.pack(fill="x", padx=20, pady=(16, 8))
        admin = current_user['role'] == 'admin'

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

        mk_label(right_f, "Пошук:", size=9).pack(side="left", padx=(0, 4))
        self.tsearch = tk.StringVar()
        self.tsearch.trace("w", lambda *a: self.task_reload())
        e = mk_entry(right_f, width=16)
        e.configure(textvariable=self.tsearch)
        e.pack(side="left", ipady=6)

        mk_label(right_f, "Фільтр:", size=9).pack(side="left", padx=(12, 4))
        self.tfilter = tk.StringVar(value="Всі")
        cb = ttk.Combobox(right_f, textvariable=self.tfilter,
                          values=["Всі"] + PRIORITY_LEVELS + TASK_STATUSES,
                          state="readonly", width=14, font=("Segoe UI", 9))
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self.task_reload())

        pad = tk.Frame(self.page, bg=C['bg'])
        pad.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        pad.columnconfigure(0, weight=1)
        pad.rowconfigure(0, weight=1)

        self.ttree = make_tree(pad,
                               ["#", "Назва", "Відповідальний", "Категорія", "Пріоритет", "Дедлайн", "Статус", "Автор"],
                               [40, 230, 150, 120, 100, 120, 100, 120])
        self.ttree.bind("<Double-1>", lambda e: self.task_edit())
        self.task_reload()

def task_reload(self):
        if not self.ttree:
            return
        filt   = self.tfilter.get() if self.tfilter else "Всі"
        search = self.tsearch.get() if hasattr(self, 'tsearch') and self.tsearch else ''
        for r in self.ttree.get_children():
            self.ttree.delete(r)
        for i, row in enumerate(db_get_tasks(filt, search)):
            done = row[5] == "Виконано"
            tag  = "done" if done else row[3]
            self.ttree.insert("", "end", iid=str(row[0]),
                              values=(row[0], row[1], row[2], row[8], row[3], row[4], row[5], row[6]),
                              tags=(tag,))

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
                'category': row[9] if len(row) > 9 else ''
            }
            self._task_form(data)

def _task_form(self, existing):
        title = "Редагувати завдання" if existing else "Нове завдання"
        dlg = Modal(self.root, title, width=500, height=540)

        title_e = dlg.field("Назва завдання *",
                             default=existing.get('title', '') if existing else '')
        assignee_e = dlg.field("Відповідальний",
                                default=existing.get('assignee', '') if existing else '')
        deadline_e = dlg.field("Дедлайн (РРРР-ММ-ДД)",
                                default=existing.get('deadline', '') if existing else '')
        category_e = dlg.field("Категорія",
                                default=existing.get('category', '') if existing else '')

        pv = dlg.combobox("Пріоритет", PRIORITY_LEVELS,
                          default=existing.get('priority', 'Середня') if existing else 'Середня')

        if existing:
            sv = dlg.combobox("Статус", TASK_STATUSES,
                              default=existing.get('status', 'Активне'))

        note_t = dlg.textarea("Нотатки", default=existing.get('note', '') if existing else '')

        def submit():
            t = title_e.get().strip()
            if not t:
                dlg.error("Назва обов'язкова.")
                return
            data = {
                'title':    t,
                'assignee': assignee_e.get().strip(),
                'priority': pv.get(),
                'deadline': deadline_e.get().strip(),
                'status':   sv.get() if existing else 'Активне',
                'author':   current_user['username'],
                'note':     note_t.get("1.0", "end-1c").strip(),
                'category': category_e.get().strip(),
            }
            if existing:
                db_update_task(existing['id'], data)
                log_action(f"редагував завдання: {t}")
            else:
                db_add_task(data)
                log_action(f"додав завдання: {t}")
            self.task_reload()
            dlg.win.destroy()

        dlg.add_ok("Зберегти", submit)
