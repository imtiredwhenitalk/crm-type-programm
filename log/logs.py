import tkinter as tk
from tkinter import messagebox, filedialog, mk_label , mk_entry, mk_btn, make_tree , tree
import csv
from crm import LOGS_DIR 
from main.uihelper import make_tree
from login import current_user
from main.theme import C
import logging
import os
from db import db_get_logs , log_search

os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def pg_logs(self):
        bar = tk.Frame(self.page, bg=C['bg'])
        bar.pack(fill="x", padx=20, pady=(16, 8))

        tk.Label(bar, text="Журнал дій", font=("Segoe UI", 11, "bold"),
                 bg=C['bg'], fg=C['text']).pack(side="left")

        right_f = tk.Frame(bar, bg=C['bg'])
        right_f.pack(side="right")
        mk_label(right_f, "Пошук:", size=9).pack(side="left", padx=(0, 4))
        log_search = tk.StringVar()
        e = mk_entry(right_f, width=20)
        e.configure(textvariable=log_search)
        e.pack(side="left", ipady=6)

        mk_btn(right_f, "Оновити",
               lambda: log_reload(),
               bg=C['ibg'], fg=C['text']).pack(side="left", padx=(8, 0))

        if current_user['role'] == 'admin':
            mk_btn(right_f, "Експорт CSV",
                   lambda: self._export_logs(),
                   bg=C['ibg'], fg=C['text']).pack(side="left", padx=(8, 0))

        pad = tk.Frame(self.page, bg=C['bg'])
        pad.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        pad.columnconfigure(0, weight=1)
        pad.rowconfigure(0, weight=1)

        tree = make_tree(pad, ["Час", "Користувач", "Дія"], [180, 140, 600])

def log_reload():
            for r in tree.get_children():
                tree.delete(r)
            for i, row in enumerate(db_get_logs(log_search.get())):
                ts  = (row[0] or '')[:19].replace("T", " ")
                tag = "even" if i % 2 == 0 else "odd"
                tree.insert("", "end", values=(ts, row[1] or '', row[2] or ''), tags=(tag,))

            log_search.trace("w", lambda *a: log_reload())
            log_reload()

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
        messagebox.showinfo("Готово", f"Журнал збережено:\n{path}")
