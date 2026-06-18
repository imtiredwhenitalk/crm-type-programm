import os
import sqlite3
import logging
import datetime

from db.current_user import current_user, _state
from db.db import db, hash_pw

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'crm_log.txt')
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

_USER_COLS = 'id,username,role,phone,email,org,department'

def _user_dict(row):
    return {
        'id': row[0], 'username': row[1], 'role': row[2],
        'phone': row[3] or '', 'email': row[4] or '', 'org': row[5] or '',
        'department': row[6] or '' if len(row) > 6 else '',
    }

def db_login(username, password):
    conn = db()
    row = conn.execute(
        f'SELECT {_USER_COLS} FROM users WHERE username=? AND password=?',
        (username, hash_pw(password))
    ).fetchone()
    if row:
        conn.execute('UPDATE users SET last_login=? WHERE id=?',
                     (datetime.datetime.now().isoformat(), row[0]))
        conn.commit()
    conn.close()
    if not row:
        return None
    return _user_dict(row)

def db_login_by_username(username):
    conn = db()
    row = conn.execute(
        f'SELECT {_USER_COLS} FROM users WHERE username=?', (username,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return _user_dict(row)

def db_create_user(username, password, role, department=''):
    try:
        conn = db()
        conn.execute(
            'INSERT INTO users (username,password,role,department,created) VALUES (?,?,?,?,?)',
            (username, hash_pw(password), role, department,
             datetime.datetime.now().isoformat())
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
        'SELECT id,username,role,phone,email,org,department,created,last_login FROM users ORDER BY id'
    ).fetchall()
    conn.close()
    return rows

def db_set_role(uid, role):
    conn = db()
    conn.execute('UPDATE users SET role=? WHERE id=?', (role,uid))
    conn.commit(); conn.close()

def db_set_department(uid, department):
    conn = db()
    conn.execute('UPDATE users SET department=? WHERE id=?', (department, uid))
    conn.commit(); conn.close()

def db_delete_user(uid):
    conn = db()
    conn.execute('DELETE FROM users WHERE id=?', (uid,))
    conn.commit(); conn.close()

def db_get_logs(search='', limit=500, username=None):
    conn = db()
    conditions = []
    params = []
    if username:
        conditions.append('username=?')
        params.append(username)
    if search:
        q = f"%{search.lower()}%"
        conditions.append('(lower(username) LIKE ? OR lower(action) LIKE ?)')
        params.extend([q, q])
    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
    params.append(limit)
    rows = conn.execute(
        f'SELECT timestamp,username,action FROM logs {where} ORDER BY timestamp DESC LIMIT ?',
        params
    ).fetchall()
    conn.close()
    return rows

def log_action(action):
    u = _state['user']
    uname = u['username'] if u else 'system'
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
