from db import db

DEPARTMENTS = ['IT', 'HR', 'Фінанси', 'Маркетинг', 'Продажі', 'Виробництво', 'Логістика', 'Адміністрація']

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