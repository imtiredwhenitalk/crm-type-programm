import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import logging
import hashlib
import sqlite3
import json
import csv
import os

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR    = os.path.join(BASE_DIR, 'logs')
DATA_DIR    = os.path.join(BASE_DIR, 'data')
LOG_FILE    = os.path.join(LOGS_DIR, 'crm_log.txt')
SESSION_FILE = os.path.join(DATA_DIR, 'session.json')
DB_PATH     = os.path.join(BASE_DIR, 'crm.db')

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

current_user    = None
PRIORITY_LEVELS = ['Критична', 'Висока', 'Середня', 'Низька']

# ── Themes ──────────────────────────────────────────────────────────────────
THEMES = {
    'light': {
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
        'tree_bg': '#ffffff',
        'tree_alt':'#fafafa',
        'tree_sel':'#eef2ff',
        'tree_sfg':'#1a1a2e',
    },
    'dark': {
        'bg':      '#1a1a2e',
        'sidebar': '#0f0f1a',
        'side2':   '#2a2a4e',
        'white':   '#16213e',
        'text':    '#e0e0e0',
        'muted':   '#7777aa',
        'ibg':     '#0f0f1a',
        'sep':     '#2a2a4e',
        'accent':  '#4a6bff',
        'danger':  '#e74c3c',
        'success': '#2ecc71',
        'warn':    '#e67e22',
        'tree_bg': '#16213e',
        'tree_alt':'#1a1f35',
        'tree_sel':'#2a2a6e',
        'tree_sfg':'#e0e0e0',
    }
}
C = THEMES['light']

FAQ_SECTIONS = [
    ("Вхід у систему", [
        ("Як увійти?",
         "Введіть логін та пароль на головному екрані.\n"
         "Логін адміна за замовчуванням: admin / admin.\n"
         "Після входу система запитає додаткові дані профілю.\n\n"
         "✅ Ввімкніть «Запам'ятати пристрій» — тоді наступного разу\n"
         "   входити знову не потрібно."),
        ("Забув пароль?",
         "Зверніться до адміністратора — він може видалити акаунт\n"
         "та створити новий через Адмінку → Користувачі → + Створити."),
        ("Блокування після 3 спроб?",
         "Якщо ввести неправильний пароль 3 рази поспіль —\n"
         "вхід буде заблоковано на 5 хвилин.\n"
         "Зачекайте або зверніться до адміна."),
    ]),
    ("Працівники", [
        ("Як додати працівника?",
         "Адмін: Працівники → + Додати → заповнити форму → Зберегти.\n"
         "Звичайний користувач може лише переглядати список."),
        ("Як редагувати працівника?",
         "Виберіть рядок у таблиці (подвійний клік або кнопка 'Редагувати').\n"
         "Доступно лише адміну."),
        ("Як шукати працівника?",
         "Введіть ім'я або відділ у поле 'Пошук' над таблицею.\n"
         "Фільтрація відбувається в реальному часі."),
        ("Як експортувати в CSV?",
         "Кнопка 'Експорт CSV' → оберіть місце збереження файлу."),
        ("Статистика?",
         "Вкладка 'Статистика' показує кількість по відділах,\n"
         "середню зарплату та загальний фонд оплати праці."),
    ]),
    ("Завдання", [
        ("Як створити завдання?",
         "Адмін: Завдання → + Завдання → заповнити назву,\n"
         "відповідального, дедлайн та пріоритет → Зберегти."),
        ("Рівні пріоритету:",
         "Критична — негайно\nВисока — найближчим часом\n"
         "Середня — планово\nНизька — при нагоді\n\n"
         "Колір рядка в таблиці відповідає пріоритету."),
    ]),
    ("Таймер", [
        ("Як використовувати таймер?",
         "Перейдіть на сторінку 'Таймер' → натисніть 'Почати роботу'.\n"
         "Натисніть 'Завершити роботу' — система покаже тривалість сесії."),
    ]),
    ("Адмінка", [
        ("Що може адмін?",
         "- Створювати нових користувачів\n"
         "- Змінювати ролі (admin / user)\n"
         "- Видаляти користувачів\n"
         "- Керувати працівниками і завданнями\n"
         "- Переглядати повний журнал дій"),
    ]),
]

# ── DB ───────────────────────────────────────────────────────────────────────
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
            created  TEXT,
            locked_until TEXT DEFAULT ""
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            username TEXT PRIMARY KEY,
            count    INTEGER DEFAULT 0,
            last_attempt TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS workers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            department TEXT DEFAULT "",
            salary     REAL DEFAULT 0,
            hire_date  TEXT DEFAULT "",
            phone      TEXT DEFAULT "",
            email      TEXT DEFAULT "",
            position   TEXT DEFAULT "",
            note       TEXT DEFAULT ""
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            title     TEXT NOT NULL,
            assignee  TEXT DEFAULT "",
            priority  TEXT DEFAULT "Середня",
            deadline  TEXT DEFAULT "",
            status    TEXT DEFAULT "Активне",
            author    TEXT DEFAULT "",
            created   TEXT
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

    # Migrations for users table
    existing = [r[1] for r in conn.execute('PRAGMA table_info(users)').fetchall()]
    for col, dflt in [('phone','""'),('email','""'),('org','""'),('locked_until','""')]:
        if col not in existing:
            conn.execute(f'ALTER TABLE users ADD COLUMN {col} TEXT DEFAULT {dflt}')

    if not conn.execute('SELECT id FROM users WHERE username="admin"').fetchone():
        conn.execute(
            'INSERT INTO users (username,password,role,created) VALUES (?,?,?,?)',
            ('admin', hash_pw('admin'), 'admin', datetime.datetime.now().isoformat())
        )

    conn.commit()
    conn.close()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ── Login attempts / locking ──────────────────────────────────────────────
def get_attempts(username):
    conn = db()
    row = conn.execute('SELECT count, last_attempt FROM login_attempts WHERE username=?', (username,)).fetchone()
    conn.close()
    return row if row else (0, None)

def record_failed(username):
    now = datetime.datetime.now().isoformat()
    conn = db()
    existing = conn.execute('SELECT count FROM login_attempts WHERE username=?', (username,)).fetchone()
    if existing:
        new_count = existing[0] + 1
        conn.execute('UPDATE login_attempts SET count=?, last_attempt=? WHERE username=?',
                     (new_count, now, username))
    else:
        conn.execute('INSERT INTO login_attempts (username, count, last_attempt) VALUES (?,?,?)',
                     (username, 1, now))
    conn.commit()
    conn.close()

def reset_attempts(username):
    conn = db()
    conn.execute('DELETE FROM login_attempts WHERE username=?', (username,))
    conn.commit()
    conn.close()

def is_locked(username):
    count, last = get_attempts(username)
    if count >= 3 and last:
        dt = datetime.datetime.fromisoformat(last)
        if (datetime.datetime.now() - dt).total_seconds() < 300:  # 5 min
            remaining = 300 - int((datetime.datetime.now() - dt).total_seconds())
            return True, remaining
        else:
            reset_attempts(username)
    return False, 0

# ── Session ───────────────────────────────────────────────────────────────
def save_session(username):
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump({'username': username, 'saved_at': datetime.datetime.now().isoformat()}, f)

def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Session valid for 30 days
        saved = datetime.datetime.fromisoformat(data['saved_at'])
        if (datetime.datetime.now() - saved).days < 30:
            return data.get('username')
    except Exception:
        pass
    return None

def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# ── User DB ───────────────────────────────────────────────────────────────
def db_login(username, password):
    conn = db()
    row = conn.execute(
        'SELECT id,username,role,phone,email,org FROM users WHERE username=? AND password=?',
        (username, hash_pw(password))
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {'id':row[0],'username':row[1],'role':row[2],
            'phone':row[3] or '','email':row[4] or '','org':row[5] or ''}

def db_login_by_username(username):
    conn = db()
    row = conn.execute(
        'SELECT id,username,role,phone,email,org FROM users WHERE username=?', (username,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {'id':row[0],'username':row[1],'role':row[2],
            'phone':row[3] or '','email':row[4] or '','org':row[5] or ''}

def db_create_user(username, password, role):
    try:
        conn = db()
        conn.execute(
            'INSERT INTO users (username,password,role,created) VALUES (?,?,?,?)',
            (username, hash_pw(password), role, datetime.datetime.now().isoformat())
        )
        conn.commit(); conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def db_update_profile(uid, phone, email, org):
    conn = db()
    conn.execute('UPDATE users SET phone=?,email=?,org=? WHERE id=?', (phone,email,org,uid))
    conn.commit(); conn.close()

def db_get_users():
    conn = db()
    rows = conn.execute('SELECT id,username,role,phone,email,org,created FROM users ORDER BY id').fetchall()
    conn.close()
    return rows

def db_set_role(uid, role):
    conn = db()
    conn.execute('UPDATE users SET role=? WHERE id=?', (role,uid))
    conn.commit(); conn.close()

def db_delete_user(uid):
    conn = db()
    conn.execute('DELETE FROM users WHERE id=?', (uid,))
    conn.commit(); conn.close()

def db_get_logs():
    conn = db()
    rows = conn.execute('SELECT timestamp,username,action FROM logs ORDER BY timestamp DESC LIMIT 300').fetchall()
    conn.close()
    return rows

def log_action(action):
    uname = current_user['username'] if current_user else 'system'
    now   = datetime.datetime.now()
    logging.info(f"{uname} - {action}")
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{now} - {uname} - {action}\n")
    except Exception:
        pass
    conn = db()
    conn.execute('INSERT INTO logs (timestamp,username,action) VALUES (?,?,?)',
                 (now.isoformat(), uname, action))
    conn.commit(); conn.close()

# ── Workers DB ────────────────────────────────────────────────────────────
def db_get_workers(search=''):
    conn = db()
    q = f"%{search.lower()}%"
    rows = conn.execute(
        '''SELECT id,name,department,salary,hire_date,phone,email,position,note
           FROM workers WHERE lower(name) LIKE ? OR lower(department) LIKE ?
           OR lower(position) LIKE ? ORDER BY name''',
        (q, q, q)
    ).fetchall()
    conn.close()
    return rows

def db_add_worker(data):
    conn = db()
    conn.execute(
        '''INSERT INTO workers (name,department,salary,hire_date,phone,email,position,note)
           VALUES (?,?,?,?,?,?,?,?)''',
        (data['name'], data['department'], data.get('salary',0),
         data['hire_date'], data['phone'], data['email'],
         data['position'], data['note'])
    )
    conn.commit(); conn.close()

def db_update_worker(wid, data):
    conn = db()
    conn.execute(
        '''UPDATE workers SET name=?,department=?,salary=?,hire_date=?,
           phone=?,email=?,position=?,note=? WHERE id=?''',
        (data['name'], data['department'], data.get('salary',0),
         data['hire_date'], data['phone'], data['email'],
         data['position'], data['note'], wid)
    )
    conn.commit(); conn.close()

def db_delete_workers(ids):
    conn = db()
    conn.executemany('DELETE FROM workers WHERE id=?', [(i,) for i in ids])
    conn.commit(); conn.close()

def db_worker_stats():
    conn = db()
    rows = conn.execute(
        'SELECT department, COUNT(*), AVG(salary), SUM(salary) FROM workers GROUP BY department'
    ).fetchall()
    total = conn.execute('SELECT COUNT(*), AVG(salary), SUM(salary) FROM workers').fetchone()
    conn.close()
    return rows, total

# ── Tasks DB ─────────────────────────────────────────────────────────────
def db_get_tasks(filt='Всі'):
    conn = db()
    if filt == 'Виконані':
        rows = conn.execute("SELECT id,title,assignee,priority,deadline,status,author FROM tasks WHERE status='Виконано' ORDER BY id").fetchall()
    elif filt in PRIORITY_LEVELS:
        rows = conn.execute("SELECT id,title,assignee,priority,deadline,status,author FROM tasks WHERE priority=? ORDER BY id", (filt,)).fetchall()
    else:
        rows = conn.execute("SELECT id,title,assignee,priority,deadline,status,author FROM tasks ORDER BY id").fetchall()
    conn.close()
    return rows

def db_add_task(data):
    conn = db()
    conn.execute(
        'INSERT INTO tasks (title,assignee,priority,deadline,status,author,created) VALUES (?,?,?,?,?,?,?)',
        (data['title'], data['assignee'], data['priority'],
         data['deadline'], 'Активне', data['author'], datetime.datetime.now().isoformat())
    )
    conn.commit(); conn.close()

def db_delete_tasks(ids):
    conn = db()
    conn.executemany('DELETE FROM tasks WHERE id=?', [(i,) for i in ids])
    conn.commit(); conn.close()

def db_task_done(ids):
    conn = db()
    conn.executemany("UPDATE tasks SET status='Виконано' WHERE id=?", [(i,) for i in ids])
    conn.commit(); conn.close()

# ── Helpers ───────────────────────────────────────────────────────────────
def mk_entry(parent, show=None, width=None):
    kw = dict(font=("Arial",11), relief="flat",
              bg=C['ibg'], fg=C['text'],
              insertbackground=C['text'], show=show or '')
    if width:
        kw['width'] = width
    return tk.Entry(parent, **kw)

def mk_label(parent, text, size=9, color=None, bold=False):
    font = ("Arial", size, "bold") if bold else ("Arial", size)
    return tk.Label(parent, text=text, font=font,
                    bg=parent.cget('bg'), fg=color or C['muted'])

def mk_btn(parent, text, cmd, bg=None, fg='white', padx=16, pady=10):
    return tk.Button(parent, text=text, command=cmd,
                     font=("Arial",10,"bold"),
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
                 background=C['tree_bg'], foreground=C['text'],
                 rowheight=36, fieldbackground=C['tree_bg'],
                 font=("Arial",10), borderwidth=0)
    st.configure("T.Treeview.Heading",
                 background=C['ibg'], foreground='#888',
                 font=("Arial",9,"bold"), relief="flat")
    st.map("T.Treeview",
           background=[("selected", C['tree_sel'])],
           foreground=[("selected", C['tree_sfg'])])
    st.layout("T.Treeview", [('T.Treeview.treearea', {'sticky':'nswe'})])

    wrap = tk.Frame(parent, bg=C['white'])
    wrap.pack(fill="both", expand=True)

    tree = ttk.Treeview(wrap, columns=columns, show="headings", style="T.Treeview")
    vsb  = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    for col, w in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, minwidth=40, anchor="w")

    tree.tag_configure("even",     background=C['tree_bg'])
    tree.tag_configure("odd",      background=C['tree_alt'])
    tree.tag_configure("done",     foreground=C['muted'])
    tree.tag_configure("Критична", foreground=C['danger'])
    tree.tag_configure("Висока",   foreground=C['warn'])
    tree.tag_configure("Середня",  foreground="#c0920a")
    tree.tag_configure("Низька",   foreground=C['success'])

    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return tree

# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN WINDOW
# ══════════════════════════════════════════════════════════════════════════════
class LoginWindow:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("CRM — Вхід")
        self.win.geometry("400x500")
        self.win.configure(bg=C['white'])
        self.win.resizable(False, False)
        self._build()

        # Auto-login from session
        saved = load_session()
        if saved:
            user = db_login_by_username(saved)
            if user:
                global current_user
                current_user = user
                self.win.after(100, self._auto_login)

        self.win.mainloop()

    def _auto_login(self):
        log_action("автоматичний вхід (збережена сесія)")
        self.win.destroy()
        CRMApp()

    def _build(self):
        tk.Frame(self.win, bg=C['sidebar'], height=6).pack(fill="x")

        tk.Label(self.win, text="CRM System",
                 font=("Arial",24,"bold"),
                 bg=C['white'], fg=C['sidebar']).pack(pady=(36,4))
        tk.Label(self.win, text="Введіть логін та пароль",
                 font=("Arial",10),
                 bg=C['white'], fg=C['muted']).pack(pady=(0,24))

        frm = tk.Frame(self.win, bg=C['white'])
        frm.pack(padx=40, fill="x")

        mk_label(frm, "Логін").pack(anchor="w")
        self.eu = mk_entry(frm)
        self.eu.pack(fill="x", ipady=8, pady=(2,14))

        mk_label(frm, "Пароль").pack(anchor="w")
        self.ep = mk_entry(frm, show="*")
        self.ep.pack(fill="x", ipady=8, pady=(2,10))

        self.remember = tk.BooleanVar(value=False)
        tk.Checkbutton(frm, text="Запам'ятати пристрій (30 днів)",
                       variable=self.remember,
                       font=("Arial",9),
                       bg=C['white'], fg=C['muted'],
                       activebackground=C['white'],
                       selectcolor=C['ibg']).pack(anchor="w", pady=(0,18))

        mk_btn(frm, "Увійти", self.do_login).pack(fill="x", pady=(0,8))

        mk_btn(frm, "Інструкція (FAQ)", self.open_faq,
               bg=C['ibg'], fg=C['text']).pack(fill="x")

        self.msg = tk.Label(frm, text="", font=("Arial",9),
                            bg=C['white'], fg=C['danger'], wraplength=300)
        self.msg.pack(pady=(10,0))

        self.ep.bind("<Return>", lambda e: self.do_login())
        self.eu.bind("<Return>", lambda e: self.ep.focus())

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
            self.msg.config(text=f"⛔ Акаунт заблоковано на {mins}хв {secs}с\n(Занадто багато невдалих спроб)")
            return

        user = db_login(u, p)
        if user:
            reset_attempts(u)
            global current_user
            current_user = user
            if self.remember.get():
                save_session(u)
            log_action("увійшов у систему")
            self.win.destroy()
            ProfileWindow(on_done=lambda: CRMApp())
        else:
            record_failed(u)
            count, _ = get_attempts(u)
            remaining_tries = max(0, 3 - count)
            if remaining_tries == 0:
                self.msg.config(text="⛔ Акаунт заблоковано на 5 хвилин!")
            else:
                self.msg.config(text=f"❌ Невірний логін або пароль.\nЗалишилось спроб: {remaining_tries}")

    def open_faq(self):
        FAQWindow(self.win)


# ══════════════════════════════════════════════════════════════════════════════
#  FAQ WINDOW
# ══════════════════════════════════════════════════════════════════════════════
class FAQWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Інструкція — CRM System")
        self.win.geometry("720x560")
        self.win.configure(bg=C['white'])
        self.win.grab_set()
        self._build()

    def _build(self):
        tk.Frame(self.win, bg=C['sidebar'], height=6).pack(fill="x")
        tk.Label(self.win, text="Інструкція з використання",
                 font=("Arial",15,"bold"),
                 bg=C['white'], fg=C['sidebar']).pack(pady=(20,4), padx=24, anchor="w")
        tk.Label(self.win, text="CRM System v3.0",
                 font=("Arial",9), bg=C['white'], fg=C['muted']).pack(padx=24, anchor="w", pady=(0,12))
        tk.Frame(self.win, bg=C['sep'], height=1).pack(fill="x")

        main  = tk.Frame(self.win, bg=C['white'])
        main.pack(fill="both", expand=True)
        left  = tk.Frame(main, bg=C['ibg'], width=210)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        right = tk.Frame(main, bg=C['white'])
        right.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="РОЗДІЛИ", font=("Arial",8,"bold"),
                 bg=C['ibg'], fg=C['muted']).pack(pady=(16,8), padx=16, anchor="w")

        self.title_lbl = tk.Label(right, text="", font=("Arial",12,"bold"),
                                   bg=C['white'], fg=C['sidebar'], anchor="w")
        self.title_lbl.pack(pady=(20,4), padx=24, anchor="w")

        self.body_txt = tk.Text(right, font=("Arial",10), bg=C['white'], fg=C['text'],
                                 relief="flat", bd=0, wrap="word", state="disabled", cursor="arrow")
        self.body_txt.pack(fill="both", expand=True, padx=24, pady=(0,20))

        first = True
        for section, pairs in FAQ_SECTIONS:
            tk.Label(left, text=section, font=("Arial",9,"bold"),
                     bg=C['ibg'], fg=C['sidebar']).pack(anchor="w", padx=16, pady=(10,2))
            for q, a in pairs:
                b = tk.Button(left, text=f"  {q}", font=("Arial",9),
                              bg=C['ibg'], fg=C['text'], relief="flat", bd=0,
                              pady=5, padx=8, anchor="w", cursor="hand2",
                              wraplength=180, justify="left",
                              command=lambda qq=q, aa=a: self._show(qq, aa))
                b.pack(fill="x", padx=8)
                if first:
                    self._show(q, a); first = False

    def _show(self, q, a):
        self.title_lbl.config(text=q)
        self.body_txt.config(state="normal")
        self.body_txt.delete("1.0","end")
        self.body_txt.insert("1.0", a)
        self.body_txt.config(state="disabled")


# ══════════════════════════════════════════════════════════════════════════════
#  PROFILE WINDOW
# ══════════════════════════════════════════════════════════════════════════════
class ProfileWindow:
    def __init__(self, on_done):
        self.on_done = on_done
        self.win = tk.Tk()
        self.win.title("Профіль")
        self.win.geometry("400x400")
        self.win.configure(bg=C['white'])
        self.win.resizable(False, False)
        self._build()
        self.win.mainloop()

    def _build(self):
        tk.Frame(self.win, bg=C['sidebar'], height=6).pack(fill="x")
        tk.Label(self.win, text=f"Вітаємо, {current_user['username']}",
                 font=("Arial",16,"bold"),
                 bg=C['white'], fg=C['sidebar']).pack(pady=(28,4))
        tk.Label(self.win, text="Заповніть дані профілю (необов'язково)",
                 font=("Arial",10), bg=C['white'], fg=C['muted']).pack(pady=(0,18))

        frm = tk.Frame(self.win, bg=C['white'])
        frm.pack(padx=36, fill="x")
        self.fields = {}
        for lbl, key in [("Номер телефону","phone"),("Email","email"),("Організація","org")]:
            mk_label(frm, lbl).pack(anchor="w")
            e = mk_entry(frm)
            e.insert(0, current_user.get(key,''))
            e.pack(fill="x", ipady=7, pady=(2,12))
            self.fields[key] = e

        mk_btn(frm, "Зберегти і продовжити", self.save).pack(fill="x", pady=(8,6))
        mk_btn(frm, "Пропустити", self.skip, bg=C['ibg'], fg=C['text']).pack(fill="x")

    def save(self):
        phone = self.fields['phone'].get().strip()
        email = self.fields['email'].get().strip()
        org   = self.fields['org'].get().strip()
        db_update_profile(current_user['id'], phone, email, org)
        current_user.update({'phone':phone,'email':email,'org':org})
        log_action("оновив профіль")
        self.win.destroy(); self.on_done()

    def skip(self):
        self.win.destroy(); self.on_done()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
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
        self.tfilter    = tk.StringVar(value="Всі")
        self.wsearch    = tk.StringVar()
        self.dark_mode  = False

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
                 font=("Arial",20,"bold"),
                 bg=C['sidebar'], fg="white").pack(pady=(28,2))
        tk.Label(self.side, text=current_user['username'],
                 font=("Arial",10), bg=C['sidebar'], fg="#aaaacc").pack()

        role_fg = "#ffcc44" if current_user['role']=='admin' else "#6666aa"
        tk.Label(self.side, text=current_user['role'].upper(),
                 font=("Arial",8,"bold"), bg=C['sidebar'], fg=role_fg).pack(pady=(2,18))

        tk.Frame(self.side, bg=C['side2'], height=1).pack(fill="x", padx=16, pady=(0,10))

        self.navbtns = {}
        pages = [("workers","👥 Працівники"),("tasks","📋 Завдання"),
                 ("timer","⏱ Таймер"),("logs","📜 Журнал"),("faq","❓ FAQ")]
        if current_user['role'] == 'admin':
            pages.append(("admin","⚙️ Адмінка"))

        for key, lbl in pages:
            b = tk.Button(self.side, text=lbl, font=("Arial",10),
                          bg=C['sidebar'], fg="#aaaacc", relief="flat", bd=0,
                          pady=12, padx=20, anchor="w", cursor="hand2",
                          activebackground=C['side2'], activeforeground="white",
                          command=lambda k=key: self.show(k))
            b.pack(fill="x")
            self.navbtns[key] = b

        tk.Frame(self.side, bg=C['side2'], height=1).pack(fill="x", padx=16, pady=10)

        # Dark mode toggle
        self.dark_btn = tk.Button(self.side, text="🌙 Темна тема",
                                   font=("Arial",9), bg=C['sidebar'], fg="#6666aa",
                                   relief="flat", bd=0, pady=10, padx=20, anchor="w",
                                   cursor="hand2", command=self.toggle_theme)
        self.dark_btn.pack(fill="x")

        tk.Button(self.side, text="🚪 Вийти",
                  font=("Arial",9), bg=C['sidebar'], fg="#666688",
                  relief="flat", bd=0, pady=10, padx=20, anchor="w",
                  cursor="hand2", command=self.logout).pack(fill="x", side="bottom", pady=(0,14))

    def toggle_theme(self):
        global C
        self.dark_mode = not self.dark_mode
        C = THEMES['dark'] if self.dark_mode else THEMES['light']
        self.dark_btn.config(text="☀️ Світла тема" if self.dark_mode else "🌙 Темна тема")
        # Rebuild UI
        for w in self.root.winfo_children():
            w.destroy()
        self._layout()
        self._sidebar()
        self._header()
        self.show("workers")

    def _header(self):
        hdr = tk.Frame(self.body, bg=C['white'], pady=14)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(0, weight=1)

        self.htitle = tk.Label(hdr, text="", font=("Arial",15,"bold"),
                               bg=C['white'], fg=C['sidebar'])
        self.htitle.grid(row=0, column=0, sticky="w", padx=24)

        self.hsub = tk.Label(hdr, text="", font=("Arial",9),
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
            "workers": ("Працівники",  "Список співробітників"),
            "tasks":   ("Завдання",    "Дедлайни та пріоритети"),
            "timer":   ("Таймер",      "Облік робочого часу"),
            "logs":    ("Журнал",      "Історія дій"),
            "faq":     ("FAQ",         "Інструкція з використання"),
            "admin":   ("Адмінка",     "Управління системою"),
        }
        t, s = info.get(key, ("",""))
        self.htitle.config(text=t)
        self.hsub.config(text=s)

        {"workers": self.pg_workers,
         "tasks":   self.pg_tasks,
         "timer":   self.pg_timer,
         "logs":    self.pg_logs,
         "faq":     self.pg_faq,
         "admin":   self.pg_admin}[key]()

    def _toolbar(self):
        bar = tk.Frame(self.page, bg=C['bg'])
        bar.pack(fill="x", pady=(0,10))
        return bar

    # ── Workers page ────────────────────────────────────────────────────────
    def pg_workers(self):
        # Notebook: list + stats
        nb = ttk.Notebook(self.page)
        nb.pack(fill="both", expand=True)

        tab_list  = tk.Frame(nb, bg=C['bg'])
        tab_stats = tk.Frame(nb, bg=C['bg'])
        nb.add(tab_list,  text="  Список  ")
        nb.add(tab_stats, text="  Статистика  ")

        self._workers_list(tab_list)
        self._workers_stats(tab_stats)

    def _workers_list(self, parent):
        bar   = tk.Frame(parent, bg=C['bg'])
        bar.pack(fill="x", pady=(0,10))
        admin = current_user['role'] == 'admin'

        if admin:
            mk_btn(bar, "+ Додати",   self.worker_add).pack(side="left")
            mk_btn(bar, "✏ Редагувати", self.worker_edit,
                   bg=C['warn']).pack(side="left", padx=(8,0))
            mk_btn(bar, "🗑 Видалити",  self.worker_del,
                   bg=C['white'], fg=C['danger']).pack(side="left", padx=(8,0))

        mk_btn(bar, "📥 Експорт CSV", self.worker_export_csv,
               bg=C['ibg'], fg=C['text']).pack(side="left", padx=(8,0))

        self.wsearch = tk.StringVar()
        self.wsearch.trace("w", lambda *a: self.worker_reload())
        mk_label(bar, "Пошук:", size=9).pack(side="right", padx=(0,6))
        tk.Entry(bar, textvariable=self.wsearch,
                 font=("Arial",10), relief="flat",
                 bg=C['white'], fg=C['text'],
                 insertbackground=C['text']).pack(side="right", ipady=7, ipadx=10)

        self.wtree = make_tree(parent,
                               ["#","Ім'я","Посада","Відділ","Зарплата","Дата найму","Телефон","Email"],
                               [40,180,140,140,100,120,130,160])
        self.wtree.bind("<Double-1>", lambda e: self.worker_edit())
        self.worker_reload()

    def worker_reload(self):
        if not self.wtree:
            return
        q = self.wsearch.get() if hasattr(self,'wsearch') and self.wsearch else ''
        rows = db_get_workers(q)
        for r in self.wtree.get_children():
            self.wtree.delete(r)
        for i, row in enumerate(rows):
            tag = "even" if i%2==0 else "odd"
            sal = f"{row[3]:,.0f} ₴" if row[3] else ""
            self.wtree.insert("", "end", iid=str(row[0]),
                              values=(row[0], row[1], row[7], row[2], sal, row[4], row[5], row[6]),
                              tags=(tag,))

    def worker_del(self):
        sel = self.wtree.selection()
        if not sel:
            messagebox.showwarning("Увага","Виберіть рядок.")
            return
        if not messagebox.askyesno("Підтвердження","Видалити вибраних працівників?"):
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
            messagebox.showwarning("Увага","Виберіть рядок.")
            return
        wid = int(sel[0])
        conn = db()
        row = conn.execute('SELECT * FROM workers WHERE id=?', (wid,)).fetchone()
        conn.close()
        if row:
            data = {'id':row[0],'name':row[1],'department':row[2],'salary':row[3],
                    'hire_date':row[4],'phone':row[5],'email':row[6],'position':row[7],'note':row[8]}
            self._worker_form(data)

    def _worker_form(self, existing):
        win = tk.Toplevel(self.root)
        win.title("Редагувати працівника" if existing else "Новий працівник")
        win.geometry("400x560")
        win.configure(bg=C['white'])
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="Редагувати" if existing else "Новий працівник",
                 font=("Arial",13,"bold"),
                 bg=C['white'], fg=C['sidebar']).pack(pady=(20,10), padx=20, anchor="w")

        frm = tk.Frame(win, bg=C['white'])
        frm.pack(padx=20, fill="x")

        entries = {}
        fields = [
            ("Ім'я *",        "name"),
            ("Посада",         "position"),
            ("Відділ",         "department"),
            ("Зарплата (₴)",   "salary"),
            ("Дата найму",     "hire_date"),
            ("Телефон",        "phone"),
            ("Email",          "email"),
            ("Нотатки",        "note"),
        ]
        for lbl, key in fields:
            mk_label(frm, lbl).pack(anchor="w")
            e = mk_entry(frm)
            if existing and key in existing:
                val = existing[key]
                e.insert(0, str(val) if val is not None else "")
            e.pack(fill="x", ipady=6, pady=(2,8))
            entries[key] = e

        msg = tk.Label(frm, text="", font=("Arial",9), bg=C['white'], fg=C['danger'])
        msg.pack()

        def submit():
            name = entries['name'].get().strip()
            if not name:
                msg.config(text="Ім'я обов'язкове."); return
            try:
                sal = float(entries['salary'].get().replace(',','.') or 0)
            except ValueError:
                msg.config(text="Зарплата — число."); return
            data = {
                'name':      name,
                'position':  entries['position'].get().strip(),
                'department':entries['department'].get().strip(),
                'salary':    sal,
                'hire_date': entries['hire_date'].get().strip(),
                'phone':     entries['phone'].get().strip(),
                'email':     entries['email'].get().strip(),
                'note':      entries['note'].get().strip(),
            }
            if existing:
                db_update_worker(existing['id'], data)
                log_action(f"редагував працівника: {name}")
            else:
                db_add_worker(data)
                log_action(f"додав працівника: {name}")
            self.worker_reload()
            win.destroy()

        mk_btn(frm, "Зберегти", submit).pack(fill="x", pady=(6,0))

    def worker_export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файл","*.csv")],
            initialfile="workers_export.csv"
        )
        if not path:
            return
        rows = db_get_workers()
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(["ID","Ім'я","Відділ","Зарплата","Дата найму","Телефон","Email","Посада","Нотатки"])
            for row in rows:
                w.writerow(row)
        log_action(f"експортував працівників у CSV: {path}")
        messagebox.showinfo("Готово", f"Збережено: {path}")

    def _workers_stats(self, parent):
        tk.Label(parent, text="Статистика по відділах",
                 font=("Arial",13,"bold"),
                 bg=C['bg'], fg=C['sidebar']).pack(pady=(16,12), padx=16, anchor="w")

        tree = make_tree(parent,
                         ["Відділ","Кількість","Сер. зарплата","Фонд ЗП"],
                         [240,100,160,160])

        rows, total = db_worker_stats()
        for i, row in enumerate(rows):
            dept  = row[0] or "(без відділу)"
            count = row[1]
            avg   = f"{row[2]:,.0f} ₴" if row[2] else "—"
            fund  = f"{row[3]:,.0f} ₴" if row[3] else "—"
            tag   = "even" if i%2==0 else "odd"
            tree.insert("", "end", values=(dept, count, avg, fund), tags=(tag,))

        if total:
            tree.insert("", "end", values=(
                "ВСЬОГО",
                total[0],
                f"{total[1]:,.0f} ₴" if total[1] else "—",
                f"{total[2]:,.0f} ₴" if total[2] else "—",
            ), tags=("Висока",))

    # ── Tasks page ──────────────────────────────────────────────────────────
    def pg_tasks(self):
        bar   = self._toolbar()
        admin = current_user['role'] == 'admin'

        if admin:
            mk_btn(bar, "+ Завдання", self.task_add).pack(side="left")
            mk_btn(bar, "🗑 Видалити", self.task_del,
                   bg=C['white'], fg=C['danger']).pack(side="left", padx=(8,0))

        mk_btn(bar, "✅ Виконано", self.task_done,
               bg=C['white'], fg=C['success']).pack(side="left", padx=(8,0))

        self.tfilter = tk.StringVar(value="Всі")
        mk_label(bar, "Фільтр:", size=9).pack(side="right", padx=(0,6))
        cb = ttk.Combobox(bar, textvariable=self.tfilter,
                          values=["Всі"] + PRIORITY_LEVELS + ["Виконані"],
                          state="readonly", width=12, font=("Arial",10))
        cb.pack(side="right")
        cb.bind("<<ComboboxSelected>>", lambda e: self.task_reload())

        self.ttree = make_tree(self.page,
                               ["#","Назва","Відповідальний","Пріоритет","Дедлайн","Статус","Автор"],
                               [40,230,160,100,130,100,130])
        self.task_reload()

    def task_reload(self):
        if not self.ttree:
            return
        filt = self.tfilter.get() if self.tfilter else "Всі"
        for r in self.ttree.get_children():
            self.ttree.delete(r)
        for i, row in enumerate(db_get_tasks(filt)):
            done = row[5] == "Виконано"
            tag  = "done" if done else row[3]
            self.ttree.insert("", "end", iid=str(row[0]),
                              values=row, tags=(tag,))

    def task_del(self):
        sel = self.ttree.selection()
        if not sel:
            messagebox.showwarning("Увага","Виберіть завдання.")
            return
        ids = [int(s) for s in sel]
        db_delete_tasks(ids)
        log_action(f"видалив завдання id={ids}")
        self.task_reload()

    def task_done(self):
        sel = self.ttree.selection()
        if not sel:
            messagebox.showwarning("Увага","Виберіть завдання.")
            return
        ids = [int(s) for s in sel]
        db_task_done(ids)
        log_action(f"виконав завдання id={ids}")
        self.task_reload()

    def task_add(self):
        win = tk.Toplevel(self.root)
        win.title("Нове завдання")
        win.geometry("380x430")
        win.configure(bg=C['white'])
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="Нове завдання", font=("Arial",13,"bold"),
                 bg=C['white'], fg=C['sidebar']).pack(pady=(20,10), padx=20, anchor="w")

        frm = tk.Frame(win, bg=C['white'])
        frm.pack(padx=20, fill="x")

        def fld(lbl):
            mk_label(frm, lbl).pack(anchor="w")
            e = mk_entry(frm)
            e.pack(fill="x", ipady=7, pady=(2,10))
            return e

        et = fld("Назва завдання")
        ea = fld("Відповідальний")
        ed = fld("Дедлайн (РРРР-ММ-ДД)")

        mk_label(frm, "Пріоритет").pack(anchor="w")
        pv = tk.StringVar(value="Середня")
        ttk.Combobox(frm, textvariable=pv, values=PRIORITY_LEVELS,
                     state="readonly", font=("Arial",11)).pack(fill="x", pady=(2,14))

        msg = tk.Label(frm, text="", font=("Arial",9), bg=C['white'], fg=C['danger'])
        msg.pack()

        def submit():
            title = et.get().strip()
            if not title:
                msg.config(text="Назва обов'язкова."); return
            db_add_task({
                'title':    title,
                'assignee': ea.get().strip(),
                'priority': pv.get(),
                'deadline': ed.get().strip(),
                'author':   current_user['username'],
            })
            log_action(f"додав завдання: {title}")
            self.task_reload()
            win.destroy()

        mk_btn(frm, "Зберегти", submit).pack(fill="x", pady=(4,0))

    # ── Timer page ──────────────────────────────────────────────────────────
    def pg_timer(self):
        f = tk.Frame(self.page, bg=C['bg'])
        f.pack(expand=True)
        mk_label(f, "Робочий час", size=12).pack(pady=(60,8))
        self.tlabel = tk.Label(f, text="00:00:00",
                               font=("Courier",54,"bold"),
                               bg=C['bg'], fg=C['sidebar'])
        self.tlabel.pack(pady=(0,32))
        self.tbtn = tk.Button(f, text="▶ Почати роботу",
                              font=("Arial",13,"bold"),
                              bg="#eafaf1", fg="#1a5c35",
                              relief="flat", bd=0,
                              padx=48, pady=16, cursor="hand2",
                              command=self.toggle_work)
        self.tbtn.pack()
        self.tstatus = tk.Label(f, text="", font=("Arial",9),
                                bg=C['bg'], fg=C['muted'])
        self.tstatus.pack(pady=(14,0))

    def toggle_work(self):
        if not self.working:
            self.work_start = datetime.datetime.now()
            self.working    = True
            self.tbtn.config(text="⏹ Завершити роботу", bg="#fdecea", fg="#9b2a2a")
            self.tstatus.config(text=f"Почато: {self.work_start.strftime('%H:%M:%S')}")
            log_action("почав роботу")
        else:
            h, m, s = self._elapsed()
            messagebox.showinfo("Час роботи", f"Ви відпрацювали:\n{h} год {m} хв {s} сек")
            log_action(f"завершив роботу ({h}г {m}хв {s}с)")
            self.working    = False
            self.work_start = None
            for widget, cfg in [
                (self.tlabel,  {"text":"00:00:00"}),
                (self.tbtn,    {"text":"▶ Почати роботу","bg":"#eafaf1","fg":"#1a5c35"}),
                (self.tstatus, {"text":""}),
            ]:
                if widget:
                    try: widget.config(**cfg)
                    except tk.TclError: pass

    def _elapsed(self):
        diff   = datetime.datetime.now() - self.work_start
        h, rem = divmod(int(diff.total_seconds()), 3600)
        m, s   = divmod(rem, 60)
        return h, m, s

    def _tick(self):
        if self.working and self.work_start and self.tlabel:
            h, m, s = self._elapsed()
            try: self.tlabel.config(text=f"{h:02}:{m:02}:{s:02}")
            except tk.TclError: pass
        self.root.after(1000, self._tick)

    # ── Logs page ────────────────────────────────────────────────────────────
    def pg_logs(self):
        tree = make_tree(self.page, ["Час","Користувач","Дія"], [180,160,560])
        for i, row in enumerate(db_get_logs()):
            ts  = (row[0] or '')[:19].replace("T"," ")
            tag = "even" if i%2==0 else "odd"
            tree.insert("", "end", values=(ts, row[1] or '', row[2] or ''), tags=(tag,))

    # ── FAQ page ─────────────────────────────────────────────────────────────
    def pg_faq(self):
        outer = tk.Frame(self.page, bg=C['bg'])
        outer.pack(fill="both", expand=True)
        left  = tk.Frame(outer, bg=C['white'], width=240)
        left.pack(side="left", fill="y", padx=(0,12))
        left.pack_propagate(False)
        right = tk.Frame(outer, bg=C['white'])
        right.pack(side="left", fill="both", expand=True)

        mk_label(left, "РОЗДІЛИ", size=8, bold=True).pack(pady=(16,8), padx=16, anchor="w")

        title_lbl = tk.Label(right, text="", font=("Arial",13,"bold"),
                             bg=C['white'], fg=C['sidebar'], anchor="w")
        title_lbl.pack(pady=(20,4), padx=24, anchor="w")
        body_txt  = tk.Text(right, font=("Arial",11), bg=C['white'], fg=C['text'],
                            relief="flat", bd=0, wrap="word", state="disabled",
                            cursor="arrow", spacing1=4, spacing3=4)
        body_txt.pack(fill="both", expand=True, padx=24, pady=(0,20))

        def show(q, a):
            title_lbl.config(text=q)
            body_txt.config(state="normal")
            body_txt.delete("1.0","end")
            body_txt.insert("1.0", a)
            body_txt.config(state="disabled")

        first = True
        for section, pairs in FAQ_SECTIONS:
            tk.Label(left, text=section, font=("Arial",9,"bold"),
                     bg=C['white'], fg=C['sidebar']).pack(anchor="w", padx=16, pady=(12,2))
            tk.Frame(left, bg=C['sep'], height=1).pack(fill="x", padx=16, pady=(0,4))
            for q, a in pairs:
                b = tk.Button(left, text=f"  {q}", font=("Arial",9),
                              bg=C['white'], fg=C['text'], relief="flat", bd=0,
                              pady=6, padx=8, anchor="w", cursor="hand2",
                              wraplength=210, justify="left",
                              command=lambda qq=q, aa=a: show(qq, aa))
                b.pack(fill="x", padx=8)
                if first: show(q, a); first = False

    # ── Admin page ───────────────────────────────────────────────────────────
    def pg_admin(self):
        if current_user['role'] != 'admin':
            return
        nb = ttk.Notebook(self.page)
        nb.pack(fill="both", expand=True)
        tu = tk.Frame(nb, bg=C['bg'])
        tw = tk.Frame(nb, bg=C['bg'])
        tt = tk.Frame(nb, bg=C['bg'])
        nb.add(tu, text="  Користувачі  ")
        nb.add(tw, text="  Працівники  ")
        nb.add(tt, text="  Завдання  ")
        self._admin_users(tu)
        self._admin_workers(tw)
        self._admin_tasks(tt)

    def _admin_users(self, parent):
        bar = tk.Frame(parent, bg=C['bg'])
        utree_h = [None]
        bar.pack(fill="x", pady=(0,10), padx=4)
        mk_btn(bar, "+ Створити",
               lambda: self._create_user_dialog(utree_h[0])).pack(side="left")
        mk_btn(bar, "Зробити адміном",
               lambda: self._au_role(utree_h[0],'admin'),
               bg=C['warn']).pack(side="left", padx=(8,0))
        mk_btn(bar, "Зробити user",
               lambda: self._au_role(utree_h[0],'user'),
               bg=C['ibg'], fg=C['text']).pack(side="left", padx=(8,0))
        mk_btn(bar, "🗑 Видалити",
               lambda: self._au_delete(utree_h[0]),
               bg=C['danger']).pack(side="left", padx=(8,0))
        mk_btn(bar, "🔄 Оновити",
               lambda: self._au_reload(utree_h[0])).pack(side="right")

        tree = make_tree(parent,
                         ["ID","Логін","Роль","Телефон","Email","Організація","Реєстрація"],
                         [40,150,80,130,180,160,170])
        utree_h[0] = tree
        self._au_reload(tree)

    def _create_user_dialog(self, tree):
        win = tk.Toplevel(self.root)
        win.title("Створити користувача")
        win.geometry("340x340")
        win.configure(bg=C['white'])
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="Новий користувач", font=("Arial",13,"bold"),
                 bg=C['white'], fg=C['sidebar']).pack(pady=(20,12), padx=20, anchor="w")

        frm = tk.Frame(win, bg=C['white'])
        frm.pack(padx=20, fill="x")

        mk_label(frm, "Логін").pack(anchor="w")
        eu = mk_entry(frm)
        eu.pack(fill="x", ipady=7, pady=(2,10))

        mk_label(frm, "Пароль").pack(anchor="w")
        ep = mk_entry(frm, show="*")
        ep.pack(fill="x", ipady=7, pady=(2,10))

        mk_label(frm, "Роль").pack(anchor="w")
        rv = tk.StringVar(value="user")
        ttk.Combobox(frm, textvariable=rv, values=["user","admin"],
                     state="readonly", font=("Arial",11)).pack(fill="x", pady=(2,14))

        msg = tk.Label(frm, text="", font=("Arial",9), bg=C['white'], fg=C['danger'])
        msg.pack()

        def submit():
            u = eu.get().strip(); p = ep.get()
            if not u or not p:
                msg.config(text="Заповніть всі поля."); return
            if len(p) < 4:
                msg.config(text="Пароль мінімум 4 символи."); return
            if db_create_user(u, p, rv.get()):
                log_action(f"(адмін) створив юзера: {u} роль={rv.get()}")
                self._au_reload(tree)
                win.destroy()
            else:
                msg.config(text="Логін вже зайнятий.")

        mk_btn(frm, "Створити", submit).pack(fill="x", pady=(8,0))

    def _au_reload(self, tree):
        if not tree: return
        for r in tree.get_children(): tree.delete(r)
        for i, row in enumerate(db_get_users()):
            ts  = (row[6] or '')[:19].replace("T"," ")
            tag = "even" if i%2==0 else "odd"
            tree.insert("", "end", iid=str(row[0]),
                        values=(row[0],row[1],row[2],row[3] or '',row[4] or '',row[5] or '',ts),
                        tags=(tag,))

    def _au_role(self, tree, role):
        if not tree: return
        sel = tree.selection()
        if not sel: messagebox.showwarning("Увага","Виберіть користувача."); return
        for s in sel:
            db_set_role(int(s), role)
            log_action(f"змінив роль user id={s} на {role}")
        self._au_reload(tree)

    def _au_delete(self, tree):
        if not tree: return
        sel = tree.selection()
        if not sel: messagebox.showwarning("Увага","Виберіть користувача."); return
        for s in sel:
            if int(s) == current_user['id']:
                messagebox.showwarning("Увага","Не можна видалити себе."); return
        if not messagebox.askyesno("Підтвердження","Видалити?"): return
        for s in sel:
            db_delete_user(int(s))
            log_action(f"видалив user id={s}")
        self._au_reload(tree)

    def _admin_workers(self, parent):
        bar = tk.Frame(parent, bg=C['bg'])
        wh  = [None]
        bar.pack(fill="x", pady=(0,10), padx=4)
        mk_btn(bar, "+ Додати", self.worker_add).pack(side="left")
        mk_btn(bar, "🗑 Видалити",
               lambda: self._aw_delete(wh[0]), bg=C['danger']).pack(side="left", padx=(8,0))

        tree = make_tree(parent,
                         ["#","Ім'я","Посада","Відділ","Зарплата","Дата найму"],
                         [40,200,140,160,120,140])
        wh[0] = tree
        for i, row in enumerate(db_get_workers()):
            sal = f"{row[3]:,.0f} ₴" if row[3] else ""
            tag = "even" if i%2==0 else "odd"
            tree.insert("", "end", iid=str(row[0]),
                        values=(row[0],row[1],row[7],row[2],sal,row[4]), tags=(tag,))

    def _aw_delete(self, tree):
        if not tree: return
        sel = tree.selection()
        if not sel: messagebox.showwarning("Увага","Виберіть рядок."); return
        if not messagebox.askyesno("Підтвердження","Видалити?"): return
        ids = [int(s) for s in sel]
        db_delete_workers(ids)
        log_action(f"(адмін) видалив працівників id={ids}")
        for s in sel: tree.delete(s)

    def _admin_tasks(self, parent):
        bar = tk.Frame(parent, bg=C['bg'])
        th  = [None]
        bar.pack(fill="x", pady=(0,10), padx=4)
        mk_btn(bar, "+ Завдання", self.task_add).pack(side="left")
        mk_btn(bar, "🗑 Видалити",
               lambda: self._at_delete(th[0]), bg=C['danger']).pack(side="left", padx=(8,0))
        mk_btn(bar, "✅ Виконано",
               lambda: self._at_done(th[0]),   bg=C['success']).pack(side="left", padx=(8,0))

        tree = make_tree(parent,
                         ["#","Назва","Відповідальний","Пріоритет","Дедлайн","Статус","Автор"],
                         [40,220,150,100,120,100,130])
        th[0] = tree
        for i, row in enumerate(db_get_tasks()):
            done = row[5] == "Виконано"
            tag  = "done" if done else row[3]
            tree.insert("", "end", iid=str(row[0]), values=row, tags=(tag,))

    def _at_delete(self, tree):
        if not tree: return
        sel = tree.selection()
        if not sel: return
        ids = [int(s) for s in sel]
        db_delete_tasks(ids)
        for s in sel: tree.delete(s)
        log_action(f"(адмін) видалив завдання id={ids}")

    def _at_done(self, tree):
        if not tree: return
        sel = tree.selection()
        if not sel: return
        ids = [int(s) for s in sel]
        db_task_done(ids)
        for s in sel:
            vals    = list(tree.item(s,'values'))
            vals[5] = "Виконано"
            tree.item(s, values=vals, tags=("done",))
        log_action(f"(адмін) виконав завдання id={ids}")

    def logout(self):
        clear_session()
        log_action("вийшов з системи")
        self.root.destroy()
        LoginWindow()


# ── Entry point ───────────────────────────────────────────────────────────────
db_init()
LoginWindow()