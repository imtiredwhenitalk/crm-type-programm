import db
import datetime

TASK_STATUSES   = ['Активне', 'В роботі', 'На паузі', 'Виконано']
PRIORITY_LEVELS = ['Критична', 'Висока', 'Середня', 'Низька']

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