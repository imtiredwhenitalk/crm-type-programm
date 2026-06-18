import tkinter as tk
from tkinter import messagebox, filedialog
import csv

from main.uihelper import mk_label, mk_entry, mk_btn, make_tree
from db.usersdb import db_get_logs, log_action
from db.current_user import current_user
from main.theme import C


def pg_logs(self):
    bar = tk.Frame(self.page, bg=C['bg'])
    bar.pack(fill="x", padx=20, pady=(16, 8))

    tk.Label(bar, text="Журнал дій", font=("Segoe UI", 11, "bold"),
             bg=C['bg'], fg=C['text']).pack(side="left")

    right_f = tk.Frame(bar, bg=C['bg'])
    right_f.pack(side="right")

    is_admin = current_user['role'] == 'admin'
    hint = "Всі дії" if is_admin else "Ваші дії"
    tk.Label(right_f, text=hint, font=("Segoe UI", 8),
             bg=C['bg'], fg=C['muted']).pack(side="left", padx=(0, 12))

    mk_label(right_f, "Пошук:", size=9).pack(side="left", padx=(0, 4))
    self.log_search = tk.StringVar()
    e = mk_entry(right_f, width=20)
    e.configure(textvariable=self.log_search)
    e.pack(side="left", ipady=6)

    mk_btn(right_f, "Оновити",
           lambda: self._log_reload(),
           bg=C['ibg'], fg=C['text']).pack(side="left", padx=(8, 0))

    if is_admin:
        mk_btn(right_f, "Експорт CSV",
               lambda: self._export_logs(),
               bg=C['ibg'], fg=C['text']).pack(side="left", padx=(8, 0))

    pad = tk.Frame(self.page, bg=C['bg'])
    pad.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    pad.columnconfigure(0, weight=1)
    pad.rowconfigure(0, weight=1)

    self.log_tree = make_tree(pad, ["Час", "Користувач", "Дія"], [180, 140, 600])
    self.log_search.trace("w", lambda *a: self._log_reload())
    self._log_reload()


def _log_reload(self):
    if not hasattr(self, 'log_tree') or not self.log_tree:
        return
    search = self.log_search.get() if hasattr(self, 'log_search') else ''
    uname = None if current_user['role'] == 'admin' else current_user['username']
    for r in self.log_tree.get_children():
        self.log_tree.delete(r)
    for i, row in enumerate(db_get_logs(search, username=uname)):
        ts  = (row[0] or '')[:19].replace("T", " ")
        tag = "even" if i % 2 == 0 else "odd"
        self.log_tree.insert("", "end", values=(ts, row[1] or '', row[2] or ''), tags=(tag,))


def _export_logs(self):
    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV файл", "*.csv")],
        initialfile="logs_export.csv"
    )
    if not path:
        return
    rows = db_get_logs()
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(["Час", "Користувач", "Дія"])
        for row in rows:
            ts = (row[0] or '')[:19].replace("T", " ")
            w.writerow([ts, row[1] or '', row[2] or ''])
    log_action(f"експортував журнал у CSV")
    messagebox.showinfo("Готово", f"Журнал збережено:\n{path}")
