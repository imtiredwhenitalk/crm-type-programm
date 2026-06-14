import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import logging
import hashlib
import sqlite3
import json
import os


BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR    = os.path.join(BASE_DIR, 'logs')
DATA_DIR    = os.path.join(BASE_DIR, 'data')
LOG_FILE    = os.path.join(LOGS_DIR, 'crm_log.txt')
WORKER_FILE = os.path.join(DATA_DIR, 'worker.json')
TASK_FILE   = os.path.join(DATA_DIR, 'tasks.json')
DB_PATH     = os.path.join(BASE_DIR, 'crm.db')

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

current_user    = None
PRIORITY_LEVELS = ['Критична', 'Висока', 'Середня', 'Низька']

C = {
    'bg':      '#f0f2f5',
    'sidebar': '#1a1a2e',
    'side2':   '#2a2a4e',
    'white':   '#ffffff',
    'text':    '#1a1a1a',
    'muted':   '#aaaaaa',
    'ibg':     '#f5f5f5',
    'sep':     '#eeeeee',
    'accent':  '#3a5bd5',
    'danger':  '#e74c3c',
    'success': '#2ecc71',
    'warn':    '#e67e22',
}


def db():
    return sqlite3.connect(DB_PATH)


def db_init():
    conn = db()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role     TEXT DEFAULT "user",
            phone    TEXT DEFAULT "",
            email    TEXT DEFAULT "",
            org      TEXT DEFAULT "",
            created  TEXT
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username  TEXT,
            action    TEXT
        )
    ''')

    existing_cols = [r[1] for r in conn.execute('PRAGMA table_info(users)').fetchall()]
    for col, default in [('phone','""'), ('email','""'), ('org','""')]:
        if col not in existing_cols:
            conn.execute(f'ALTER TABLE users ADD COLUMN {col} TEXT DEFAULT {default}')

    log_cols = [r[1] for r in conn.execute('PRAGMA table_info(logs)').fetchall()]
    if 'username' not in log_cols:
        conn.execute('ALTER TABLE logs ADD COLUMN username TEXT')

    admin_exists = conn.execute(
        'SELECT id FROM users WHERE username="admin"'
    ).fetchone()
    if not admin_exists:
        conn.execute(
            'INSERT INTO users (username, password, role, created) VALUES (?,?,?,?)',
            ('admin', hashlib.sha256(b'admin').hexdigest(), 'admin',
             datetime.datetime.now().isoformat())
        )

    conn.commit()
    conn.close()


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def db_login(username, password):
    conn = db()
    row = conn.execute(
        'SELECT id,username,role,phone,email,org FROM users WHERE username=? AND password=?',
        (username, hash_pw(password))
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {'id': row[0], 'username': row[1], 'role': row[2],
            'phone': row[3] or '', 'email': row[4] or '', 'org': row[5] or ''}


def db_register(username, password):
    try:
        conn = db()
        conn.execute(
            'INSERT INTO users (username,password,role,created) VALUES (?,?,?,?)',
            (username, hash_pw(password), 'user', datetime.datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def db_update_profile(uid, phone, email, org):
    conn = db()
    conn.execute('UPDATE users SET phone=?,email=?,org=? WHERE id=?',
                 (phone, email, org, uid))
    conn.commit()
    conn.close()


def db_get_users():
    conn = db()
    rows = conn.execute(
        'SELECT id,username,role,phone,email,org,created FROM users ORDER BY id'
    ).fetchall()
    conn.close()
    return rows


def db_set_role(uid, role):
    conn = db()
    conn.execute('UPDATE users SET role=? WHERE id=?', (role, uid))
    conn.commit()
    conn.close()


def db_delete_user(uid):
    conn = db()
    conn.execute('DELETE FROM users WHERE id=?', (uid,))
    conn.commit()
    conn.close()


def db_get_logs():
    conn = db()
    rows = conn.execute(
        'SELECT timestamp,username,action FROM logs ORDER BY timestamp DESC LIMIT 300'
    ).fetchall()
    conn.close()
    return rows


def log_action(action):
    uname = current_user['username'] if current_user else 'system'
    now   = datetime.datetime.now()
    logging.info(f"{uname} - {action}")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{now} - {uname} - {action}\n")
    conn = db()
    conn.execute('INSERT INTO logs (timestamp,username,action) VALUES (?,?,?)',
                 (now.isoformat(), uname, action))
    conn.commit()
    conn.close()


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_workers():  return load_json(WORKER_FILE)
def save_workers(w): save_json(WORKER_FILE, w)
def load_tasks():    return load_json(TASK_FILE)
def save_tasks(t):   save_json(TASK_FILE, t)


def next_id(items):
    return (max((x.get('id', 0) for x in items), default=0)) + 1


def entry(parent, show=None):
    return tk.Entry(parent, font=("Arial", 11), relief="flat",
                    bg=C['ibg'], fg=C['text'],
                    insertbackground=C['text'], show=show or '')


def label(parent, text, size=9, color=None, bold=False):
    font = ("Arial", size, "bold") if bold else ("Arial", size)
    return tk.Label(parent, text=text, font=font,
                    bg=parent.cget('bg'), fg=color or C['muted'])


def btn(parent, text, cmd, bg=None, fg='white', padx=16, pady=10):
    return tk.Button(parent, text=text, command=cmd,
                     font=("Arial", 10, "bold"),
                     bg=bg or C['accent'], fg=fg,
                     relief="flat", bd=0,
                     padx=padx, pady=pady,
                     cursor="hand2",
                     activebackground=C['side2'],
                     activeforeground='white')


def make_tree(parent, columns, widths):
    st = ttk.Style()
    st.theme_use("clam")
    st.configure("T.Treeview",
                 background=C['white'], foreground=C['text'],
                 rowheight=36, fieldbackground=C['white'],
                 font=("Arial", 10), borderwidth=0)
    st.configure("T.Treeview.Heading",
                 background=C['ibg'], foreground='#888',
                 font=("Arial", 9, "bold"), relief="flat")
    st.map("T.Treeview",
           background=[("selected", "#eef2ff")],
           foreground=[("selected", C['sidebar'])])
    st.layout("T.Treeview", [('T.Treeview.treearea', {'sticky': 'nswe'})])

    wrap = tk.Frame(parent, bg=C['white'])
    wrap.pack(fill="both", expand=True)

    tree = ttk.Treeview(wrap, columns=columns, show="headings", style="T.Treeview")
    vsb  = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    for col, w in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, minwidth=40, anchor="w")

    tree.tag_configure("even",     background=C['white'])
    tree.tag_configure("odd",      background="#fafafa")
    tree.tag_configure("done",     foreground=C['muted'])
    tree.tag_configure("Критична", foreground=C['danger'])
    tree.tag_configure("Висока",   foreground=C['warn'])
    tree.tag_configure("Середня",  foreground="#c0920a")
    tree.tag_configure("Низька",   foreground=C['success'])

    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return tree


def tree_fill(tree, rows, tag_fn=None):
    for r in tree.get_children():
        tree.delete(r)
    for i, row in enumerate(rows):
        iid  = str(row[0]) if row else str(i)
        base = "even" if i % 2 == 0 else "odd"
        tag  = tag_fn(row) if tag_fn else base
        tree.insert("", "end", iid=iid, values=row, tags=(tag,))


class LoginWindow:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("CRM — Вхiд")
        self.win.geometry("380x480")
        self.win.configure(bg=C['white'])
        self.win.resizable(False, False)
        self._build()
        self.win.mainloop()

    def _build(self):
        tk.Frame(self.win, bg=C['sidebar'], height=6).pack(fill="x")

        tk.Label(self.win, text="CRM System",
                 font=("Arial", 24, "bold"),
                 bg=C['white'], fg=C['sidebar']).pack(pady=(40, 4))
        tk.Label(self.win, text="Увiйдiть або зареєструйтесь",
                 font=("Arial", 10),
                 bg=C['white'], fg=C['muted']).pack(pady=(0, 28))

        frm = tk.Frame(self.win, bg=C['white'])
        frm.pack(padx=40, fill="x")

        label(frm, "Логiн").pack(anchor="w")
        self.eu = entry(frm)
        self.eu.pack(fill="x", ipady=8, pady=(2, 14))

        label(frm, "Пароль").pack(anchor="w")
        self.ep = entry(frm, show="*")
        self.ep.pack(fill="x", ipady=8, pady=(2, 22))

        btn(frm, "Увiйти", self.do_login).pack(fill="x", pady=(0, 8))
        btn(frm, "Зареєструватись", self.do_reg,
            bg=C['ibg'], fg=C['text']).pack(fill="x")

        self.msg = tk.Label(frm, text="", font=("Arial", 9),
                            bg=C['white'], fg=C['danger'])
        self.msg.pack(pady=(10, 0))

    def do_login(self):
        u, p = self.eu.get().strip(), self.ep.get()
        if not u or not p:
            self.msg.config(text="Заповнiть всi поля.")
            return
        user = db_login(u, p)
        if user:
            global current_user
            current_user = user
            log_action("увiйшов у систему")
            self.win.destroy()
            ProfileWindow(on_done=lambda: CRMApp())
        else:
            self.msg.config(text="Невiрний логiн або пароль.")

    def do_reg(self):
        u, p = self.eu.get().strip(), self.ep.get()
        if not u or not p:
            self.msg.config(text="Заповнiть всi поля.")
            return
        if len(p) < 4:
            self.msg.config(text="Пароль мiнiмум 4 символи.")
            return
        if db_register(u, p):
            self.msg.config(fg=C['success'], text="Акаунт створено. Увiйдiть.")
        else:
            self.msg.config(fg=C['danger'], text="Логiн вже зайнятий.")


class ProfileWindow:
    def __init__(self, on_done):
        self.on_done = on_done
        self.win = tk.Tk()
        self.win.title("Профiль")
        self.win.geometry("400x400")
        self.win.configure(bg=C['white'])
        self.win.resizable(False, False)
        self._build()
        self.win.mainloop()

    def _build(self):
        tk.Frame(self.win, bg=C['sidebar'], height=6).pack(fill="x")

        tk.Label(self.win, text=f"Вiтаємо, {current_user['username']}",
                 font=("Arial", 16, "bold"),
                 bg=C['white'], fg=C['sidebar']).pack(pady=(28, 4))
        tk.Label(self.win, text="Заповнiть данi профiлю (необов'язково)",
                 font=("Arial", 10),
                 bg=C['white'], fg=C['muted']).pack(pady=(0, 18))

        frm = tk.Frame(self.win, bg=C['white'])
        frm.pack(padx=36, fill="x")

        self.fields = {}
        for lbl, key in [("Номер телефону", "phone"),
                         ("Email",          "email"),
                         ("Органiзацiя",    "org")]:
            label(frm, lbl).pack(anchor="w")
            e = entry(frm)
            e.insert(0, current_user.get(key, ''))
            e.pack(fill="x", ipady=7, pady=(2, 12))
            self.fields[key] = e

        btn(frm, "Зберегти i продовжити", self.save).pack(fill="x", pady=(8, 6))
        btn(frm, "Пропустити", self.skip,
            bg=C['ibg'], fg=C['text']).pack(fill="x")

    def save(self):
        phone = self.fields['phone'].get().strip()
        email = self.fields['email'].get().strip()
        org   = self.fields['org'].get().strip()
        db_update_profile(current_user['id'], phone, email, org)
        current_user.update({'phone': phone, 'email': email, 'org': org})
        log_action("оновив профiль")
        self.win.destroy()
        self.on_done()

    def skip(self):
        self.win.destroy()
        self.on_done()


class CRMApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CRM System")
        self.root.attributes("-zoomed", True)
        self.root.configure(bg=C['bg'])

        self.working    = False
        self.work_start = None
        self.tlabel     = None
        self.tbtn       = None
        self.tstatus    = None
        self.wtree      = None
        self.ttree      = None
        self.tfilter    = tk.StringVar(value="Всi")
        self.search     = tk.StringVar()

        self._layout()
        self._sidebar()
        self._header()
        self.show("workers")
        self._tick()
        self.root.mainloop()

    def _layout(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.side = tk.Frame(self.root, bg=C['sidebar'], width=220)
        self.side.grid(row=0, column=0, sticky="ns")
        self.side.grid_propagate(False)

        self.body = tk.Frame(self.root, bg=C['bg'])
        self.body.grid(row=0, column=1, sticky="nsew")
        self.body.columnconfigure(0, weight=1)
        self.body.rowconfigure(1, weight=1)

    def _sidebar(self):
        tk.Label(self.side, text="CRM",
                 font=("Arial", 20, "bold"),
                 bg=C['sidebar'], fg="white").pack(pady=(28, 2))

        tk.Label(self.side, text=current_user['username'],
                 font=("Arial", 10),
                 bg=C['sidebar'], fg="#aaaacc").pack()

        role_fg = "#ffcc44" if current_user['role'] == 'admin' else "#6666aa"
        tk.Label(self.side, text=current_user['role'].upper(),
                 font=("Arial", 8, "bold"),
                 bg=C['sidebar'], fg=role_fg).pack(pady=(2, 18))

        tk.Frame(self.side, bg=C['side2'], height=1).pack(fill="x", padx=16, pady=(0, 10))

        self.navbtns = {}
        pages = [("workers","Робiтники"), ("tasks","Завдання"),
                 ("timer","Таймер"), ("logs","Журнал")]
        if current_user['role'] == 'admin':
            pages.append(("admin", "Адмiнка"))

        for key, lbl in pages:
            b = tk.Button(self.side, text=lbl,
                          font=("Arial", 10),
                          bg=C['sidebar'], fg="#aaaacc",
                          relief="flat", bd=0,
                          pady=12, padx=20, anchor="w",
                          cursor="hand2",
                          activebackground=C['side2'],
                          activeforeground="white",
                          command=lambda k=key: self.show(k))
            b.pack(fill="x")
            self.navbtns[key] = b

        tk.Frame(self.side, bg=C['side2'], height=1).pack(fill="x", padx=16, pady=10)

        tk.Button(self.side, text="Вийти",
                  font=("Arial", 9),
                  bg=C['sidebar'], fg="#666688",
                  relief="flat", bd=0,
                  pady=10, padx=20, anchor="w",
                  cursor="hand2",
                  command=self.logout).pack(fill="x", side="bottom", pady=(0, 14))

    def _header(self):
        hdr = tk.Frame(self.body, bg=C['white'], pady=14)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(0, weight=1)

        self.htitle = tk.Label(hdr, text="",
                               font=("Arial", 15, "bold"),
                               bg=C['white'], fg=C['sidebar'])
        self.htitle.grid(row=0, column=0, sticky="w", padx=24)

        self.hsub = tk.Label(hdr, text="",
                             font=("Arial", 9),
                             bg=C['white'], fg=C['muted'])
        self.hsub.grid(row=1, column=0, sticky="w", padx=24)

        self.page = tk.Frame(self.body, bg=C['bg'])
        self.page.grid(row=1, column=0, sticky="nsew", padx=24, pady=20)
        self.page.columnconfigure(0, weight=1)
        self.page.rowconfigure(0, weight=1)

    def show(self, key):
        for k, b in self.navbtns.items():
            b.config(bg=C['sidebar'], fg="#aaaacc")
        if key in self.navbtns:
            self.navbtns[key].config(bg=C['side2'], fg="white")

        for w in self.page.winfo_children():
            w.destroy()

        info = {
            "workers": ("Робiтники",  "Список спiвробiтникiв"),
            "tasks":   ("Завдання",   "Дедлайни та прiоритети"),
            "timer":   ("Таймер",     "Облiк робочого часу"),
            "logs":    ("Журнал",     "Iсторiя дiй"),
            "admin":   ("Адмiнка",   "Управлiння системою"),
        }
        t, s = info.get(key, ("", ""))
        self.htitle.config(text=t)
        self.hsub.config(text=s)

        {"workers": self.pg_workers,
         "tasks":   self.pg_tasks,
         "timer":   self.pg_timer,
         "logs":    self.pg_logs,
         "admin":   self.pg_admin}[key]()


    def _toolbar(self):
        bar = tk.Frame(self.page, bg=C['bg'])
        bar.pack(fill="x", pady=(0, 10))
        return bar

    def pg_workers(self):
        bar   = self._toolbar()
        admin = current_user['role'] == 'admin'

        if admin:
            btn(bar, "+ Додати", self.worker_add).pack(side="left")
            btn(bar, "Видалити", self.worker_del,
                bg=C['white'], fg=C['danger']).pack(side="left", padx=(8,0))

        self.search = tk.StringVar()
        self.search.trace("w", lambda *a: self.worker_reload())
        label(bar, "Пошук:", size=9).pack(side="right", padx=(0,6))
        tk.Entry(bar, textvariable=self.search,
                 font=("Arial", 10), relief="flat",
                 bg=C['white'], fg=C['text'],
                 insertbackground=C['text']).pack(side="right", ipady=7, ipadx=10)

        self.wtree = make_tree(self.page,
                               ["#", "Iм'я", "Вiддiл", "Зарплата", "Дата найму"],
                               [40, 230, 190, 130, 160])
        self.worker_reload()

    def worker_reload(self):
        if not self.wtree:
            return
        q   = self.search.get().lower() if self.search else ''
        rows = []
        for w in load_workers():
            if q and q not in w.get('Name','').lower() \
                 and q not in w.get('Department','').lower():
                continue
            rows.append((w.get('id',''), w.get('Name',''),
                         w.get('Department',''), w.get('Salary',''),
                         w.get('Hire Date','')))
        tree_fill(self.wtree, rows)

    def worker_del(self):
        sel = self.wtree.selection()
        if not sel:
            messagebox.showwarning("Увага", "Виберiть рядок.")
            return
        if not messagebox.askyesno("Пiдтвердження", "Видалити?"):
            return
        ids = {int(s) for s in sel}
        save_workers([w for w in load_workers() if w.get('id') not in ids])
        log_action(f"видалив робiтникiв id={ids}")
        self.worker_reload()

    def worker_add(self):
        self._popup("Додати робiтника",
                    [("Iм'я","Name"),("Вiддiл","Department"),
                     ("Зарплата","Salary"),("Дата найму","Hire Date")],
                    self._worker_save)

    def _worker_save(self, data, win):
        if not data.get("Name"):
            messagebox.showwarning("Увага", "Iм'я обов'язкове.", parent=win)
            return False
        workers   = load_workers()
        data['id'] = next_id(workers)
        workers.append(data)
        save_workers(workers)
        log_action(f"додав робiтника: {data['Name']}")
        self.worker_reload()
        return True


    def pg_tasks(self):
        bar   = self._toolbar()
        admin = current_user['role'] == 'admin'

        if admin:
            btn(bar, "+ Завдання", self.task_add).pack(side="left")
            btn(bar, "Видалити", self.task_del,
                bg=C['white'], fg=C['danger']).pack(side="left", padx=(8,0))

        btn(bar, "Виконано", self.task_done,
            bg=C['white'], fg=C['success']).pack(side="left", padx=(8,0))

        self.tfilter = tk.StringVar(value="Всi")
        label(bar, "Фiльтр:", size=9).pack(side="right", padx=(0,6))
        cb = ttk.Combobox(bar, textvariable=self.tfilter,
                          values=["Всi"] + PRIORITY_LEVELS + ["Виконанi"],
                          state="readonly", width=12, font=("Arial",10))
        cb.pack(side="right")
        cb.bind("<<ComboboxSelected>>", lambda e: self.task_reload())

        self.ttree = make_tree(self.page,
                               ["#","Назва","Вiдповiдальний","Прiоритет",
                                "Дедлайн","Статус","Автор"],
                               [40,230,160,100,130,100,130])
        self.task_reload()

    def task_reload(self):
        if not self.ttree:
            return
        filt = self.tfilter.get() if self.tfilter else "Всi"
        rows = []
        tags = []
        for t in load_tasks():
            if filt == "Виконанi" and t.get('status') != "Виконано":
                continue
            if filt not in ("Всi","Виконанi") and t.get('priority') != filt:
                continue
            rows.append((t.get('id',''), t.get('title',''), t.get('assignee',''),
                         t.get('priority',''), t.get('deadline',''),
                         t.get('status','Активне'), t.get('author','')))
            done = t.get('status') == "Виконано"
            tags.append("done" if done else t.get('priority','Середня'))

        for r in self.ttree.get_children():
            self.ttree.delete(r)
        for row, tag in zip(rows, tags):
            self.ttree.insert("", "end", iid=str(row[0]),
                              values=row, tags=(tag,))

    def task_del(self):
        sel = self.ttree.selection()
        if not sel:
            messagebox.showwarning("Увага", "Виберiть завдання.")
            return
        ids = {int(s) for s in sel}
        save_tasks([t for t in load_tasks() if t.get('id') not in ids])
        log_action(f"видалив завдання id={ids}")
        self.task_reload()

    def task_done(self):
        sel = self.ttree.selection()
        if not sel:
            messagebox.showwarning("Увага", "Виберiть завдання.")
            return
        ids   = {int(s) for s in sel}
        tasks = load_tasks()
        for t in tasks:
            if t.get('id') in ids:
                t['status'] = "Виконано"
        save_tasks(tasks)
        log_action(f"виконав завдання id={ids}")
        self.task_reload()

    def task_add(self):
        win = tk.Toplevel(self.root)
        win.title("Нове завдання")
        win.geometry("380x430")
        win.configure(bg=C['white'])
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="Нове завдання",
                 font=("Arial", 13, "bold"),
                 bg=C['white'], fg=C['sidebar']).pack(pady=(20,10), padx=20, anchor="w")

        frm = tk.Frame(win, bg=C['white'])
        frm.pack(padx=20, fill="x")

        def fld(lbl):
            label(frm, lbl).pack(anchor="w")
            e = entry(frm)
            e.pack(fill="x", ipady=7, pady=(2,10))
            return e

        et = fld("Назва завдання")
        ea = fld("Вiдповiдальний")
        ed = fld("Дедлайн (РРРР-ММ-ДД)")

        label(frm, "Прiоритет").pack(anchor="w")
        pv = tk.StringVar(value="Середня")
        ttk.Combobox(frm, textvariable=pv, values=PRIORITY_LEVELS,
                     state="readonly", font=("Arial",11)).pack(fill="x", pady=(2,14))

        def submit():
            title = et.get().strip()
            if not title:
                messagebox.showwarning("Увага", "Назва обов'язкова.", parent=win)
                return
            tasks = load_tasks()
            tasks.append({
                'id':       next_id(tasks),
                'title':    title,
                'assignee': ea.get().strip(),
                'priority': pv.get(),
                'deadline': ed.get().strip(),
                'status':   'Активне',
                'author':   current_user['username'],
                'created':  datetime.datetime.now().isoformat(),
            })
            save_tasks(tasks)
            log_action(f"додав завдання: {title}")
            self.task_reload()
            win.destroy()

        btn(frm, "Зберегти", submit).pack(fill="x", pady=(4,0))


    def pg_timer(self):
        f = tk.Frame(self.page, bg=C['bg'])
        f.pack(expand=True)

        label(f, "Робочий час", size=12).pack(pady=(60,8))

        self.tlabel = tk.Label(f, text="00:00:00",
                               font=("Courier", 54, "bold"),
                               bg=C['bg'], fg=C['sidebar'])
        self.tlabel.pack(pady=(0,32))

        self.tbtn = tk.Button(f, text="Почати роботу",
                              font=("Arial", 13, "bold"),
                              bg="#eafaf1", fg="#1a5c35",
                              relief="flat", bd=0,
                              padx=48, pady=16,
                              cursor="hand2",
                              command=self.toggle_work)
        self.tbtn.pack()

        self.tstatus = tk.Label(f, text="",
                                font=("Arial", 9),
                                bg=C['bg'], fg=C['muted'])
        self.tstatus.pack(pady=(14,0))

    def toggle_work(self):
        if not self.working:
            self.work_start = datetime.datetime.now()
            self.working    = True
            self.tbtn.config(text="Завершити роботу", bg="#fdecea", fg="#9b2a2a")
            self.tstatus.config(text=f"Почато: {self.work_start.strftime('%H:%M:%S')}")
            log_action("почав роботу")
        else:
            h, m, s = self._elapsed()
            messagebox.showinfo("Час роботи", f"{h} год {m} хв {s} сек")
            log_action(f"завершив роботу ({h}г {m}хв {s}с)")
            self.working    = False
            self.work_start = None
            if self.tlabel:
                try: self.tlabel.config(text="00:00:00")
                except tk.TclError: pass
            if self.tbtn:
                try: self.tbtn.config(text="Почати роботу", bg="#eafaf1", fg="#1a5c35")
                except tk.TclError: pass
            if self.tstatus:
                try: self.tstatus.config(text="")
                except tk.TclError: pass

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


    def pg_logs(self):
        tree = make_tree(self.page,
                         ["Час","Користувач","Дiя"],
                         [180,160,560])
        for i, row in enumerate(db_get_logs()):
            ts  = (row[0] or '')[:19].replace("T"," ")
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=(ts, row[1] or '', row[2] or ''),
                        tags=(tag,))


    def pg_admin(self):
        if current_user['role'] != 'admin':
            return

        nb = ttk.Notebook(self.page)
        nb.pack(fill="both", expand=True)

        tu = tk.Frame(nb, bg=C['bg'])
        tw = tk.Frame(nb, bg=C['bg'])
        tt = tk.Frame(nb, bg=C['bg'])

        nb.add(tu, text="  Користувачi  ")
        nb.add(tw, text="  Робiтники  ")
        nb.add(tt, text="  Завдання  ")

        self._admin_users(tu)
        self._admin_workers(tw)
        self._admin_tasks(tt)

    def _admin_users(self, parent):
        bar = tk.Frame(parent, bg=C['bg'])
        bar.pack(fill="x", pady=(0,10), padx=4)

        utree_holder = [None]

        btn(bar, "Оновити",
            lambda: self._au_reload(utree_holder[0])).pack(side="left")
        btn(bar, "Зробити адмiном",
            lambda: self._au_role(utree_holder[0], 'admin'),
            bg=C['warn']).pack(side="left", padx=(8,0))
        btn(bar, "Зробити user",
            lambda: self._au_role(utree_holder[0], 'user'),
            bg=C['ibg'], fg=C['text']).pack(side="left", padx=(8,0))
        btn(bar, "Видалити",
            lambda: self._au_delete(utree_holder[0]),
            bg=C['danger']).pack(side="left", padx=(8,0))

        tree = make_tree(parent,
                         ["ID","Логiн","Роль","Телефон","Email","Органiзацiя","Реєстрацiя"],
                         [40,150,80,130,180,160,170])
        utree_holder[0] = tree
        self._au_reload(tree)

    def _au_reload(self, tree):
        if not tree:
            return
        for r in tree.get_children():
            tree.delete(r)
        for i, row in enumerate(db_get_users()):
            ts  = (row[6] or '')[:19].replace("T"," ")
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", iid=str(row[0]),
                        values=(row[0],row[1],row[2],
                                row[3] or '',row[4] or '',
                                row[5] or '',ts),
                        tags=(tag,))

    def _au_role(self, tree, role):
        if not tree:
            return
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Увага", "Виберiть користувача.")
            return
        for s in sel:
            db_set_role(int(s), role)
            log_action(f"змiнив роль user id={s} на {role}")
        self._au_reload(tree)

    def _au_delete(self, tree):
        if not tree:
            return
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Увага", "Виберiть користувача.")
            return
        for s in sel:
            if int(s) == current_user['id']:
                messagebox.showwarning("Увага", "Не можна видалити себе.")
                return
        if not messagebox.askyesno("Пiдтвердження", "Видалити?"):
            return
        for s in sel:
            db_delete_user(int(s))
            log_action(f"видалив user id={s}")
        self._au_reload(tree)

    def _admin_workers(self, parent):
        bar = tk.Frame(parent, bg=C['bg'])
        bar.pack(fill="x", pady=(0,10), padx=4)

        wtree_h = [None]
        btn(bar, "+ Додати",
            lambda: self.worker_add()).pack(side="left")
        btn(bar, "Видалити",
            lambda: self._aw_delete(wtree_h[0]),
            bg=C['danger']).pack(side="left", padx=(8,0))

        tree = make_tree(parent,
                         ["#","Iм'я","Вiддiл","Зарплата","Дата найму"],
                         [40,230,190,130,160])
        wtree_h[0] = tree

        for i, w in enumerate(load_workers()):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", iid=str(w.get('id',i)),
                        values=(w.get('id',''), w.get('Name',''),
                                w.get('Department',''), w.get('Salary',''),
                                w.get('Hire Date','')),
                        tags=(tag,))

    def _aw_delete(self, tree):
        if not tree:
            return
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Увага", "Виберiть рядок.")
            return
        if not messagebox.askyesno("Пiдтвердження", "Видалити?"):
            return
        ids = {int(s) for s in sel}
        save_workers([w for w in load_workers() if w.get('id') not in ids])
        log_action(f"(адмiн) видалив робiтникiв id={ids}")
        for s in sel:
            tree.delete(s)

    def _admin_tasks(self, parent):
        bar = tk.Frame(parent, bg=C['bg'])
        bar.pack(fill="x", pady=(0,10), padx=4)

        ttree_h = [None]
        btn(bar, "+ Завдання",
            lambda: self.task_add()).pack(side="left")
        btn(bar, "Видалити",
            lambda: self._at_delete(ttree_h[0]),
            bg=C['danger']).pack(side="left", padx=(8,0))
        btn(bar, "Виконано",
            lambda: self._at_done(ttree_h[0]),
            bg=C['success']).pack(side="left", padx=(8,0))

        tree = make_tree(parent,
                         ["#","Назва","Вiдповiдальний","Прiоритет",
                          "Дедлайн","Статус","Автор"],
                         [40,220,150,100,120,100,130])
        ttree_h[0] = tree

        for i, t in enumerate(load_tasks()):
            done = t.get('status') == "Виконано"
            tag  = "done" if done else t.get('priority','Середня')
            tree.insert("", "end", iid=str(t.get('id',i)),
                        values=(t.get('id',''), t.get('title',''),
                                t.get('assignee',''), t.get('priority',''),
                                t.get('deadline',''), t.get('status',''),
                                t.get('author','')),
                        tags=(tag,))

    def _at_delete(self, tree):
        if not tree:
            return
        sel = tree.selection()
        if not sel:
            return
        ids = {int(s) for s in sel}
        save_tasks([t for t in load_tasks() if t.get('id') not in ids])
        for s in sel:
            tree.delete(s)
        log_action(f"(адмiн) видалив завдання id={ids}")

    def _at_done(self, tree):
        if not tree:
            return
        sel = tree.selection()
        if not sel:
            return
        ids   = {int(s) for s in sel}
        tasks = load_tasks()
        for t in tasks:
            if t.get('id') in ids:
                t['status'] = "Виконано"
        save_tasks(tasks)
        for s in sel:
            vals    = list(tree.item(s, 'values'))
            vals[5] = "Виконано"
            tree.item(s, values=vals, tags=("done",))


    def _popup(self, title, fields, on_submit):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry(f"340x{90 + len(fields)*72}")
        win.configure(bg=C['white'])
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text=title, font=("Arial", 13, "bold"),
                 bg=C['white'], fg=C['sidebar']).pack(pady=(20,12), padx=20, anchor="w")

        frm     = tk.Frame(win, bg=C['white'])
        frm.pack(padx=20, fill="x")
        entries = {}

        for lbl, key in fields:
            label(frm, lbl).pack(anchor="w")
            e = entry(frm)
            e.pack(fill="x", ipady=7, pady=(2,10))
            entries[key] = e

        def submit():
            data = {k: e.get().strip() for k, e in entries.items()}
            if on_submit(data, win):
                win.destroy()

        btn(frm, "Зберегти", submit).pack(fill="x", pady=(6,0))


    def logout(self):
        log_action("вийшов з системи")
        self.root.destroy()
        LoginWindow()


db_init()
LoginWindow()