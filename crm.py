import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import logging
import hashlib
import sqlite3
import json
import csv
import os

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR     = os.path.join(BASE_DIR, 'logs')
DATA_DIR     = os.path.join(BASE_DIR, 'data')
LOG_FILE     = os.path.join(LOGS_DIR, 'crm_log.txt')
SESSION_FILE = os.path.join(DATA_DIR, 'session.json')
DB_PATH      = os.path.join(BASE_DIR, 'crm.db')

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

current_user    = None
PRIORITY_LEVELS = ['Критична', 'Висока', 'Середня', 'Низька']
TASK_STATUSES   = ['Активне', 'В роботі', 'На паузі', 'Виконано']
DEPARTMENTS     = ['IT', 'HR', 'Фінанси', 'Маркетинг', 'Продажі', 'Виробництво', 'Логістика', 'Адміністрація']

# ── Themes ───────────────────────────────────────────────────────────────────
THEMES = {
    'light': {
        'bg':       '#F4F6FA',
        'sidebar':  '#1E2235',
        'side2':    '#2C3152',
        'side_btn': '#252A45',
        'white':    '#FFFFFF',
        'text':     '#1A1D2E',
        'text2':    '#555870',
        'muted':    '#9EA3B8',
        'ibg':      '#F0F2F8',
        'border':   '#E2E5EF',
        'accent':   '#4361EE',
        'accent2':  '#3A56D4',
        'danger':   '#E63946',
        'success':  '#2DC653',
        'warn':     '#F4A261',
        'info':     '#4CC9F0',
        'tree_bg':  '#FFFFFF',
        'tree_alt': '#F8F9FC',
        'tree_sel': '#EBF0FF',
        'tree_sfg': '#1E2235',
        'card':     '#FFFFFF',
        'tag_a':    '#4361EE',
        'tag_b':    '#E63946',
        'tag_c':    '#2DC653',
        'tag_d':    '#F4A261',
    },
    'dark': {
        'bg':       '#12141E',
        'sidebar':  '#0B0D15',
        'side2':    '#1E2235',
        'side_btn': '#1A1D30',
        'white':    '#1A1D2E',
        'text':     '#E4E6F0',
        'text2':    '#9EA3C0',
        'muted':    '#5A5F7A',
        'ibg':      '#0F1120',
        'border':   '#252840',
        'accent':   '#4361EE',
        'accent2':  '#3A56D4',
        'danger':   '#E63946',
        'success':  '#2DC653',
        'warn':     '#F4A261',
        'info':     '#4CC9F0',
        'tree_bg':  '#1A1D2E',
        'tree_alt': '#1E2138',
        'tree_sel': '#252A52',
        'tree_sfg': '#E4E6F0',
        'card':     '#1A1D2E',
        'tag_a':    '#4361EE',
        'tag_b':    '#E63946',
        'tag_c':    '#2DC653',
        'tag_d':    '#F4A261',
    }
}
C = THEMES['light']

FAQ_SECTIONS = [
    ("Вхід у систему", [
        ("Як увійти?",
         "Введіть логін та пароль на головному екрані.\n"
         "Логін адміна за замовчуванням: admin / admin.\n"
         "Після входу система запитає додаткові дані профілю.\n\n"
         "Порада: Увімкніть «Запам'ятати пристрій» — тоді наступного разу\n"
         "входити знову не потрібно (сесія зберігається 30 днів)."),
        ("Забув пароль?",
         "Зверніться до адміністратора — він може видалити акаунт\n"
         "та створити новий через Адмінку > Користувачі > Створити."),
        ("Блокування після 3 спроб?",
         "Якщо ввести неправильний пароль 3 рази поспіль —\n"
         "вхід буде заблоковано на 5 хвилин.\n"
         "Зачекайте або зверніться до адміна.\n"
         "Порада: Після 5 хвилин блокування можна спробувати знову.\n"
         "Порада: Адмін може скинути блокування через Адмінку > Користувачі > Редагувати. (Але якщо не було підозрілої активності)"),
    ]),
    ("Працівники", [
        ("Як додати працівника?",
         "Адмін: Працівники > Додати > заповнити форму > Зберегти.\n"
         "Звичайний користувач може лише переглядати список."),
        ("Як редагувати працівника?",
         "Виберіть рядок у таблиці (подвійний клік або кнопка 'Редагувати').\n"
         "Доступно лише адміну."),
        ("Як шукати?",
         "Введіть ім'я, посаду або відділ у поле 'Пошук' над таблицею.\n"
         "Фільтрація відбувається в реальному часі."),
        ("Як експортувати в CSV?",
         "Кнопка 'Експорт CSV' → оберіть місце збереження файлу."),
        ("Статистика?",
         "Вкладка 'Статистика' показує кількість по відділах,\n"
         "середню зарплату та загальний фонд оплати праці.\n"
         "Порада: Натисніть на рядок у таблиці статистики —\n"
         "система покаже детальну інформацію."),
    ]),
    ("Завдання", [
        ("Як створити завдання?",
         "Адмін: Завдання > Додати > заповнити назву,\n"
         "відповідального, дедлайн та пріоритет > Зберегти."),
        ("Рівні пріоритету:",
         "Критична — негайно\nВисока — найближчим часом\n"
         "Середня — планово\nНизька — при нагоді\n\n"
         "Колір рядка в таблиці відповідає пріоритету."),
        ("Як змінити статус?",
         "Виберіть завдання і натисніть 'В роботу', 'Пауза' або 'Виконано'.\n"
         "Також можна редагувати подвійним кліком.\n"
         "Порада: Виконані завдання можна переглянути у фільтрі 'Виконані'.\n"
         "Порада: Завдання можна сортувати за пріоритетом, статусом або пошуком.\n"
         "Порада: Адмін може змінювати будь-які поля, звичайний користувач лише статус."),
    ]),
    ("Таймер", [
        ("Як використовувати таймер?",
         "Перейдіть на сторінку 'Таймер' > натисніть 'Почати роботу'.\n"
         "Натисніть 'Завершити роботу' — система покаже тривалість сесії\n"
         "та збереже запис у журналі.\n"
         "Можна переглянути історію сесій у таблиці нижче.\n"
         "Порада: Таймер працює лише для зареєстрованих користувачів.\n"
         "І це потрібно тільки для обліку робочого часу, не для контролю.\n"
         "Ви можете закрити програму — таймер продовжить працювати у фоновому режимі.\n"
         "Але якщо комп'ютер вимкнеться, сесія не збережеться, та не буде врахована у статистиці.\n"
         "Порада для адміну: у вкладці 'Аналітика' можна переглянути загальний час роботи всіх користувачів."),
    ]),
    ("Адмінка", [
        ("Що може адмін?",
         "- Створювати нових користувачів\n"
         "- Змінювати ролі (admin / user)\n"
         "- Видаляти користувачів\n"
         "- Керувати працівниками і завданнями\n"
         "- Переглядати повний журнал дій\n",
         "- Переглядати аналітику системи\n"
         "Порада: Адмін може скинути блокування після 3 невдалих спроб входу.\n"
         "Порада: Адмін може змінювати будь-які поля у працівниках та завданнях, звичайний користувач лише статус завдання.\n"
         "Порада: Адмін може переглядати журнал дій та аналітику, звичайний користувач — лише свої дії та статистику по собі."),
    ]),
]

# ── DB ────────────────────────────────────────────────────────────────────────
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def db_init():
    conn = db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT UNIQUE NOT NULL,
            password     TEXT NOT NULL,
            role         TEXT DEFAULT "user",
            phone        TEXT DEFAULT "",
            email        TEXT DEFAULT "",
            org          TEXT DEFAULT "",
            created      TEXT,
            locked_until TEXT DEFAULT "",
            last_login   TEXT DEFAULT ""
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            username     TEXT PRIMARY KEY,
            count        INTEGER DEFAULT 0,
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
            note       TEXT DEFAULT "",
            status     TEXT DEFAULT "Активний"
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
            created   TEXT,
            note      TEXT DEFAULT "",
            category  TEXT DEFAULT ""
        )
    ''')
    for sql in [
        '''CREATE TABLE IF NOT EXISTS logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username  TEXT,
            action    TEXT
        )''',
        '''CREATE TABLE IF NOT EXISTS time_sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT,
            started    TEXT,
            ended      TEXT,
            duration   INTEGER
        )''',
    ]:
        try:
            conn.execute(sql)
        except Exception:
            pass

    # Migrations
    existing_users = [r[1] for r in conn.execute('PRAGMA table_info(users)').fetchall()]
    for col, dflt in [('phone','""'),('email','""'),('org','""'),('locked_until','""'),('last_login','""')]:
        if col not in existing_users:
            try:
                conn.execute(f'ALTER TABLE users ADD COLUMN {col} TEXT DEFAULT {dflt}')
            except Exception:
                pass

    existing_workers = [r[1] for r in conn.execute('PRAGMA table_info(workers)').fetchall()]
    if 'status' not in existing_workers:
        try:
            conn.execute('ALTER TABLE workers ADD COLUMN status TEXT DEFAULT "Активний"')
        except Exception:
            pass

    existing_tasks = [r[1] for r in conn.execute('PRAGMA table_info(tasks)').fetchall()]
    for col, dflt in [('note','""'),('category','""')]:
        if col not in existing_tasks:
            try:
                conn.execute(f'ALTER TABLE tasks ADD COLUMN {col} TEXT DEFAULT {dflt}')
            except Exception:
                pass

    if not conn.execute('SELECT id FROM users WHERE username="admin"').fetchone():
        conn.execute(
            'INSERT INTO users (username,password,role,created) VALUES (?,?,?,?)',
            ('admin', hash_pw('admin'), 'admin', datetime.datetime.now().isoformat())
        )

    conn.commit()
    conn.close()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ── Login attempts / locking ──────────────────────────────────────────────────
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
        conn.execute('UPDATE login_attempts SET count=?, last_attempt=? WHERE username=?',
                     (existing[0]+1, now, username))
    else:
        conn.execute('INSERT INTO login_attempts (username, count, last_attempt) VALUES (?,?,?)',
                     (username, 1, now))
    conn.commit(); conn.close()

def reset_attempts(username):
    conn = db()
    conn.execute('DELETE FROM login_attempts WHERE username=?', (username,))
    conn.commit(); conn.close()

def is_locked(username):
    count, last = get_attempts(username)
    if count >= 3 and last:
        dt = datetime.datetime.fromisoformat(last)
        if (datetime.datetime.now() - dt).total_seconds() < 300:
            remaining = 300 - int((datetime.datetime.now() - dt).total_seconds())
            return True, remaining
        else:
            reset_attempts(username)
    return False, 0

# ── Session ───────────────────────────────────────────────────────────────────
def save_session(username):
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump({'username': username, 'saved_at': datetime.datetime.now().isoformat()}, f)

def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        saved = datetime.datetime.fromisoformat(data['saved_at'])
        if (datetime.datetime.now() - saved).days < 30:
            return data.get('username')
    except Exception:
        pass
    return None

def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# ── User DB ───────────────────────────────────────────────────────────────────
def db_login(username, password):
    conn = db()
    row = conn.execute(
        'SELECT id,username,role,phone,email,org FROM users WHERE username=? AND password=?',
        (username, hash_pw(password))
    ).fetchone()
    if row:
        conn.execute('UPDATE users SET last_login=? WHERE id=?',
                     (datetime.datetime.now().isoformat(), row[0]))
        conn.commit()
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

def db_change_password(uid, new_password):
    conn = db()
    conn.execute('UPDATE users SET password=? WHERE id=?', (hash_pw(new_password), uid))
    conn.commit(); conn.close()

def db_get_users():
    conn = db()
    rows = conn.execute(
        'SELECT id,username,role,phone,email,org,created,last_login FROM users ORDER BY id'
    ).fetchall()
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

def db_get_logs(search='', limit=500):
    conn = db()
    if search:
        q = f"%{search.lower()}%"
        rows = conn.execute(
            'SELECT timestamp,username,action FROM logs WHERE lower(username) LIKE ? OR lower(action) LIKE ? ORDER BY timestamp DESC LIMIT ?',
            (q, q, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            'SELECT timestamp,username,action FROM logs ORDER BY timestamp DESC LIMIT ?', (limit,)
        ).fetchall()
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

# ── Workers DB ────────────────────────────────────────────────────────────────
def db_get_workers(search='', dept_filter='', status_filter=''):
    conn = db()
    q = f"%{search.lower()}%"
    conditions = ['(lower(name) LIKE ? OR lower(department) LIKE ? OR lower(position) LIKE ?)']
    params = [q, q, q]
    if dept_filter and dept_filter != 'Всі':
        conditions.append('department=?')
        params.append(dept_filter)
    if status_filter and status_filter != 'Всі':
        conditions.append('status=?')
        params.append(status_filter)
    where = ' AND '.join(conditions)
    rows = conn.execute(
        f'SELECT id,name,department,salary,hire_date,phone,email,position,note,status FROM workers WHERE {where} ORDER BY name',
        params
    ).fetchall()
    conn.close()
    return rows

def db_add_worker(data):
    conn = db()
    conn.execute(
        '''INSERT INTO workers (name,department,salary,hire_date,phone,email,position,note,status)
           VALUES (?,?,?,?,?,?,?,?,?)''',
        (data['name'], data['department'], data.get('salary',0),
         data['hire_date'], data['phone'], data['email'],
         data['position'], data['note'], data.get('status','Активний'))
    )
    conn.commit(); conn.close()

def db_update_worker(wid, data):
    conn = db()
    conn.execute(
        '''UPDATE workers SET name=?,department=?,salary=?,hire_date=?,
           phone=?,email=?,position=?,note=?,status=? WHERE id=?''',
        (data['name'], data['department'], data.get('salary',0),
         data['hire_date'], data['phone'], data['email'],
         data['position'], data['note'], data.get('status','Активний'), wid)
    )
    conn.commit(); conn.close()

def db_delete_workers(ids):
    conn = db()
    conn.executemany('DELETE FROM workers WHERE id=?', [(i,) for i in ids])
    conn.commit(); conn.close()

def db_worker_stats():
    conn = db()
    rows = conn.execute(
        'SELECT department, COUNT(*), AVG(salary), SUM(salary) FROM workers GROUP BY department ORDER BY COUNT(*) DESC'
    ).fetchall()
    total = conn.execute('SELECT COUNT(*), AVG(salary), SUM(salary) FROM workers').fetchone()
    conn.close()
    return rows, total

def db_get_departments():
    conn = db()
    rows = conn.execute('SELECT DISTINCT department FROM workers WHERE department != "" ORDER BY department').fetchall()
    conn.close()
    return [r[0] for r in rows]

# ── Tasks DB ──────────────────────────────────────────────────────────────────
def db_get_tasks(filt='Всі', search=''):
    conn = db()
    conditions = []
    params = []
    if filt == 'Виконані':
        conditions.append("status='Виконано'")
    elif filt in PRIORITY_LEVELS:
        conditions.append('priority=?')
        params.append(filt)
    elif filt in TASK_STATUSES:
        conditions.append('status=?')
        params.append(filt)
    if search:
        q = f"%{search.lower()}%"
        conditions.append('(lower(title) LIKE ? OR lower(assignee) LIKE ?)')
        params.extend([q, q])
    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
    rows = conn.execute(
        f'SELECT id,title,assignee,priority,deadline,status,author,note,category FROM tasks {where} ORDER BY CASE priority WHEN "Критична" THEN 1 WHEN "Висока" THEN 2 WHEN "Середня" THEN 3 ELSE 4 END, id',
        params
    ).fetchall()
    conn.close()
    return rows

def db_add_task(data):
    conn = db()
    conn.execute(
        'INSERT INTO tasks (title,assignee,priority,deadline,status,author,created,note,category) VALUES (?,?,?,?,?,?,?,?,?)',
        (data['title'], data['assignee'], data['priority'],
         data['deadline'], data.get('status','Активне'), data['author'],
         datetime.datetime.now().isoformat(), data.get('note',''), data.get('category',''))
    )
    conn.commit(); conn.close()

def db_update_task(tid, data):
    conn = db()
    conn.execute(
        '''UPDATE tasks SET title=?,assignee=?,priority=?,deadline=?,status=?,note=?,category=? WHERE id=?''',
        (data['title'], data['assignee'], data['priority'],
         data['deadline'], data['status'], data.get('note',''), data.get('category',''), tid)
    )
    conn.commit(); conn.close()

def db_delete_tasks(ids):
    conn = db()
    conn.executemany('DELETE FROM tasks WHERE id=?', [(i,) for i in ids])
    conn.commit(); conn.close()

def db_task_status(ids, status):
    conn = db()
    conn.executemany(f"UPDATE tasks SET status=? WHERE id=?", [(status, i) for i in ids])
    conn.commit(); conn.close()

def db_get_analytics():
    conn = db()
    workers_total  = conn.execute('SELECT COUNT(*) FROM workers').fetchone()[0]
    tasks_total    = conn.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]
    tasks_done     = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='Виконано'").fetchone()[0]
    tasks_active   = conn.execute("SELECT COUNT(*) FROM tasks WHERE status!='Виконано'").fetchone()[0]
    users_total    = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    avg_salary     = conn.execute('SELECT AVG(salary) FROM workers').fetchone()[0] or 0
    total_salary   = conn.execute('SELECT SUM(salary) FROM workers').fetchone()[0] or 0
    by_priority    = conn.execute(
        "SELECT priority, COUNT(*) FROM tasks WHERE status!='Виконано' GROUP BY priority"
    ).fetchall()
    by_dept        = conn.execute(
        'SELECT department, COUNT(*) FROM workers WHERE department!="" GROUP BY department ORDER BY COUNT(*) DESC LIMIT 5'
    ).fetchall()
    recent_logs    = conn.execute(
        'SELECT COUNT(*) FROM logs WHERE timestamp > ?',
        ((datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),)
    ).fetchone()[0]
    conn.close()
    return {
        'workers': workers_total,
        'tasks': tasks_total,
        'tasks_done': tasks_done,
        'tasks_active': tasks_active,
        'users': users_total,
        'avg_salary': avg_salary,
        'total_salary': total_salary,
        'by_priority': dict(by_priority),
        'by_dept': by_dept,
        'recent_logs': recent_logs,
    }

def db_save_time_session(username, started, ended, duration):
    conn = db()
    conn.execute(
        'INSERT INTO time_sessions (username,started,ended,duration) VALUES (?,?,?,?)',
        (username, started, ended, duration)
    )
    conn.commit(); conn.close()

def db_get_time_sessions(username=None):
    conn = db()
    if username:
        rows = conn.execute(
            'SELECT username,started,ended,duration FROM time_sessions WHERE username=? ORDER BY started DESC LIMIT 50',
            (username,)
        ).fetchall()
    else:
        rows = conn.execute(
            'SELECT username,started,ended,duration FROM time_sessions ORDER BY started DESC LIMIT 100'
        ).fetchall()
    conn.close()
    return rows

# ── UI Helpers ────────────────────────────────────────────────────────────────
def mk_entry(parent, show=None, width=None, placeholder=''):
    kw = dict(font=("Segoe UI", 10), relief="flat",
              bg=C['ibg'], fg=C['text'],
              insertbackground=C['text'],
              highlightthickness=1,
              highlightbackground=C['border'],
              highlightcolor=C['accent'])
    if show:
        kw['show'] = show
    if width:
        kw['width'] = width
    e = tk.Entry(parent, **kw)
    return e

def mk_label(parent, text, size=9, color=None, bold=False, anchor='w'):
    font = ("Segoe UI", size, "bold") if bold else ("Segoe UI", size)
    return tk.Label(parent, text=text, font=font,
                    bg=parent.cget('bg'), fg=color or C['muted'], anchor=anchor)

def mk_btn(parent, text, cmd, bg=None, fg='white', padx=14, pady=8, width=None):
    kw = dict(
        text=text, command=cmd,
        font=("Segoe UI", 9, "bold"),
        bg=bg or C['accent'], fg=fg,
        relief="flat", bd=0,
        padx=padx, pady=pady,
        cursor="hand2",
        activebackground=C['accent2'] if (bg is None or bg == C['accent']) else C['border'],
        activeforeground=fg
    )
    if width:
        kw['width'] = width
    return tk.Button(parent, **kw)

def mk_sep(parent, orient='h', color=None):
    if orient == 'h':
        return tk.Frame(parent, bg=color or C['border'], height=1)
    else:
        return tk.Frame(parent, bg=color or C['border'], width=1)

def make_tree(parent, columns, widths, height=None):
    style_name = f"CRM{id(parent)}.Treeview"
    st = ttk.Style()
    st.theme_use("clam")
    st.configure(style_name,
                 background=C['tree_bg'], foreground=C['text'],
                 rowheight=34, fieldbackground=C['tree_bg'],
                 font=("Segoe UI", 9), borderwidth=0,
                 relief="flat")
    st.configure(f"{style_name}.Heading",
                 background=C['ibg'], foreground=C['muted'],
                 font=("Segoe UI", 8, "bold"), relief="flat",
                 padding=(8, 6))
    st.map(style_name,
           background=[("selected", C['tree_sel'])],
           foreground=[("selected", C['tree_sfg'])])
    st.layout(style_name, [('Treeview.treearea', {'sticky': 'nswe'})])

    wrap = tk.Frame(parent, bg=C['white'], highlightthickness=1,
                    highlightbackground=C['border'])
    wrap.pack(fill="both", expand=True)

    kw = dict(columns=columns, show="headings", style=style_name, selectmode="extended")
    if height:
        kw['height'] = height
    tree = ttk.Treeview(wrap, **kw)
    vsb  = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
    hsb  = ttk.Scrollbar(wrap, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    for col, w in zip(columns, widths):
        tree.heading(col, text=col, anchor='w')
        tree.column(col, width=w, minwidth=40, anchor="w", stretch=False)

    tree.tag_configure("even",     background=C['tree_bg'])
    tree.tag_configure("odd",      background=C['tree_alt'])
    tree.tag_configure("done",     foreground=C['muted'])
    tree.tag_configure("Критична", foreground=C['danger'])
    tree.tag_configure("Висока",   foreground=C['warn'])
    tree.tag_configure("Середня",  foreground='#C08010')
    tree.tag_configure("Низька",   foreground=C['success'])
    tree.tag_configure("admin",    foreground=C['accent'])

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    wrap.grid_rowconfigure(0, weight=1)
    wrap.grid_columnconfigure(0, weight=1)

    return tree

# ── Modal base ────────────────────────────────────────────────────────────────
class Modal:
    """A clean, centered modal dialog with a consistent look."""
    def __init__(self, parent, title, width=480, height=None):
        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.configure(bg=C['white'])
        self.win.resizable(False, False)
        self.win.grab_set()
        self.win.transient(parent)

        if width:
            geo = f"{width}x{height}" if height else str(width)
            self.win.geometry(geo)

        # Header stripe
        tk.Frame(self.win, bg=C['accent'], height=4).pack(fill="x")

        # Title
        tk.Label(self.win, text=title, font=("Segoe UI", 13, "bold"),
                 bg=C['white'], fg=C['text']).pack(pady=(20, 2), padx=24, anchor="w")
        mk_sep(self.win).pack(fill="x", padx=24, pady=(8, 0))

        self.body = tk.Frame(self.win, bg=C['white'])
        self.body.pack(fill="both", expand=True, padx=24, pady=16)

        self.footer = tk.Frame(self.win, bg=C['ibg'])
        self.footer.pack(fill="x")
        mk_sep(self.footer, color=C['border']).pack(fill="x")

        self.btn_row = tk.Frame(self.footer, bg=C['ibg'])
        self.btn_row.pack(fill="x", padx=16, pady=10)

    def add_ok(self, text="Зберегти", cmd=None, cancel=True):
        if cancel:
            mk_btn(self.btn_row, "Скасувати",
                   self.win.destroy, bg=C['ibg'], fg=C['text'],
                   pady=7).pack(side="right", padx=(6, 0))
        mk_btn(self.btn_row, text, cmd or self.win.destroy,
               pady=7).pack(side="right")

    def field(self, label, key=None, show=None, default='', widget=None):
        """Add a labelled field to the body. Returns the entry widget."""
        mk_label(self.body, label, size=9).pack(anchor="w", pady=(8, 2))
        if widget is not None:
            widget.pack(fill="x", ipady=0)
            return widget
        e = mk_entry(self.body, show=show)
        if default:
            e.insert(0, str(default))
        e.pack(fill="x", ipady=7)
        return e

    def combobox(self, label, values, default='', readonly=True):
        mk_label(self.body, label, size=9).pack(anchor="w", pady=(8, 2))
        v = tk.StringVar(value=default or (values[0] if values else ''))
        cb = ttk.Combobox(self.body, textvariable=v, values=values,
                          state="readonly" if readonly else "normal",
                          font=("Segoe UI", 10))
        cb.pack(fill="x", ipady=5)
        return v

    def textarea(self, label, default='', height=3):
        mk_label(self.body, label, size=9).pack(anchor="w", pady=(8, 2))
        t = tk.Text(self.body, font=("Segoe UI", 10), height=height,
                    relief="flat", bg=C['ibg'], fg=C['text'],
                    insertbackground=C['text'],
                    highlightthickness=1,
                    highlightbackground=C['border'],
                    highlightcolor=C['accent'])
        if default:
            t.insert("1.0", default)
        t.pack(fill="x")
        return t

    def error(self, text=''):
        if not hasattr(self, '_err_lbl'):
            self._err_lbl = tk.Label(self.body, text='', font=("Segoe UI", 9),
                                     bg=C['white'], fg=C['danger'], wraplength=420)
            self._err_lbl.pack(pady=(8, 0))
        self._err_lbl.config(text=text)


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN WINDOW
# ══════════════════════════════════════════════════════════════════════════════
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
                global current_user
                current_user = user
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
        # Top accent bar
        tk.Frame(self.win, bg=C['accent'], height=5).pack(fill="x")

        # Logo area
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
            left = max(0, 3 - count)
            if left == 0:
                self.msg.config(text="Акаунт заблоковано на 5 хвилин!")
            else:
                self.msg.config(text=f"Невірний логін або пароль.\nЗалишилось спроб: {left}")

    def open_faq(self):
        FAQWindow(self.win)


# ══════════════════════════════════════════════════════════════════════════════
#  FAQ WINDOW
# ══════════════════════════════════════════════════════════════════════════════
class FAQWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Інструкція — CRM System")
        self.win.geometry("780x580")
        self.win.configure(bg=C['white'])
        self.win.grab_set()
        self._center(parent)
        self._build()

    def _center(self, parent):
        self.win.update_idletasks()
        w, h = 780, 580
        pw = parent.winfo_rootx() + parent.winfo_width()//2
        ph = parent.winfo_rooty() + parent.winfo_height()//2
        self.win.geometry(f"{w}x{h}+{pw - w//2}+{ph - h//2}")

    def _build(self):
        tk.Frame(self.win, bg=C['accent'], height=4).pack(fill="x")

        hdr = tk.Frame(self.win, bg=C['white'])
        hdr.pack(fill="x", padx=24, pady=(20, 0))
        tk.Label(hdr, text="Інструкція", font=("Segoe UI", 15, "bold"),
                 bg=C['white'], fg=C['text']).pack(side="left")
        tk.Label(hdr, text="CRM System v4.0",
                 font=("Segoe UI", 9), bg=C['white'], fg=C['muted']).pack(side="right", anchor="s")

        mk_sep(self.win).pack(fill="x", pady=(10, 0))

        main  = tk.Frame(self.win, bg=C['ibg'])
        main.pack(fill="both", expand=True)

        left = tk.Frame(main, bg=C['ibg'], width=220)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        mk_sep(main, orient='v').pack(side="left", fill="y")

        right = tk.Frame(main, bg=C['white'])
        right.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="РОЗДІЛИ", font=("Segoe UI", 8, "bold"),
                 bg=C['ibg'], fg=C['muted']).pack(pady=(16, 6), padx=16, anchor="w")

        self.title_lbl = tk.Label(right, text="", font=("Segoe UI", 12, "bold"),
                                   bg=C['white'], fg=C['text'], anchor="w")
        self.title_lbl.pack(pady=(20, 6), padx=24, anchor="w")
        mk_sep(right).pack(fill="x", padx=24)

        self.body_txt = tk.Text(right, font=("Segoe UI", 10), bg=C['white'], fg=C['text2'],
                                 relief="flat", bd=0, wrap="word", state="disabled",
                                 cursor="arrow", spacing1=4, spacing3=6,
                                 padx=4, pady=4)
        self.body_txt.pack(fill="both", expand=True, padx=24, pady=12)

        self.active_btn = None
        first = True
        for section, pairs in FAQ_SECTIONS:
            tk.Label(left, text=section, font=("Segoe UI", 8, "bold"),
                     bg=C['ibg'], fg=C['sidebar']).pack(anchor="w", padx=16, pady=(14, 4))
            for q, a in pairs:
                b = tk.Button(left, text=q, font=("Segoe UI", 9),
                              bg=C['ibg'], fg=C['text'], relief="flat", bd=0,
                              pady=6, padx=12, anchor="w", cursor="hand2",
                              wraplength=190, justify="left",
                              command=lambda qq=q, aa=a: self._show(qq, aa))
                b.pack(fill="x", padx=4)
                if first:
                    self._show(q, a)
                    self._highlight_btn(b)
                    first = False
                b.bind("<Enter>", lambda e, btn=b: btn.config(bg=C['border']) if btn != self.active_btn else None)
                b.bind("<Leave>", lambda e, btn=b: btn.config(bg=C['ibg']) if btn != self.active_btn else None)

    def _highlight_btn(self, btn):
        if self.active_btn:
            self.active_btn.config(bg=C['ibg'], fg=C['text'])
        self.active_btn = btn
        btn.config(bg=C['tree_sel'], fg=C['accent'])

    def _show(self, q, a):
        self.title_lbl.config(text=q)
        self.body_txt.config(state="normal")
        self.body_txt.delete("1.0", "end")
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
        self.tsearch    = tk.StringVar()
        self.dark_mode  = False
        self.current_page = None

        self._layout()
        self._sidebar()
        self._header()
        self.show("dashboard")
        self._tick()
        self.root.mainloop()

    def _layout(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.side = tk.Frame(self.root, bg=C['sidebar'], width=230)
        self.side.grid(row=0, column=0, sticky="ns")
        self.side.grid_propagate(False)
        self.body = tk.Frame(self.root, bg=C['bg'])
        self.body.grid(row=0, column=1, sticky="nsew")
        self.body.columnconfigure(0, weight=1)
        self.body.rowconfigure(1, weight=1)

    def _sidebar(self):
        # Logo
        logo_f = tk.Frame(self.side, bg=C['sidebar'])
        logo_f.pack(fill="x", pady=(24, 16))
        tk.Label(logo_f, text="CRM", font=("Segoe UI", 22, "bold"),
                 bg=C['sidebar'], fg=C['accent']).pack()
        tk.Label(logo_f, text="System", font=("Segoe UI", 8),
                 bg=C['sidebar'], fg=C['muted']).pack()

        tk.Frame(self.side, bg=C['side2'], height=1).pack(fill="x", padx=20, pady=(0, 4))

        # User info
        user_f = tk.Frame(self.side, bg=C['side2'])
        user_f.pack(fill="x", padx=10, pady=(0, 12))
        inner = tk.Frame(user_f, bg=C['side2'])
        inner.pack(fill="x", padx=10, pady=10)

        tk.Label(inner, text=current_user['username'],
                 font=("Segoe UI", 10, "bold"),
                 bg=C['side2'], fg='white').pack(anchor="w")
        role_color = "#FFD166" if current_user['role'] == 'admin' else C['muted']
        tk.Label(inner, text=current_user['role'].upper(),
                 font=("Segoe UI", 7, "bold"),
                 bg=C['side2'], fg=role_color).pack(anchor="w", pady=(2, 0))

        tk.Frame(self.side, bg=C['side2'], height=1).pack(fill="x", padx=20, pady=(0, 8))

        self.navbtns = {}
        pages = [
            ("dashboard", "Огляд"),
            ("workers",   "Працівники"),
            ("tasks",     "Завдання"),
            ("timer",     "Таймер"),
            ("logs",      "Журнал"),
            ("faq",       "Довідка"),
        ]
        if current_user['role'] == 'admin':
            pages.append(("admin", "Адмінка"))

        for key, lbl in pages:
            b = tk.Button(self.side, text=lbl,
                          font=("Segoe UI", 10),
                          bg=C['sidebar'], fg=C['muted'],
                          relief="flat", bd=0,
                          pady=11, padx=22, anchor="w",
                          cursor="hand2",
                          activebackground=C['side_btn'],
                          activeforeground="white",
                          command=lambda k=key: self.show(k))
            b.pack(fill="x")
            self.navbtns[key] = b
            b.bind("<Enter>", lambda e, btn=b: btn.config(bg=C['side_btn'], fg='white')
                   if self.current_page != btn else None)
            b.bind("<Leave>", lambda e, btn=b, k=key: btn.config(
                bg=C['side2'] if self.current_page == k else C['sidebar'],
                fg='white' if self.current_page == k else C['muted']))

        tk.Frame(self.side, bg=C['side2'], height=1).pack(fill="x", padx=20, pady=10)

        self.dark_btn = tk.Button(self.side, text="Темна тема",
                                   font=("Segoe UI", 9),
                                   bg=C['sidebar'], fg=C['muted'],
                                   relief="flat", bd=0,
                                   pady=9, padx=22, anchor="w",
                                   cursor="hand2",
                                   command=self.toggle_theme)
        self.dark_btn.pack(fill="x")

        tk.Button(self.side, text="Вийти з системи",
                  font=("Segoe UI", 9),
                  bg=C['sidebar'], fg=C['muted'],
                  relief="flat", bd=0,
                  pady=9, padx=22, anchor="w",
                  cursor="hand2",
                  command=self.logout).pack(fill="x", side="bottom", pady=(0, 14))

    def toggle_theme(self):
        global C
        self.dark_mode = not self.dark_mode
        C = THEMES['dark'] if self.dark_mode else THEMES['light']
        for w in self.root.winfo_children():
            w.destroy()
        self._layout()
        self._sidebar()
        self._header()
        self.show(self.current_page or "dashboard")

    def _header(self):
        hdr = tk.Frame(self.body, bg=C['white'],
                       highlightthickness=0)
        hdr.grid(row=0, column=0, sticky="ew")

        tk.Frame(hdr, bg=C['border'], height=1).pack(fill="x", side="bottom")

        inner = tk.Frame(hdr, bg=C['white'])
        inner.pack(fill="x", padx=28, pady=16)
        inner.columnconfigure(0, weight=1)

        self.htitle = tk.Label(inner, text="", font=("Segoe UI", 16, "bold"),
                               bg=C['white'], fg=C['text'])
        self.htitle.grid(row=0, column=0, sticky="w")

        self.hsub = tk.Label(inner, text="", font=("Segoe UI", 9),
                             bg=C['white'], fg=C['muted'])
        self.hsub.grid(row=1, column=0, sticky="w")

        # Clock in header
        self.clock_lbl = tk.Label(inner, text="", font=("Segoe UI", 9),
                                   bg=C['white'], fg=C['muted'])
        self.clock_lbl.grid(row=0, column=1, rowspan=2, sticky="e")
        self._update_clock()

        self.page = tk.Frame(self.body, bg=C['bg'])
        self.page.grid(row=1, column=0, sticky="nsew")
        self.page.columnconfigure(0, weight=1)
        self.page.rowconfigure(0, weight=1)

    def _update_clock(self):
        now = datetime.datetime.now().strftime("%d.%m.%Y  %H:%M:%S")
        if hasattr(self, 'clock_lbl'):
            try:
                self.clock_lbl.config(text=now)
            except tk.TclError:
                return
        self.root.after(1000, self._update_clock)

    def show(self, key):
        self.current_page = key
        for k, b in self.navbtns.items():
            b.config(bg=C['sidebar'], fg=C['muted'])
        if key in self.navbtns:
            self.navbtns[key].config(bg=C['side2'], fg="white")

        for w in self.page.winfo_children():
            w.destroy()

        info = {
            "dashboard": ("Огляд",       "Зведена аналітика системи"),
            "workers":   ("Працівники",  "Список та управління співробітниками"),
            "tasks":     ("Завдання",    "Дедлайни та пріоритети"),
            "timer":     ("Таймер",      "Облік робочого часу"),
            "logs":      ("Журнал",      "Повна історія дій"),
            "faq":       ("Довідка",     "Інструкція з використання"),
            "admin":     ("Адмінка",     "Управління системою"),
        }
        t, s = info.get(key, ("", ""))
        self.htitle.config(text=t)
        self.hsub.config(text=s)

        dispatch = {
            "dashboard": self.pg_dashboard,
            "workers":   self.pg_workers,
            "tasks":     self.pg_tasks,
            "timer":     self.pg_timer,
            "logs":      self.pg_logs,
            "faq":       self.pg_faq,
            "admin":     self.pg_admin,
        }
        dispatch[key]()

    def _pad(self):
        """Return the main padded content frame."""
        f = tk.Frame(self.page, bg=C['bg'])
        f.pack(fill="both", expand=True, padx=24, pady=(20, 24))
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)
        return f

    def _toolbar_frame(self, parent=None):
        p = parent or self.page
        bar = tk.Frame(p, bg=C['bg'])
        bar.pack(fill="x", pady=(0, 12))
        return bar

    # ── Dashboard ─────────────────────────────────────────────────────────────
    def pg_dashboard(self):
        canvas = tk.Canvas(self.page, bg=C['bg'], highlightthickness=0)
        scroll = ttk.Scrollbar(self.page, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        inner = tk.Frame(canvas, bg=C['bg'])
        cwin = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.columnconfigure(0, weight=1)

        def on_resize(e):
            canvas.itemconfig(cwin, width=e.width)
        canvas.bind("<Configure>", on_resize)

        def on_frame(e):
            canvas.config(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", on_frame)

        pad = tk.Frame(inner, bg=C['bg'])
        pad.pack(fill="both", expand=True, padx=24, pady=20)

        data = db_get_analytics()
        done_pct = int(data['tasks_done'] / data['tasks'] * 100) if data['tasks'] else 0

        # KPI cards row
        kpi = [
            ("Працівників",        str(data['workers']),       C['accent']),
            ("Всього завдань",      str(data['tasks']),         C['warn']),
            ("Виконано завдань",    f"{data['tasks_done']} ({done_pct}%)", C['success']),
            ("Активних завдань",    str(data['tasks_active']),  C['danger']),
            ("Користувачів",        str(data['users']),         C['info']),
            ("Дій за 24г",          str(data['recent_logs']),   C['muted']),
        ]
        kpi_row = tk.Frame(pad, bg=C['bg'])
        kpi_row.pack(fill="x", pady=(0, 20))
        for i, (lbl, val, color) in enumerate(kpi):
            card = tk.Frame(kpi_row, bg=C['card'],
                            highlightthickness=1, highlightbackground=C['border'])
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i==0 else 8, 0))
            kpi_row.columnconfigure(i, weight=1)
            tk.Frame(card, bg=color, height=3).pack(fill="x")
            inner2 = tk.Frame(card, bg=C['card'])
            inner2.pack(fill="x", padx=14, pady=10)
            tk.Label(inner2, text=val, font=("Segoe UI", 18, "bold"),
                     bg=C['card'], fg=C['text']).pack(anchor="w")
            tk.Label(inner2, text=lbl, font=("Segoe UI", 8),
                     bg=C['card'], fg=C['muted']).pack(anchor="w")

        # Second row: salary + tasks by priority + dept
        row2 = tk.Frame(pad, bg=C['bg'])
        row2.pack(fill="x", pady=(0, 20))
        row2.columnconfigure(0, weight=2)
        row2.columnconfigure(1, weight=3)

        # Salary card
        sal_card = tk.Frame(row2, bg=C['card'],
                            highlightthickness=1, highlightbackground=C['border'])
        sal_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        tk.Label(sal_card, text="Фінанси (зарплата)",
                 font=("Segoe UI", 10, "bold"), bg=C['card'], fg=C['text']).pack(
            padx=16, pady=(14, 4), anchor="w")
        mk_sep(sal_card).pack(fill="x", padx=16)
        sal_body = tk.Frame(sal_card, bg=C['card'])
        sal_body.pack(fill="x", padx=16, pady=10)
        for lbl, val in [
            ("Сер. зарплата", f"{data['avg_salary']:,.0f} грн"),
            ("Фонд ЗП",       f"{data['total_salary']:,.0f} грн"),
        ]:
            r = tk.Frame(sal_body, bg=C['card'])
            r.pack(fill="x", pady=4)
            tk.Label(r, text=lbl, font=("Segoe UI", 9),
                     bg=C['card'], fg=C['muted']).pack(side="left")
            tk.Label(r, text=val, font=("Segoe UI", 10, "bold"),
                     bg=C['card'], fg=C['success']).pack(side="right")

        # Tasks by priority
        pri_card = tk.Frame(row2, bg=C['card'],
                            highlightthickness=1, highlightbackground=C['border'])
        pri_card.grid(row=0, column=1, sticky="nsew")
        tk.Label(pri_card, text="Активні завдання за пріоритетом",
                 font=("Segoe UI", 10, "bold"), bg=C['card'], fg=C['text']).pack(
            padx=16, pady=(14, 4), anchor="w")
        mk_sep(pri_card).pack(fill="x", padx=16)
        pri_body = tk.Frame(pri_card, bg=C['card'])
        pri_body.pack(fill="x", padx=16, pady=10)
        colors = {'Критична': C['danger'], 'Висока': C['warn'],
                  'Середня': '#C08010', 'Низька': C['success']}
        total_pri = sum(data['by_priority'].values()) or 1
        for pri in PRIORITY_LEVELS:
            cnt = data['by_priority'].get(pri, 0)
            pct = int(cnt / total_pri * 100)
            r = tk.Frame(pri_body, bg=C['card'])
            r.pack(fill="x", pady=3)
            tk.Label(r, text=pri, font=("Segoe UI", 9),
                     bg=C['card'], fg=C['text'], width=10, anchor="w").pack(side="left")
            bar_bg = tk.Frame(r, bg=C['ibg'], height=8, width=200)
            bar_bg.pack(side="left", padx=(8, 8))
            bar_bg.pack_propagate(False)
            if pct > 0:
                tk.Frame(bar_bg, bg=colors.get(pri, C['accent']),
                         height=8, width=max(4, pct*2)).pack(side="left")
            tk.Label(r, text=f"{cnt}  ({pct}%)", font=("Segoe UI", 9),
                     bg=C['card'], fg=C['muted']).pack(side="left")

        # Top departments
        if data['by_dept']:
            dept_card = tk.Frame(pad, bg=C['card'],
                                 highlightthickness=1, highlightbackground=C['border'])
            dept_card.pack(fill="x")
            tk.Label(dept_card, text="Топ відділи за кількістю співробітників",
                     font=("Segoe UI", 10, "bold"), bg=C['card'], fg=C['text']).pack(
                padx=16, pady=(14, 4), anchor="w")
            mk_sep(dept_card).pack(fill="x", padx=16)
            dept_body = tk.Frame(dept_card, bg=C['card'])
            dept_body.pack(fill="x", padx=16, pady=10)
            max_cnt = max(r[1] for r in data['by_dept']) or 1
            for i, (dept, cnt) in enumerate(data['by_dept']):
                r = tk.Frame(dept_body, bg=C['card'])
                r.pack(fill="x", pady=3)
                tk.Label(r, text=dept or '(без відділу)', font=("Segoe UI", 9),
                         bg=C['card'], fg=C['text'], width=20, anchor="w").pack(side="left")
                bar_bg = tk.Frame(r, bg=C['ibg'], height=8, width=300)
                bar_bg.pack(side="left", padx=8)
                bar_bg.pack_propagate(False)
                pct_w = max(4, int(cnt / max_cnt * 300))
                colors_d = [C['accent'], C['info'], C['success'], C['warn'], C['danger']]
                tk.Frame(bar_bg, bg=colors_d[i % len(colors_d)],
                         height=8, width=pct_w).pack(side="left")
                tk.Label(r, text=str(cnt), font=("Segoe UI", 9, "bold"),
                         bg=C['card'], fg=C['text']).pack(side="left", padx=6)

    # ── Workers page ──────────────────────────────────────────────────────────
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
        dlg = Modal(self.root, title, width=500, height=620)

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

    # ── Tasks page ────────────────────────────────────────────────────────────
    def pg_tasks(self):
        bar   = tk.Frame(self.page, bg=C['bg'])
        bar.pack(fill="x", padx=20, pady=(16, 8))
        admin = current_user['role'] == 'admin'

        left_f = tk.Frame(bar, bg=C['bg'])
        left_f.pack(side="left")

        if admin:
            mk_btn(left_f, "Нове завдання", self.task_add).pack(side="left")
            mk_btn(left_f, "Редагувати", self.task_edit,
                   bg=C['warn']).pack(side="left", padx=(8, 0))
            mk_btn(left_f, "Видалити", self.task_del,
                   bg=C['danger']).pack(side="left", padx=(8, 0))

        mk_btn(left_f, "В роботу", lambda: self.task_set_status("В роботі"),
               bg=C['info'], fg=C['sidebar']).pack(side="left", padx=(8, 0))
        mk_btn(left_f, "Виконано", lambda: self.task_set_status("Виконано"),
               bg=C['success']).pack(side="left", padx=(8, 0))
        mk_btn(left_f, "Пауза", lambda: self.task_set_status("На паузі"),
               bg=C['ibg'], fg=C['text']).pack(side="left", padx=(8, 0))

        right_f = tk.Frame(bar, bg=C['bg'])
        right_f.pack(side="right")

        mk_label(right_f, "Пошук:", size=9).pack(side="left", padx=(0, 4))
        self.tsearch = tk.StringVar()
        self.tsearch.trace("w", lambda *a: self.task_reload())
        e = mk_entry(right_f, width=16)
        e.configure(textvariable=self.tsearch)
        e.pack(side="left", ipady=6)

        mk_label(right_f, "Фільтр:", size=9).pack(side="left", padx=(12, 4))
        self.tfilter = tk.StringVar(value="Всі")
        cb = ttk.Combobox(right_f, textvariable=self.tfilter,
                          values=["Всі"] + PRIORITY_LEVELS + TASK_STATUSES,
                          state="readonly", width=14, font=("Segoe UI", 9))
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self.task_reload())

        pad = tk.Frame(self.page, bg=C['bg'])
        pad.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        pad.columnconfigure(0, weight=1)
        pad.rowconfigure(0, weight=1)

        self.ttree = make_tree(pad,
                               ["#", "Назва", "Відповідальний", "Категорія", "Пріоритет", "Дедлайн", "Статус", "Автор"],
                               [40, 230, 150, 120, 100, 120, 100, 120])
        self.ttree.bind("<Double-1>", lambda e: self.task_edit())
        self.task_reload()

    def task_reload(self):
        if not self.ttree:
            return
        filt   = self.tfilter.get() if self.tfilter else "Всі"
        search = self.tsearch.get() if hasattr(self, 'tsearch') and self.tsearch else ''
        for r in self.ttree.get_children():
            self.ttree.delete(r)
        for i, row in enumerate(db_get_tasks(filt, search)):
            done = row[5] == "Виконано"
            tag  = "done" if done else row[3]
            self.ttree.insert("", "end", iid=str(row[0]),
                              values=(row[0], row[1], row[2], row[8], row[3], row[4], row[5], row[6]),
                              tags=(tag,))

    def task_del(self):
        sel = self.ttree.selection()
        if not sel:
            messagebox.showwarning("Увага", "Виберіть завдання.")
            return
        if not messagebox.askyesno("Підтвердження", f"Видалити {len(sel)} завдання(нь)?"):
            return
        ids = [int(s) for s in sel]
        db_delete_tasks(ids)
        log_action(f"видалив завдання id={ids}")
        self.task_reload()

    def task_set_status(self, status):
        sel = self.ttree.selection()
        if not sel:
            messagebox.showwarning("Увага", "Виберіть завдання.")
            return
        ids = [int(s) for s in sel]
        db_task_status(ids, status)
        log_action(f"змінив статус завдань id={ids} -> {status}")
        self.task_reload()

    def task_add(self):
        self._task_form(None)

    def task_edit(self):
        sel = self.ttree.selection()
        if not sel:
            messagebox.showwarning("Увага", "Виберіть завдання.")
            return
        tid = int(sel[0])
        conn = db()
        row = conn.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
        conn.close()
        if row:
            data = {
                'id': row[0], 'title': row[1], 'assignee': row[2],
                'priority': row[3], 'deadline': row[4], 'status': row[5],
                'author': row[6], 'note': row[8] if len(row) > 8 else '',
                'category': row[9] if len(row) > 9 else ''
            }
            self._task_form(data)

    def _task_form(self, existing):
        title = "Редагувати завдання" if existing else "Нове завдання"
        dlg = Modal(self.root, title, width=500, height=540)

        title_e = dlg.field("Назва завдання *",
                             default=existing.get('title', '') if existing else '')
        assignee_e = dlg.field("Відповідальний",
                                default=existing.get('assignee', '') if existing else '')
        deadline_e = dlg.field("Дедлайн (РРРР-ММ-ДД)",
                                default=existing.get('deadline', '') if existing else '')
        category_e = dlg.field("Категорія",
                                default=existing.get('category', '') if existing else '')

        pv = dlg.combobox("Пріоритет", PRIORITY_LEVELS,
                          default=existing.get('priority', 'Середня') if existing else 'Середня')

        if existing:
            sv = dlg.combobox("Статус", TASK_STATUSES,
                              default=existing.get('status', 'Активне'))

        note_t = dlg.textarea("Нотатки", default=existing.get('note', '') if existing else '')

        def submit():
            t = title_e.get().strip()
            if not t:
                dlg.error("Назва обов'язкова.")
                return
            data = {
                'title':    t,
                'assignee': assignee_e.get().strip(),
                'priority': pv.get(),
                'deadline': deadline_e.get().strip(),
                'status':   sv.get() if existing else 'Активне',
                'author':   current_user['username'],
                'note':     note_t.get("1.0", "end-1c").strip(),
                'category': category_e.get().strip(),
            }
            if existing:
                db_update_task(existing['id'], data)
                log_action(f"редагував завдання: {t}")
            else:
                db_add_task(data)
                log_action(f"додав завдання: {t}")
            self.task_reload()
            dlg.win.destroy()

        dlg.add_ok("Зберегти", submit)

    # ── Timer page ────────────────────────────────────────────────────────────
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

        # Card
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

    # ── Logs page ─────────────────────────────────────────────────────────────
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

    # ── FAQ page ──────────────────────────────────────────────────────────────
    def pg_faq(self):
        outer = tk.Frame(self.page, bg=C['bg'])
        outer.pack(fill="both", expand=True, padx=24, pady=20)

        left = tk.Frame(outer, bg=C['card'],
                        highlightthickness=1, highlightbackground=C['border'],
                        width=250)
        left.pack(side="left", fill="y", padx=(0, 16))
        left.pack_propagate(False)

        right = tk.Frame(outer, bg=C['card'],
                         highlightthickness=1, highlightbackground=C['border'])
        right.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="РОЗДІЛИ", font=("Segoe UI", 8, "bold"),
                 bg=C['card'], fg=C['muted']).pack(pady=(16, 6), padx=16, anchor="w")

        title_lbl = tk.Label(right, text="", font=("Segoe UI", 13, "bold"),
                             bg=C['card'], fg=C['text'], anchor="w")
        title_lbl.pack(pady=(20, 6), padx=24, anchor="w")
        mk_sep(right).pack(fill="x", padx=24)

        body_txt = tk.Text(right, font=("Segoe UI", 10), bg=C['card'], fg=C['text2'],
                           relief="flat", bd=0, wrap="word", state="disabled",
                           cursor="arrow", spacing1=4, spacing3=6, padx=4, pady=4)
        body_txt.pack(fill="both", expand=True, padx=24, pady=12)

        active_btn_ref = [None]

        def show(q, a, btn=None):
            title_lbl.config(text=q)
            body_txt.config(state="normal")
            body_txt.delete("1.0", "end")
            body_txt.insert("1.0", a)
            body_txt.config(state="disabled")
            if btn:
                if active_btn_ref[0]:
                    active_btn_ref[0].config(bg=C['card'], fg=C['text'])
                active_btn_ref[0] = btn
                btn.config(bg=C['tree_sel'], fg=C['accent'])

        first = True
        for section, pairs in FAQ_SECTIONS:
            tk.Label(left, text=section, font=("Segoe UI", 8, "bold"),
                     bg=C['card'], fg=C['sidebar']).pack(anchor="w", padx=16, pady=(14, 4))
            mk_sep(left).pack(fill="x", padx=16, pady=(0, 4))
            for q, a in pairs:
                b = tk.Button(left, text=q, font=("Segoe UI", 9),
                              bg=C['card'], fg=C['text'], relief="flat", bd=0,
                              pady=6, padx=12, anchor="w", cursor="hand2",
                              wraplength=220, justify="left")
                b.config(command=lambda qq=q, aa=a, btn=b: show(qq, aa, btn))
                b.pack(fill="x", padx=6)
                if first:
                    show(q, a, b)
                    first = False

    # ── Admin page ────────────────────────────────────────────────────────────
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


# ── Entry point ───────────────────────────────────────────────────────────────
db_init()
LoginWindow()