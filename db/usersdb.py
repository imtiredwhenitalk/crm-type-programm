from db.current_user import current_user
from db import db, hash_pw , sqlite3
from log.logs import LOG_FILE

import logging
import datetime

logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

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