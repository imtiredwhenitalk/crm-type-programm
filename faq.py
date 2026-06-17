import tkinter as tk
from uihelper import mk_sep
from theme import C

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
