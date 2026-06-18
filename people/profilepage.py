import tkinter as tk
from tkinter import messagebox
from main.uihelper import mk_label, mk_entry, mk_btn, mk_sep
from db.usersdb import db_update_profile, db_change_password, log_action
from db.current_user import current_user
from main.theme import C


def pg_profile(self):
    pad = tk.Frame(self.page, bg=C['bg'])
    pad.pack(fill="both", expand=True, padx=24, pady=20)
    pad.columnconfigure(0, weight=1)
    pad.columnconfigure(1, weight=1)

    # Left card — profile info
    info_card = tk.Frame(pad, bg=C['card'],
                         highlightthickness=1, highlightbackground=C['border'])
    info_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

    tk.Frame(info_card, bg=C['accent'], height=4).pack(fill="x")
    hdr = tk.Frame(info_card, bg=C['card'])
    hdr.pack(fill="x", padx=20, pady=(20, 0))
    tk.Label(hdr, text="Мій профіль", font=("Segoe UI", 14, "bold"),
             bg=C['card'], fg=C['text']).pack(anchor="w")
    tk.Label(hdr, text="Контактні дані та організація",
             font=("Segoe UI", 9), bg=C['card'], fg=C['muted']).pack(anchor="w", pady=(2, 0))
    mk_sep(info_card).pack(fill="x", padx=20, pady=(12, 0))

    frm = tk.Frame(info_card, bg=C['card'])
    frm.pack(fill="x", padx=20, pady=16)

    tk.Label(frm, text=f"Логін: {current_user['username']}",
             font=("Segoe UI", 10, "bold"), bg=C['card'], fg=C['text']).pack(anchor="w", pady=(0, 4))
    role_color = C['warn'] if current_user['role'] == 'admin' else C['muted']
    tk.Label(frm, text=f"Роль: {current_user['role'].upper()}",
             font=("Segoe UI", 9), bg=C['card'], fg=role_color).pack(anchor="w", pady=(0, 4))
    dept = current_user.get('department') or '—'
    tk.Label(frm, text=f"Відділ: {dept}",
             font=("Segoe UI", 9), bg=C['card'], fg=C['accent']).pack(anchor="w", pady=(0, 12))

    fields = {}
    for lbl, key in [("Номер телефону", "phone"), ("Email", "email"), ("Організація", "org")]:
        mk_label(frm, lbl).pack(anchor="w", pady=(6, 2))
        e = mk_entry(frm)
        e.insert(0, current_user.get(key, '') or '')
        e.pack(fill="x", ipady=8)
        fields[key] = e

    self._profile_msg = tk.Label(frm, text="", font=("Segoe UI", 9),
                                  bg=C['card'], fg=C['success'], wraplength=320)
    self._profile_msg.pack(pady=(8, 0))

    def save_profile():
        phone = fields['phone'].get().strip()
        email = fields['email'].get().strip()
        org   = fields['org'].get().strip()
        db_update_profile(current_user['id'], phone, email, org)
        current_user.update({'phone': phone, 'email': email, 'org': org})
        log_action("оновив профіль")
        self._profile_msg.config(text="Профіль збережено!", fg=C['success'])
        self._refresh_sidebar_user()

    mk_btn(frm, "Зберегти профіль", save_profile).pack(fill="x", ipady=3, pady=(12, 0))

    # Right card — change password
    pwd_card = tk.Frame(pad, bg=C['card'],
                        highlightthickness=1, highlightbackground=C['border'])
    pwd_card.grid(row=0, column=1, sticky="nsew")

    tk.Frame(pwd_card, bg=C['warn'], height=4).pack(fill="x")
    hdr2 = tk.Frame(pwd_card, bg=C['card'])
    hdr2.pack(fill="x", padx=20, pady=(20, 0))
    tk.Label(hdr2, text="Зміна пароля", font=("Segoe UI", 14, "bold"),
             bg=C['card'], fg=C['text']).pack(anchor="w")
    tk.Label(hdr2, text="Мінімум 4 символи",
             font=("Segoe UI", 9), bg=C['card'], fg=C['muted']).pack(anchor="w", pady=(2, 0))
    mk_sep(pwd_card).pack(fill="x", padx=20, pady=(12, 0))

    pwd_frm = tk.Frame(pwd_card, bg=C['card'])
    pwd_frm.pack(fill="x", padx=20, pady=16)

    pwd_fields = {}
    for lbl, key, show in [("Новий пароль", "new", "*"), ("Повторити пароль", "confirm", "*")]:
        mk_label(pwd_frm, lbl).pack(anchor="w", pady=(6, 2))
        e = mk_entry(pwd_frm, show=show)
        e.pack(fill="x", ipady=8)
        pwd_fields[key] = e

    self._pwd_msg = tk.Label(pwd_frm, text="", font=("Segoe UI", 9),
                              bg=C['card'], fg=C['danger'], wraplength=320)
    self._pwd_msg.pack(pady=(8, 0))

    def change_pwd():
        p1 = pwd_fields['new'].get()
        p2 = pwd_fields['confirm'].get()
        if len(p1) < 4:
            self._pwd_msg.config(text="Пароль мінімум 4 символи.", fg=C['danger'])
            return
        if p1 != p2:
            self._pwd_msg.config(text="Паролі не співпадають.", fg=C['danger'])
            return
        db_change_password(current_user['id'], p1)
        log_action("змінив пароль")
        pwd_fields['new'].delete(0, 'end')
        pwd_fields['confirm'].delete(0, 'end')
        self._pwd_msg.config(text="Пароль успішно змінено!", fg=C['success'])

    mk_btn(pwd_frm, "Змінити пароль", change_pwd, bg=C['warn']).pack(fill="x", ipady=3, pady=(12, 0))

    # Stats row
    stats_card = tk.Frame(pad, bg=C['card'],
                          highlightthickness=1, highlightbackground=C['border'])
    stats_card.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(16, 0))

    tk.Label(stats_card, text="Швидка інформація",
             font=("Segoe UI", 10, "bold"), bg=C['card'], fg=C['text']).pack(
        padx=20, pady=(14, 4), anchor="w")
    mk_sep(stats_card).pack(fill="x", padx=20)
    stats_body = tk.Frame(stats_card, bg=C['card'])
    stats_body.pack(fill="x", padx=20, pady=12)

    from main.task import db_get_time_sessions
    sessions = db_get_time_sessions(current_user['username'])
    total_sec = sum(s[3] or 0 for s in sessions)
    th, rem = divmod(total_sec, 3600)
    tm, _   = divmod(rem, 60)

    for lbl, val in [
        ("Сесій роботи", str(len(sessions))),
        ("Загальний час", f"{th}г {tm}хв"),
        ("Email", current_user.get('email') or '—'),
        ("Телефон", current_user.get('phone') or '—'),
    ]:
        r = tk.Frame(stats_body, bg=C['card'])
        r.pack(side="left", expand=True, fill="x", padx=8)
        tk.Label(r, text=val, font=("Segoe UI", 14, "bold"),
                 bg=C['card'], fg=C['accent']).pack()
        tk.Label(r, text=lbl, font=("Segoe UI", 8),
                 bg=C['card'], fg=C['muted']).pack()
