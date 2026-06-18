from db.db import db
import datetime

TASK_STATUSES   = ['Активне', 'В роботі', 'На паузі', 'Виконано']
PRIORITY_LEVELS = ['Критична', 'Висока', 'Середня', 'Низька']

def db_get_tasks(filt='Всі', search='', department=None):
    conn = db()
    conditions = []
    params = []
    if department is not None:
        conditions.append('department=?')
        params.append(department)
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
        f'''SELECT id,title,assignee,priority,deadline,status,author,note,category,department
            FROM tasks {where}
            ORDER BY CASE priority WHEN "Критична" THEN 1 WHEN "Висока" THEN 2
                                   WHEN "Середня" THEN 3 ELSE 4 END, id''',
        params
    ).fetchall()
    conn.close()
    return rows

def db_add_task(data):
    conn = db()
    conn.execute(
        '''INSERT INTO tasks (title,assignee,priority,deadline,status,author,created,note,category,department)
           VALUES (?,?,?,?,?,?,?,?,?,?)''',
        (data['title'], data['assignee'], data['priority'],
         data['deadline'], data.get('status','Активне'), data['author'],
         datetime.datetime.now().isoformat(), data.get('note',''),
         data.get('category',''), data.get('department',''))
    )
    conn.commit(); conn.close()

def db_update_task(tid, data):
    conn = db()
    conn.execute(
        '''UPDATE tasks SET title=?,assignee=?,priority=?,deadline=?,status=?,
           note=?,category=?,department=? WHERE id=?''',
        (data['title'], data['assignee'], data['priority'],
         data['deadline'], data['status'], data.get('note',''),
         data.get('category',''), data.get('department',''), tid)
    )
    conn.commit(); conn.close()

def db_delete_tasks(ids):
    conn = db()
    conn.executemany('DELETE FROM tasks WHERE id=?', [(i,) for i in ids])
    conn.commit(); conn.close()

def db_task_status(ids, status):
    conn = db()
    conn.executemany('UPDATE tasks SET status=? WHERE id=?', [(status, i) for i in ids])
    conn.commit(); conn.close()

def _dept_clause(department):
    if department is None:
        return '', []
    return ' AND department=?', [department]

def db_get_analytics(department=None):
    conn = db()
    dc, dp = _dept_clause(department)
    w_dc = ' AND department=?' if department else ''
    w_params = [department] if department else []

    workers_total  = conn.execute(
        f'SELECT COUNT(*) FROM workers WHERE 1=1{w_dc}', w_params
    ).fetchone()[0]
    tasks_total    = conn.execute(
        f'SELECT COUNT(*) FROM tasks WHERE 1=1{dc}', dp
    ).fetchone()[0]
    tasks_done     = conn.execute(
        f"SELECT COUNT(*) FROM tasks WHERE status='Виконано'{dc}", dp
    ).fetchone()[0]
    tasks_active   = conn.execute(
        f"SELECT COUNT(*) FROM tasks WHERE status!='Виконано'{dc}", dp
    ).fetchone()[0]
    users_total    = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    avg_salary     = conn.execute(
        f'SELECT AVG(salary) FROM workers WHERE 1=1{w_dc}', w_params
    ).fetchone()[0] or 0
    total_salary   = conn.execute(
        f'SELECT SUM(salary) FROM workers WHERE 1=1{w_dc}', w_params
    ).fetchone()[0] or 0
    by_priority    = conn.execute(
        f"SELECT priority, COUNT(*) FROM tasks WHERE status!='Виконано'{dc} GROUP BY priority", dp
    ).fetchall()
    by_status      = conn.execute(
        f'SELECT status, COUNT(*) FROM tasks WHERE 1=1{dc} GROUP BY status', dp
    ).fetchall()
    by_task_dept   = conn.execute(
        f'''SELECT department, COUNT(*) FROM tasks
            WHERE department!="" AND status!='Виконано'{dc}
            GROUP BY department ORDER BY COUNT(*) DESC LIMIT 8''', dp
    ).fetchall()
    by_dept        = conn.execute(
        f'''SELECT department, COUNT(*) FROM workers
            WHERE department!=""{w_dc.replace("department", "department") if w_dc else ""}
            GROUP BY department ORDER BY COUNT(*) DESC LIMIT 8''',
        w_params if department else []
    ).fetchall()
    if not department:
        by_dept = conn.execute(
            'SELECT department, COUNT(*) FROM workers WHERE department!="" '
            'GROUP BY department ORDER BY COUNT(*) DESC LIMIT 8'
        ).fetchall()
    overdue        = conn.execute(
        f'''SELECT COUNT(*) FROM tasks
            WHERE status!='Виконано' AND deadline!='' AND deadline < ?{dc}''',
        [datetime.date.today().isoformat()] + dp
    ).fetchone()[0]
    by_worker_status = conn.execute(
        f'SELECT status, COUNT(*) FROM workers WHERE 1=1{w_dc} GROUP BY status', w_params
    ).fetchall()
    recent_logs    = conn.execute(
        'SELECT COUNT(*) FROM logs WHERE timestamp > ?',
        ((datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),)
    ).fetchone()[0]
    completion_by_dept = conn.execute(
        '''SELECT department,
                  SUM(CASE WHEN status='Виконано' THEN 1 ELSE 0 END),
                  COUNT(*)
           FROM tasks WHERE department!=""
           GROUP BY department ORDER BY COUNT(*) DESC LIMIT 8'''
    ).fetchall() if not department else []
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
        'by_status': dict(by_status),
        'by_task_dept': by_task_dept,
        'by_dept': by_dept,
        'by_worker_status': dict(by_worker_status),
        'overdue': overdue,
        'recent_logs': recent_logs,
        'completion_by_dept': completion_by_dept,
        'department': department or '',
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

def db_get_task_stats_by_dept():
    conn = db()
    rows = conn.execute(
        '''SELECT department,
                  SUM(CASE WHEN status='Виконано' THEN 1 ELSE 0 END) as done,
                  SUM(CASE WHEN status!='Виконано' THEN 1 ELSE 0 END) as active,
                  COUNT(*) as total
           FROM tasks WHERE department!=""
           GROUP BY department ORDER BY total DESC'''
    ).fetchall()
    conn.close()
    return rows
