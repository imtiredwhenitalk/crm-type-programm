from db import db
import datetime

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