import tkinter as tk
import db 

from tkinter import ttk, messagebox , mk_btn, make_tree , mk_sep
from login import LoginWindow, current_user
from theme import C
from uihelper import make_tree
from logs import log_action
from task import db_get_tasks, db_delete_tasks, TASK_STATUSES, PRIORITY_LEVELS
from modalbase import Modal
from usersdb import db_get_users, db_create_user, db_set_role, db_delete_user
from workersdb import db_get_workers, db_delete_workers
from task import db_get_tasks, db_delete_tasks, db_task_status
from session import clear_session , db_get_time_sessions

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
        mk_btn(bar, "Зробити адміном",
               lambda: self._au_role(utree_h[0], 'admin'),
               bg=C['warn']).pack(side="left", padx=(8, 0))
        mk_btn(bar, "Зробити user",
               lambda: self._au_role(utree_h[0], 'user'),
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
                         ["ID", "Логін", "Роль", "Телефон", "Email", "Організація", "Реєстрація", "Останній вхід"],
                         [40, 140, 70, 120, 180, 150, 155, 155])
        utree_h[0] = tree
        self._au_reload(tree)

def _create_user_dialog(self, tree):
        dlg = Modal(self.root, "Створити користувача", width=440, height=380)

        eu = dlg.field("Логін *")
        ep = dlg.field("Пароль *", show="*")
        ep2 = dlg.field("Повторити пароль *", show="*")
        rv = dlg.combobox("Роль", ["user", "admin"], default="user")

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
            if db_create_user(u, p, rv.get()):
                log_action(f"(адмін) створив юзера: {u} роль={rv.get()}")
                self._au_reload(tree)
                dlg.win.destroy()
            else:
                dlg.error("Логін вже зайнятий.")

        dlg.add_ok("Створити", submit)

def _au_reload(self, tree):
        if not tree:
            return
        for r in tree.get_children():
            tree.delete(r)
        for i, row in enumerate(db_get_users()):
            ts   = (row[6] or '')[:19].replace("T", " ")
            last = (row[7] or '')[:19].replace("T", " ")
            tag  = "admin" if row[2] == 'admin' else ("even" if i % 2 == 0 else "odd")
            tree.insert("", "end", iid=str(row[0]),
                        values=(row[0], row[1], row[2], row[3] or '', row[4] or '',
                                row[5] or '', ts, last),
                        tags=(tag,))

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
        bar = tk.Frame(parent, bg=C['bg'])
        bar.pack(fill="x", padx=20, pady=(16, 8))
        mk_btn(bar, "Додати", self.worker_add).pack(side="left")
        mk_btn(bar, "Редагувати",
               lambda: self._aw_edit(wh[0]),
               bg=C['warn']).pack(side="left", padx=(8, 0))
        mk_btn(bar, "Видалити",
               lambda: self._aw_delete(wh[0]),
               bg=C['danger']).pack(side="left", padx=(8, 0))

        pad = tk.Frame(parent, bg=C['bg'])
        pad.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        pad.columnconfigure(0, weight=1)
        pad.rowconfigure(0, weight=1)

        tree = make_tree(pad,
                         ["#", "Ім'я", "Посада", "Відділ", "Статус", "Зарплата", "Дата найму"],
                         [40, 200, 140, 150, 90, 120, 130])
        wh[0] = tree
        for i, row in enumerate(db_get_workers()):
            sal = f"{row[3]:,.0f} грн" if row[3] else ""
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", iid=str(row[0]),
                        values=(row[0], row[1], row[7], row[2], row[9] if len(row)>9 else '', sal, row[4]),
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

        pad = tk.Frame(parent, bg=C['bg'])
        pad.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        pad.columnconfigure(0, weight=1)
        pad.rowconfigure(0, weight=1)

        tree = make_tree(pad,
                         ["#", "Назва", "Відповідальний", "Пріоритет", "Дедлайн", "Статус", "Автор"],
                         [40, 230, 150, 100, 120, 100, 120])
        th[0] = tree
        for i, row in enumerate(db_get_tasks()):
            done = row[5] == "Виконано"
            tag  = "done" if done else row[3]
            tree.insert("", "end", iid=str(row[0]),
                        values=(row[0], row[1], row[2], row[3], row[4], row[5], row[6]),
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
            vals[5] = status
            tag = "done" if status == "Виконано" else vals[3]
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

        # Time sessions summary
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

        # Recent sessions table
        tk.Label(pad, text="Останні сесії роботи",
                 font=("Segoe UI", 10, "bold"),
                 bg=C['bg'], fg=C['text']).pack(anchor="w", pady=(8, 6))

        sess_frame = tk.Frame(pad, bg=C['bg'])
        sess_frame.pack(fill="x")
        sess_tree = make_tree(sess_frame,
                              ["Користувач", "Початок", "Кінець", "Тривалість"],
                              [150, 180, 180, 180])
        sess_tree.configure(height=min(10, len(sessions)))

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

def logout(self):
        if not messagebox.askyesno("Вихід", "Вийти з системи?"):
            return
        clear_session()
        log_action("вийшов з системи")
        self.root.destroy()
        LoginWindow()

