import tkinter as tk
from tkinter import messagebox
import logging
import datetime
import os
import sqlite3
import json

start_working = False
work_start_time = None

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR    = os.path.join(BASE_DIR, 'logs')
DATA_DIR    = os.path.join(BASE_DIR, 'data')
LOG_FILE    = os.path.join(LOGS_DIR, 'crm_log.txt')
WORKER_FILE = os.path.join(DATA_DIR, 'worker.json')

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

conn = sqlite3.connect(os.path.join(BASE_DIR, 'crm.db'))
conn.execute('CREATE TABLE IF NOT EXISTS logs (timestamp TEXT, user TEXT, action TEXT)')
conn.commit()
conn.close()


def load_workers():
    if not os.path.exists(WORKER_FILE):
        return []
    with open(WORKER_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_workers(workers):
    with open(WORKER_FILE, 'w', encoding='utf-8') as f:
        json.dump(workers, f, ensure_ascii=False, indent=2)


def add_worker_to_json(data):
    workers = load_workers()
    data['id'] = len(workers) + 1
    workers.append(data)
    save_workers(workers)


def save_worker_to_db(data):
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'crm.db'))
    conn.execute(
        'INSERT INTO logs (timestamp, user, action) VALUES (?, ?, ?)',
        (datetime.datetime.now().isoformat(), user(), f"Added worker: {data}")
    )
    conn.commit()
    conn.close()


def user():
    return os.getenv('USERNAME') or os.getenv('USER') or 'Unknown User'


def log_save(action):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.datetime.now()} - {user()} - {action}\n")


def log(action):
    logging.info(f"{user()} - {action}")


def whoami():
    log_save("запустив програму")
    return user()


def whoadd():
    log_save("відкрив форму додавання робітника")
    return user()


def show_error():
    messagebox.showerror("Error", "An error occurred while adding the worker.")


def show_message():
    messagebox.showinfo("Info", "Worker added successfully!")


def worker_not_added():
    return False


def submit_worker(entries, worker_adder):
    data = {field: entry.get() for field, entry in entries.items()}
    if not data.get("Name", "").strip():
        messagebox.showwarning("Увага", "Поле 'Name' не може бути порожнім.")
        return
    add_worker_to_json(data)
    save_worker_to_db(data)
    log_save(f"додав робітника: {data}")
    show_message()
    for entry in entries.values():
        entry.delete(0, tk.END)


def add_worker():
    add = tk.Toplevel(root)
    add.title("Add Worker")
    add.geometry("800x600")
    add.configure(bg="#ffffff")
    add.resizable(False, False)

    fields = ["Name", "Department", "Salary", "Hire Date"]
    entries = {}
    worker_adder = whoadd()

    tk.Label(add, text="Додати робітника", font=("Arial", 13, "bold"),
             bg="#ffffff", fg="#1a1a1a").grid(row=0, column=0, columnspan=2, pady=(14, 10), padx=16)

    for i, field in enumerate(fields):
        tk.Label(add, text=field, font=("Arial", 9),
                 bg="#ffffff", fg="#888888").grid(row=i*2+1, column=0, columnspan=2, padx=16, pady=(6, 0), sticky="w")
        entry = tk.Entry(add, font=("Arial", 11), relief="flat", bd=0,
                         bg="#f5f5f5", fg="#1a1a1a", insertbackground="#1a1a1a")
        entry.grid(row=i*2+2, column=0, columnspan=2, padx=16, pady=(2, 0), ipady=5, sticky="ew")
        entries[field] = entry

    add.columnconfigure(0, weight=1)
    add.columnconfigure(1, weight=1)

    if worker_not_added():
        show_error()
    else:
        tk.Button(
            add, text="Зберегти",
            command=lambda: submit_worker(entries, worker_adder),
            font=("Arial", 10, "bold"), bg="#1a1a2e", fg="white",
            relief="flat", bd=0, pady=8, cursor="hand2"
        ).grid(row=9, column=0, columnspan=2, padx=16, pady=16, sticky="ew")


def show_workers():
    workers = load_workers()
    if not workers:
        messagebox.showinfo("Workers", "Немає збережених робітників.")
        return
    lines = [f"#{w.get('id','')}  {w.get('Name','')}  |  {w.get('Department','')}  |  {w.get('Salary','')}  |  {w.get('Hire Date','')}" for w in workers]
    messagebox.showinfo("Workers", "\n".join(lines))


def show_departments():
    workers = load_workers()
    if not workers:
        messagebox.showinfo("Departments", "Немає даних.")
        return
    depts = sorted({w.get('Department', '') for w in workers if w.get('Department')})
    messagebox.showinfo("Departments", "\n".join(depts) or "Немає відділів.")


def show_salaries():
    workers = load_workers()
    if not workers:
        messagebox.showinfo("Salaries", "Немає даних.")
        return
    lines = [f"{w.get('Name','?')}  —  {w.get('Salary','?')}" for w in workers]
    messagebox.showinfo("Salaries", "\n".join(lines))


def show_hire_dates():
    workers = load_workers()
    if not workers:
        messagebox.showinfo("Hire Dates", "Немає даних.")
        return
    lines = [f"{w.get('Name','?')}  —  {w.get('Hire Date','?')}" for w in workers]
    messagebox.showinfo("Hire Dates", "\n".join(lines))


def stop_work():
    global start_working, work_start_time
    worked_time = datetime.datetime.now() - work_start_time
    hours, remainder = divmod(int(worked_time.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    messagebox.showinfo("Stop Work", f"Час роботи:\n{hours} год {minutes} хв {seconds} сек")
    log("завершив роботу")
    log_save("завершив роботу")
    timer_label.config(text="00:00:00")
    button_start_work.config(text="Почати роботу", bg="#eafaf1", fg="#1a5c35")
    start_working = False
    work_start_time = None


def start_work():
    global start_working, work_start_time
    if not start_working:
        work_start_time = datetime.datetime.now()
        messagebox.showinfo("Start Work", f"Привіт, {user()}!\nГарної роботи!")
        log("почав роботу")
        log_save("почав роботу")
        button_start_work.config(text="Завершити роботу", bg="#fdecea", fg="#9b2a2a")
        start_working = True
    else:
        stop_work()


def update_timer():
    if start_working and work_start_time:
        worked_time = datetime.datetime.now() - work_start_time
        hours, remainder = divmod(int(worked_time.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        timer_label.config(text=f"{hours:02}:{minutes:02}:{seconds:02}")
    root.after(1000, update_timer)


def show_info():
    messagebox.showinfo("Info", "CRM System\nVersion 1.0\nDeveloped by imtiredwhenitalk")


root = tk.Tk()
root.title("CRM System")
root.geometry("1920x1080")
root.configure(bg="#ffffff")
root.resizable(False, False)

root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)

header = tk.Frame(root, bg="#1a1a2e", pady=12)
header.grid(row=0, column=0, columnspan=2, sticky="ew")
header.columnconfigure(0, weight=1)
tk.Label(header, text="CRM System", font=("Arial", 16, "bold"), bg="#1a1a2e", fg="white").grid(row=0, column=0)
tk.Label(header, text=f"{user()}", font=("Arial", 9), bg="#1a1a2e", fg="#8888aa").grid(row=1, column=0)

def sep(row):
    tk.Frame(root, bg="#eeeeee", height=1).grid(row=row, column=0, columnspan=2, sticky="ew")

def row_btn(row, col, text, cmd, span=1, padl=0, padr=0):
    tk.Button(
        root, text=text, command=cmd,
        font=("Arial", 10), bg="#ffffff", fg="#1a1a1a",
        relief="flat", bd=0, pady=10, padx=14,
        anchor="w", cursor="hand2",
        activebackground="#f5f5f5", activeforeground="#1a1a1a"
    ).grid(row=row, column=col, columnspan=span, padx=(padl, padr), sticky="ew")

sep(1)
row_btn(2, 0, "Додати робітника",    add_worker,       span=1, padl=0, padr=0)
sep(3)
row_btn(4, 0, "Показати робітників", show_workers,     span=1)
sep(5)
row_btn(6, 0, "Відділи",             show_departments, span=1)
sep(7)
row_btn(8, 0, "Зарплати",            show_salaries,    span=1)
sep(9)
row_btn(10, 0, "Дати найму",         show_hire_dates,  span=1)
sep(11)
row_btn(12, 0, "Інформація",         show_info,        span=1)
sep(13)

tk.Label(root, text="час роботи", font=("Arial", 8), bg="#ffffff", fg="#bbbbbb").grid(
    row=14, column=0, columnspan=2, pady=(16, 2))

timer_label = tk.Label(root, text="00:00:00", font=("Courier", 28, "bold"), bg="#ffffff", fg="#1a1a2e")
timer_label.grid(row=15, column=0, columnspan=2, pady=(0, 12))

button_start_work = tk.Button(
    root, text="Почати роботу", command=start_work,
    font=("Arial", 11, "bold"), bg="#eafaf1", fg="#1a5c35",
    relief="flat", bd=0, pady=10, cursor="hand2"
)
button_start_work.grid(row=16, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="ew")

update_timer()
whoami()
root.mainloop()