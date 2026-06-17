import csv
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from main.uihelper import mk_label, mk_entry, mk_btn,make_tree
from db.modalbase import Modal
from db.usersdb import db_get_workers, db_delete_workers, db_add_worker, db_update_worker, db_get_departments, db_worker_stats
from login import current_user
from crm import log_action
from main.theme import C
from db import db
from tkinter import ttk
from db.workersdb import DEPARTMENTS

def pg_workers(self):
        nb = ttk.Notebook(self.page)
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        tab_list  = tk.Frame(nb, bg=C['bg'])
        tab_stats = tk.Frame(nb, bg=C['bg'])
        nb.add(tab_list,  text="  Список  ")
        nb.add(tab_stats, text="  Статистика  ")

        self._workers_list(tab_list)
        self._workers_stats(tab_stats)

def _workers_list(self, parent):
        bar   = tk.Frame(parent, bg=C['bg'])
        bar.pack(fill="x", padx=20, pady=(16, 8))
        admin = current_user['role'] == 'admin'

        left_btns = tk.Frame(bar, bg=C['bg'])
        left_btns.pack(side="left")

        if admin:
            mk_btn(left_btns, "Додати працівника", self.worker_add).pack(side="left")
            mk_btn(left_btns, "Редагувати", self.worker_edit,
                   bg=C['warn']).pack(side="left", padx=(8, 0))
            mk_btn(left_btns, "Видалити", self.worker_del,
                   bg=C['danger']).pack(side="left", padx=(8, 0))

        mk_btn(left_btns, "Експорт CSV", self.worker_export_csv,
               bg=C['ibg'], fg=C['text']).pack(side="left", padx=(8, 0))

        # Right side: filters
        right_f = tk.Frame(bar, bg=C['bg'])
        right_f.pack(side="right")

        mk_label(right_f, "Пошук:", size=9).pack(side="left", padx=(0, 4))
        self.wsearch = tk.StringVar()
        self.wsearch.trace("w", lambda *a: self.worker_reload())
        e = mk_entry(right_f, width=18)
        e.configure(textvariable=self.wsearch)
        e.pack(side="left", ipady=6)

        mk_label(right_f, "Статус:", size=9).pack(side="left", padx=(12, 4))
        self.w_status_var = tk.StringVar(value='Всі')
        cb_s = ttk.Combobox(right_f, textvariable=self.w_status_var,
                             values=['Всі', 'Активний', 'Звільнений', 'Відпустка'],
                             state="readonly", width=12, font=("Segoe UI", 9))
        cb_s.pack(side="left")
        cb_s.bind("<<ComboboxSelected>>", lambda e: self.worker_reload())

        pad = tk.Frame(parent, bg=C['bg'])
        pad.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        pad.columnconfigure(0, weight=1)
        pad.rowconfigure(0, weight=1)

        self.wtree = make_tree(pad,
                               ["#", "Ім'я", "Посада", "Відділ", "Статус", "Зарплата", "Дата найму", "Телефон", "Email"],
                               [40, 180, 140, 140, 90, 110, 120, 130, 160])
        self.wtree.bind("<Double-1>", lambda e: self.worker_edit())
        self.worker_reload()

def worker_reload(self):
        if not self.wtree:
            return
        q  = self.wsearch.get() if hasattr(self, 'wsearch') and self.wsearch else ''
        st = self.w_status_var.get() if hasattr(self, 'w_status_var') else ''
        rows = db_get_workers(q, status_filter=st)
        for r in self.wtree.get_children():
            self.wtree.delete(r)
        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            sal = f"{row[3]:,.0f} грн" if row[3] else ""
            self.wtree.insert("", "end", iid=str(row[0]),
                              values=(row[0], row[1], row[7], row[2], row[9], sal, row[4], row[5], row[6]),
                              tags=(tag,))

def worker_del(self):
        sel = self.wtree.selection()
        if not sel:
            messagebox.showwarning("Увага", "Виберіть рядок.")
            return
        if not messagebox.askyesno("Підтвердження", f"Видалити {len(sel)} працівника(ів)?"):
            return
        ids = [int(s) for s in sel]
        db_delete_workers(ids)
        log_action(f"видалив працівників id={ids}")
        self.worker_reload()

def worker_add(self):
        self._worker_form(None)

def worker_edit(self):
        sel = self.wtree.selection()
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
                'position': row[7], 'note': row[8], 'status': row[9] if len(row) > 9 else 'Активний'
            }
            self._worker_form(data)

def _worker_form(self, existing):
        title = "Редагувати працівника" if existing else "Новий працівник"
        dlg = Modal(self.root, title, width=600, height=750)

        entries = {}
        fields = [
            ("Ім'я *",       "name"),
            ("Посада",        "position"),
            ("Дата найму",    "hire_date"),
            ("Телефон",       "phone"),
            ("Email",         "email"),
        ]
        for lbl, key in fields:
            entries[key] = dlg.field(lbl, default=str(existing.get(key, '') or '') if existing else '')

        mk_label(dlg.body, "Відділ", size=9).pack(anchor="w", pady=(8, 2))
        dept_vals = DEPARTMENTS + db_get_departments()
        dept_vals = list(dict.fromkeys(dept_vals))  # dedupe
        dept_var = tk.StringVar(value=(existing.get('department', '') if existing else ''))
        dept_cb = ttk.Combobox(dlg.body, textvariable=dept_var,
                               values=dept_vals, font=("Segoe UI", 10))
        dept_cb.pack(fill="x", ipady=5)
        entries['department'] = dept_cb

        mk_label(dlg.body, "Статус", size=9).pack(anchor="w", pady=(8, 2))
        status_var = tk.StringVar(value=(existing.get('status', 'Активний') if existing else 'Активний'))
        status_cb = ttk.Combobox(dlg.body, textvariable=status_var,
                                 values=['Активний', 'Звільнений', 'Відпустка'],
                                 state="readonly", font=("Segoe UI", 10))
        status_cb.pack(fill="x", ipady=5)

        mk_label(dlg.body, "Зарплата (грн)", size=9).pack(anchor="w", pady=(8, 2))
        sal_e = mk_entry(dlg.body)
        if existing and existing.get('salary'):
            sal_e.insert(0, str(existing['salary']))
        sal_e.pack(fill="x", ipady=7)

        note_t = dlg.textarea("Нотатки", default=existing.get('note', '') if existing else '')

        def submit():
            name = entries['name'].get().strip()
            if not name:
                dlg.error("Ім'я обов'язкове.")
                return
            try:
                sal = float(sal_e.get().replace(',', '.') or 0)
            except ValueError:
                dlg.error("Зарплата повинна бути числом.")
                return
            data = {
                'name':       name,
                'position':   entries['position'].get().strip(),
                'department': dept_var.get().strip(),
                'salary':     sal,
                'hire_date':  entries['hire_date'].get().strip(),
                'phone':      entries['phone'].get().strip(),
                'email':      entries['email'].get().strip(),
                'note':       note_t.get("1.0", "end-1c").strip(),
                'status':     status_var.get(),
            }
            if existing:
                db_update_worker(existing['id'], data)
                log_action(f"редагував працівника: {name}")
            else:
                db_add_worker(data)
                log_action(f"додав працівника: {name}")
            self.worker_reload()
            dlg.win.destroy()

        dlg.add_ok("Зберегти", submit)

def worker_export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файл", "*.csv")],
            initialfile="workers_export.csv"
        )
        if not path:
            return
        rows = db_get_workers()
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(["ID", "Ім'я", "Відділ", "Зарплата", "Дата найму",
                        "Телефон", "Email", "Посада", "Нотатки", "Статус"])
            for row in rows:
                w.writerow(row)
        log_action(f"експортував працівників у CSV: {path}")
        messagebox.showinfo("Готово", f"Файл збережено:\n{path}")

def _workers_stats(self, parent):
        pad = tk.Frame(parent, bg=C['bg'])
        pad.pack(fill="both", expand=True, padx=20, pady=16)
        pad.columnconfigure(0, weight=1)
        pad.rowconfigure(1, weight=1)

        tk.Label(pad, text="Статистика за відділами",
                 font=("Segoe UI", 12, "bold"),
                 bg=C['bg'], fg=C['text']).grid(row=0, column=0, sticky="w", pady=(0, 12))

        tree = make_tree(pad,
                         ["Відділ", "Кількість", "Сер. зарплата", "Фонд ЗП", "% від загального"],
                         [240, 100, 160, 160, 140])

        rows, total = db_worker_stats()
        total_fund = total[2] or 1
        for i, row in enumerate(rows):
            dept  = row[0] or "(без відділу)"
            count = row[1]
            avg   = f"{row[2]:,.0f} грн" if row[2] else "—"
            fund  = f"{row[3]:,.0f} грн" if row[3] else "—"
            pct   = f"{row[3]/total_fund*100:.1f}%" if row[3] else "—"
            tag   = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=(dept, count, avg, fund, pct), tags=(tag,))

        if total:
            tree.insert("", "end", values=(
                "ВСЬОГО",
                total[0],
                f"{total[1]:,.0f} грн" if total[1] else "—",
                f"{total[2]:,.0f} грн" if total[2] else "—",
                "100%",
            ), tags=("Висока",))
