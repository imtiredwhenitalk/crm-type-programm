import tkinter as tk
from uihelper import mk_label, mk_entry, mk_btn, mk_sep
from usersdb import db_update_profile
from login import current_user
from crm import log_action
from theme import C

class ProfileWindow:
    def __init__(self, on_done):
        self.on_done = on_done
        self.win = tk.Tk()
        self.win.title("Профіль")
        self.win.geometry("440x430")
        self.win.configure(bg=C['white'])
        self.win.resizable(False, False)
        self._center()
        self._build()
        self.win.mainloop()

    def _center(self):
        self.win.update_idletasks()
        w, h = 440, 430
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        tk.Frame(self.win, bg=C['accent'], height=4).pack(fill="x")

        tk.Label(self.win, text=f"Вітаємо, {current_user['username']}",
                 font=("Segoe UI", 16, "bold"),
                 bg=C['white'], fg=C['text']).pack(pady=(28, 4))
        tk.Label(self.win, text="Заповніть дані профілю (необов'язково)",
                 font=("Segoe UI", 10), bg=C['white'], fg=C['muted']).pack()
        mk_sep(self.win).pack(fill="x", padx=36, pady=(16, 0))

        frm = tk.Frame(self.win, bg=C['white'])
        frm.pack(padx=36, fill="x", pady=16)
        self.fields = {}
        for lbl, key in [("Номер телефону", "phone"), ("Email", "email"), ("Організація", "org")]:
            mk_label(frm, lbl).pack(anchor="w", pady=(6, 2))
            e = mk_entry(frm)
            e.insert(0, current_user.get(key, ''))
            e.pack(fill="x", ipady=8)
            self.fields[key] = e

        tk.Frame(frm, height=10, bg=C['white']).pack()
        mk_btn(frm, "Зберегти і продовжити", self.save).pack(fill="x", ipady=3)
        tk.Frame(frm, height=6, bg=C['white']).pack()
        mk_btn(frm, "Пропустити", self.skip, bg=C['ibg'], fg=C['text2']).pack(fill="x", ipady=3)

    def save(self):
        phone = self.fields['phone'].get().strip()
        email = self.fields['email'].get().strip()
        org   = self.fields['org'].get().strip()
        db_update_profile(current_user['id'], phone, email, org)
        current_user.update({'phone': phone, 'email': email, 'org': org})
        log_action("оновив профіль")
        self.win.destroy()
        self.on_done()

    def skip(self):
        self.win.destroy()
        self.on_done()
