import tkinter as tk
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main.uihelper import mk_label, mk_entry, mk_btn, mk_sep
from login.lock import get_attempts, record_failed, reset_attempts, is_locked
from db.session import save_session, load_session
from db.current_user import set_current_user
from db.usersdb import db_login, db_login_by_username, log_action
from people.profile import ProfileWindow
from main.faq import FAQWindow
from main.theme import C
from main.main import CRMApp

class LoginWindow:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("CRM System — Вхід")
        self.win.geometry("420x540")
        self.win.configure(bg=C['white'])
        self.win.resizable(False, False)
        self._center()
        self._build()

        saved = load_session()
        if saved:
            user = db_login_by_username(saved)
            if user:
                set_current_user(user)
                self.win.after(150, self._auto_login)

        self.win.mainloop()

    def _center(self):
        self.win.update_idletasks()
        w, h = 420, 540
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _auto_login(self):
        log_action("автоматичний вхід (збережена сесія)")
        self.win.destroy()
        CRMApp()

    def _build(self):
        tk.Frame(self.win, bg=C['accent'], height=5).pack(fill="x")

        logo_frame = tk.Frame(self.win, bg=C['white'])
        logo_frame.pack(pady=(36, 0))
        tk.Label(logo_frame, text="CRM", font=("Segoe UI", 32, "bold"),
                 bg=C['white'], fg=C['accent']).pack()
        tk.Label(logo_frame, text="System", font=("Segoe UI", 11),
                 bg=C['white'], fg=C['muted']).pack()

        mk_sep(self.win).pack(fill="x", padx=40, pady=24)

        frm = tk.Frame(self.win, bg=C['white'])
        frm.pack(padx=40, fill="x")

        mk_label(frm, "Логін", size=9).pack(anchor="w")
        self.eu = mk_entry(frm)
        self.eu.pack(fill="x", ipady=9, pady=(3, 14))

        mk_label(frm, "Пароль", size=9).pack(anchor="w")
        self.ep = mk_entry(frm, show="*")
        self.ep.pack(fill="x", ipady=9, pady=(3, 14))

        self.remember = tk.BooleanVar(value=False)
        chk_frame = tk.Frame(frm, bg=C['white'])
        chk_frame.pack(fill="x", pady=(0, 20))
        tk.Checkbutton(chk_frame, text="Запам'ятати пристрій (30 днів)",
                       variable=self.remember,
                       font=("Segoe UI", 9), bg=C['white'], fg=C['text2'],
                       activebackground=C['white'], selectcolor=C['ibg'],
                       cursor="hand2").pack(anchor="w")

        mk_btn(frm, "Увійти", self.do_login).pack(fill="x", ipady=3)
        tk.Frame(frm, height=8, bg=C['white']).pack()
        mk_btn(frm, "Інструкція", self.open_faq,
               bg=C['ibg'], fg=C['text2']).pack(fill="x", ipady=3)

        self.msg = tk.Label(frm, text="", font=("Segoe UI", 9),
                            bg=C['white'], fg=C['danger'], wraplength=340)
        self.msg.pack(pady=(14, 0))

        self.ep.bind("<Return>", lambda e: self.do_login())
        self.eu.bind("<Return>", lambda e: self.ep.focus())
        self.eu.focus()

    def do_login(self):
        u = self.eu.get().strip()
        p = self.ep.get()
        if not u or not p:
            self.msg.config(text="Заповніть всі поля.")
            return

        locked, remaining = is_locked(u)
        if locked:
            mins = remaining // 60
            secs = remaining % 60
            self.msg.config(text=f"Акаунт заблоковано на {mins}хв {secs}с\n(Занадто багато невдалих спроб)")
            return

        user = db_login(u, p)
        if user:
            reset_attempts(u)
            set_current_user(user)
            if self.remember.get():
                save_session(u)
            log_action("увійшов у систему")
            self.win.destroy()
            ProfileWindow(on_done=lambda: CRMApp())
        else:
            record_failed(u)
            count, _ = get_attempts(u)
            left = max(0, 3 - count)
            if left == 0:
                self.msg.config(text="Акаунт заблоковано на 5 хвилин!")
            else:
                self.msg.config(text=f"Невірний логін або пароль.\nЗалишилось спроб: {left}")

    def open_faq(self):
        FAQWindow(self.win)