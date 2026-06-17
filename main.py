import tkinter as tk
import datetime

from login import current_user
from theme import C , THEMES

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
