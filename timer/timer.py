from tkinter import ttk
import tkinter as tk
from tkinter import messagebox
import datetime

from main.uihelper import make_tree
from main.task import db_get_time_sessions, db_save_time_session
from db.current_user import current_user
from db.usersdb import log_action
from main.theme import C


def pg_timer(self):
    nb = ttk.Notebook(self.page)
    nb.pack(fill="both", expand=True)
    tab_timer = tk.Frame(nb, bg=C['bg'])
    tab_hist  = tk.Frame(nb, bg=C['bg'])
    nb.add(tab_timer, text="  Таймер  ")
    nb.add(tab_hist,  text="  Історія сесій  ")
    self._timer_main(tab_timer)
    self._timer_history(tab_hist)


def _timer_main(self, parent):
    f = tk.Frame(parent, bg=C['bg'])
    f.place(relx=0.5, rely=0.45, anchor="center")

    card = tk.Frame(f, bg=C['card'],
                    highlightthickness=1, highlightbackground=C['border'])
    card.pack(padx=40, pady=20, ipadx=50, ipady=30)

    tk.Label(card, text="Робочий час",
             font=("Segoe UI", 11), bg=C['card'], fg=C['muted']).pack(pady=(20, 4))
    self.tlabel = tk.Label(card, text="00:00:00",
                           font=("Courier New", 56, "bold"),
                           bg=C['card'], fg=C['text'])
    self.tlabel.pack(pady=(0, 24))

    self.tbtn = tk.Button(card, text="Почати роботу",
                          font=("Segoe UI", 12, "bold"),
                          bg=C['success'], fg='white',
                          relief="flat", bd=0,
                          padx=48, pady=14, cursor="hand2",
                          command=self.toggle_work)
    self.tbtn.pack(pady=(0, 12))

    self.tstatus = tk.Label(card, text="",
                            font=("Segoe UI", 9), bg=C['card'], fg=C['muted'])
    self.tstatus.pack(pady=(0, 20))


def _timer_history(self, parent):
    pad = tk.Frame(parent, bg=C['bg'])
    pad.pack(fill="both", expand=True, padx=20, pady=16)
    pad.columnconfigure(0, weight=1)
    pad.rowconfigure(1, weight=1)

    bar = tk.Frame(pad, bg=C['bg'])
    bar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    tk.Label(bar, text="Мої сесії роботи", font=("Segoe UI", 11, "bold"),
             bg=C['bg'], fg=C['text']).pack(side="left")

    tree = make_tree(pad,
                     ["Початок", "Кінець", "Тривалість"],
                     [200, 200, 200])
    tree.grid(row=1, column=0, sticky="nsew")

    sessions = db_get_time_sessions(current_user['username'])
    for i, row in enumerate(sessions):
        started = (row[1] or '')[:19].replace("T", " ")
        ended   = (row[2] or '')[:19].replace("T", " ")
        dur_s   = row[3] or 0
        h, rem  = divmod(dur_s, 3600)
        m, s    = divmod(rem, 60)
        dur_str = f"{h}г {m}хв {s}с"
        tag = "even" if i % 2 == 0 else "odd"
        tree.insert("", "end", values=(started, ended, dur_str), tags=(tag,))


def toggle_work(self):
    if not self.working:
        self.work_start = datetime.datetime.now()
        self.working    = True
        if self.tbtn:
            self.tbtn.config(text="Завершити роботу", bg=C['danger'])
        if self.tstatus:
            self.tstatus.config(text=f"Розпочато: {self.work_start.strftime('%H:%M:%S')}")
        log_action("почав роботу")
    else:
        h, m, s = self._elapsed()
        ended = datetime.datetime.now()
        duration = int((ended - self.work_start).total_seconds())
        db_save_time_session(
            current_user['username'],
            self.work_start.isoformat(),
            ended.isoformat(),
            duration
        )
        messagebox.showinfo("Час роботи",
                            f"Відпрацьовано: {h} год {m} хв {s} сек")
        log_action(f"завершив роботу ({h}г {m}хв {s}с)")
        self.working    = False
        self.work_start = None
        for widget, cfg in [
            (self.tlabel,  {"text": "00:00:00"}),
            (self.tbtn,    {"text": "Почати роботу", "bg": C['success']}),
            (self.tstatus, {"text": ""}),
        ]:
            if widget:
                try:
                    widget.config(**cfg)
                except tk.TclError:
                    pass


def _elapsed(self):
    diff   = datetime.datetime.now() - self.work_start
    h, rem = divmod(int(diff.total_seconds()), 3600)
    m, s   = divmod(rem, 60)
    return h, m, s


def _tick(self):
    if self.working and self.work_start and self.tlabel:
        h, m, s = self._elapsed()
        try:
            self.tlabel.config(text=f"{h:02}:{m:02}:{s:02}")
        except tk.TclError:
            pass
    self.root.after(1000, self._tick)
