import sqlite3
import hashlib
import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'crm.db')

PRIORITY_LEVELS = ['Критична', 'Висока', 'Середня', 'Низька']

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row  
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

    admin = conn.execute('SELECT id FROM users WHERE username="admin"').fetchone()
    if not admin:
        conn.execute(
            'INSERT INTO users (username,password,role,created) VALUES (?,?,?,?)',
            ('admin', hash_pw('admin'), 'admin', datetime.datetime.now().isoformat())
        )

    conn.commit()
    conn.close()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_db_connection():
    """Возвращает соединение с БД"""
    return db()

def db_login_by_username(username):
    """Получает пользователя по имени"""
    conn = db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None