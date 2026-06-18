import tkinter as tk
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main.uihelper import mk_sep
from main.theme import C

FAQ_SECTIONS = [
    ("Вхід у систему", [
        ("Як увійти?",
         "Введіть логін та пароль на головному екрані.\n"
         "Логін адміна за замовчуванням: admin / admin.\n"
         "Після першого входу система запропонує заповнити профіль.\n\n"
         "Порада: Увімкніть «Запам'ятати пристрій» — тоді наступного разу\n"
         "входити знову не потрібно (сесія зберігається 30 днів).\n\n"
         "Після автоматичного входу ви одразу потрапляєте в головне вікно,\n"
         "без повторного заповнення профілю."),
        ("Забув пароль?",
         "Зверніться до адміністратора — він може:\n"
         "  • Видалити старий акаунт і створити новий (Адмінка > Користувачі)\n"
         "  • Або попросити вас змінити пароль у розділі «Профіль»\n\n"
         "Якщо ви пам'ятаєте пароль — перейдіть у «Профіль» > «Зміна пароля»\n"
         "та введіть новий пароль (мінімум 4 символи)."),
        ("Блокування після 3 спроб?",
         "Якщо ввести неправильний пароль 3 рази поспіль —\n"
         "вхід буде заблоковано на 5 хвилин.\n"
         "Зачекайте або зверніться до адміна.\n\n"
         "Адмін може скинути блокування:\n"
         "  Адмінка > Користувачі > вибрати користувача > «Скинути блокування»"),
        ("Що таке «Запам'ятати пристрій»?",
         "Ця опція зберігає ваш логін у локальному файлі сесії.\n"
         "При наступному запуску програми вхід відбудеться автоматично.\n"
         "Сесія діє 30 днів, після чого потрібно увійти знову.\n\n"
         "Щоб вийти з збереженої сесії — натисніть «Вийти з системи»\n"
         "у боковому меню. Це очистить збережені дані."),
    ]),
    ("Профіль", [
        ("Навіщо потрібен профіль?",
         "Профіль містить ваші контактні дані: телефон, email та організацію.\n"
         "Ці дані допомагають колегам та адміністратору зв'язатися з вами.\n\n"
         "При першому вході з'являється вікно заповнення профілю.\n"
         "Можна пропустити і заповнити пізніше в розділі «Профіль»."),
        ("Як редагувати профіль?",
         "Перейдіть у боковому меню на «Профіль».\n"
         "Змініть потрібні поля та натисніть «Зберегти профіль».\n\n"
         "У цьому ж розділі відображається статистика вашого робочого часу\n"
         "та загальна інформація про акаунт."),
        ("Як змінити пароль?",
         "Профіль > блок «Зміна пароля».\n"
         "Введіть новий пароль двічі (мінімум 4 символи) та натисніть\n"
         "«Змінити пароль». Зміна застосовується негайно."),
    ]),
    ("Огляд (Dashboard)", [
        ("Що показує головна сторінка?",
         "Розділ «Огляд» — це зведена панель аналітики:\n\n"
         "  • Кількість працівників, завдань, користувачів\n"
         "  • Відсоток виконаних завдань\n"
         "  • Кількість активних завдань\n"
         "  • Дії в системі за останні 24 години\n\n"
         "Нижче — фінансові показники (середня зарплата, фонд ЗП),\n"
         "діаграма пріоритетів завдань та топ-5 відділів."),
        ("Хто бачить аналітику?",
         "Всі авторизовані користувачі бачать загальну статистику.\n"
         "Детальна аналітика робочого часу всіх користувачів\n"
         "доступна лише адміністратору в розділі «Адмінка» > «Аналітика»."),
    ]),
    ("Працівники", [
        ("Як додати працівника?",
         "Адмін: Працівники > Додати працівника > заповнити форму > Зберегти.\n"
         "Обов'язкове поле — лише ім'я. Решта — за бажанням.\n\n"
         "Звичайний користувач може лише переглядати список та експортувати CSV."),
        ("Як редагувати працівника?",
         "Виберіть рядок у таблиці (подвійний клік або кнопка «Редагувати»).\n"
         "Доступно лише адміну.\n\n"
         "У формі можна змінити: ім'я, посаду, відділ, зарплату,\n"
         "дату найму, контакти, статус та нотатки."),
        ("Як шукати та фільтрувати?",
         "Поле «Пошук» — шукає за ім'ям, посадою або відділом в реальному часі.\n"
         "Фільтр «Статус» — показує лише Активних, Звільнених або у Відпустці."),
        ("Як експортувати в CSV?",
         "Кнопка «Експорт CSV» → оберіть місце збереження файлу.\n"
         "Файл містить усі поля працівників і відкривається в Excel."),
        ("Статистика за відділами?",
         "Вкладка «Статистика» показує кількість по відділах,\n"
         "середню зарплату, фонд оплати праці та відсоток від загального.\n\n"
         "Подвійний клік на рядку — покаже список працівників цього відділу."),
    ]),
    ("Завдання", [
        ("Як створити завдання?",
         "Адмін: Завдання > Нове завдання > заповнити назву,\n"
         "відповідального, дедлайн, пріоритет та категорію > Зберегти.\n\n"
         "Автор завдання автоматично записується як поточний користувач."),
        ("Рівні пріоритету",
         "Критична — негайно, червоний колір\n"
         "Висока   — найближчим часом, помаранчевий\n"
         "Середня  — планово, жовтий\n"
         "Низька   — при нагоді, зелений\n\n"
         "Колір рядка в таблиці відповідає пріоритету.\n"
         "Виконані завдання відображаються сірим кольором."),
        ("Як змінити статус?",
         "Виберіть завдання і натисніть «В роботу», «Пауза» або «Виконано».\n"
         "Також можна редагувати подвійним кліком (адмін).\n\n"
         "Статуси: Активне → В роботі → На паузі → Виконано\n\n"
         "Фільтр «Виконані» показує лише завершені завдання.\n"
         "Пошук працює за назвою та відповідальним."),
        ("Хто може керувати завданнями?",
         "Адмін: створення, редагування, видалення, зміна будь-яких полів.\n"
         "Користувач: перегляд, зміна статусу обраних завдань."),
    ]),
    ("Таймер", [
        ("Як використовувати таймер?",
         "Перейдіть на сторінку «Таймер» > натисніть «Почати роботу».\n"
         "Таймер відображає поточний час сесії у форматі ГГ:ХХ:СС.\n"
         "Натисніть «Завершити роботу» — система покаже тривалість\n"
         "та збереже запис у базу даних.\n\n"
         "Історія сесій доступна на вкладці «Історія сесій»."),
        ("Чи працює таймер у фоні?",
         "Таймер працює поки програма відкрита.\n"
         "Якщо закрити програму під час активної сесії —\n"
         "незавершена сесія не збережеться.\n\n"
         "Завжди натискайте «Завершити роботу» перед виходом."),
        ("Аналітика робочого часу",
         "Користувач бачить свої сесії у вкладці «Історія сесій».\n"
         "У «Профіль» відображається загальний час та кількість сесій.\n\n"
         "Адмін бачить час усіх користувачів у «Адмінка» > «Аналітика»."),
    ]),
    ("Журнал дій", [
        ("Що записується в журнал?",
         "Система автоматично фіксує всі важливі дії:\n"
         "  • Вхід та вихід з системи\n"
         "  • Додавання, редагування, видалення записів\n"
         "  • Зміна статусів завдань\n"
         "  • Початок та завершення робочих сесій\n"
         "  • Експорт даних\n\n"
         "Кожен запис містить час, ім'я користувача та опис дії."),
        ("Хто бачить журнал?",
         "Адміністратор бачить усі дії всіх користувачів.\n"
         "Звичайний користувач бачить лише свої власні дії.\n\n"
         "Адмін може експортувати повний журнал у CSV."),
        ("Як шукати в журналі?",
         "Введіть текст у поле «Пошук» — фільтрація відбувається\n"
         "за іменем користувача або текстом дії в реальному часі."),
    ]),
    ("Інтерфейс", [
        ("Темна тема",
         "Натисніть «Темна тема» внизу бокового меню.\n"
         "Повторне натискання поверне світлу тему.\n"
         "Налаштування теми зберігається під час сесії."),
        ("Навігація",
         "Бокове меню зліва містить усі розділи системи.\n"
         "Активний розділ підсвічується.\n"
         "У верхній частині — назва поточної сторінки та годинник.\n\n"
         "Розділ «Адмінка» видимий лише для адміністраторів."),
        ("Гарячі клавіші",
         "На екрані входу: Enter у полі логіну → перехід до пароля.\n"
         "Enter у полі пароля → спроба входу.\n"
         "Подвійний клік на рядку таблиці → редагування (де доступно)."),
    ]),
    ("Адмінка", [
        ("Що може адмін?",
         "Розділ «Адмінка» містить 4 вкладки:\n\n"
         "  Користувачі — створення, зміна ролей, скидання блокування, видалення\n"
         "  Працівники  — повне CRUD-управління\n"
         "  Завдання    — створення, видалення, зміна статусів\n"
         "  Аналітика   — робочий час усіх користувачів\n\n"
         "Адмін не може видалити власний акаунт."),
        ("Управління користувачами",
         "Створити: «Створити користувача» → логін, пароль, роль.\n"
         "Ролі: admin (повний доступ) або user (обмежений).\n"
         "Скинути блокування: вибрати користувача → «Скинути блокування».\n\n"
         "Таблиця показує телефон, email, організацію та дати входу."),
        ("Безпека",
         "Рекомендується змінити пароль admin/admin одразу після першого входу.\n"
         "Не передавайте свої облікові дані іншим особам.\n"
         "При підозрілій активності — зверніться до адміністратора."),
    ]),
]


class FAQWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Інструкція — CRM System")
        self.win.geometry("820x620")
        self.win.configure(bg=C['white'])
        self.win.grab_set()
        self._center(parent)
        self._build()

    def _center(self, parent):
        self.win.update_idletasks()
        w, h = 820, 620
        pw = parent.winfo_rootx() + parent.winfo_width() // 2
        ph = parent.winfo_rooty() + parent.winfo_height() // 2
        self.win.geometry(f"{w}x{h}+{pw - w // 2}+{ph - h // 2}")

    def _build(self):
        tk.Frame(self.win, bg=C['accent'], height=4).pack(fill="x")

        hdr = tk.Frame(self.win, bg=C['white'])
        hdr.pack(fill="x", padx=24, pady=(20, 0))
        tk.Label(hdr, text="Інструкція", font=("Segoe UI", 15, "bold"),
                 bg=C['white'], fg=C['text']).pack(side="left")
        tk.Label(hdr, text="CRM System v4.0",
                 font=("Segoe UI", 9), bg=C['white'], fg=C['muted']).pack(side="right", anchor="s")

        mk_sep(self.win).pack(fill="x", pady=(10, 0))

        main = tk.Frame(self.win, bg=C['ibg'])
        main.pack(fill="both", expand=True)

        left = tk.Frame(main, bg=C['ibg'], width=240)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        scroll_left = tk.Canvas(left, bg=C['ibg'], highlightthickness=0, width=240)
        scroll_left.pack(side="left", fill="both", expand=True)
        left_inner = tk.Frame(scroll_left, bg=C['ibg'])
        scroll_left.create_window((0, 0), window=left_inner, anchor="nw", width=230)

        mk_sep(main, orient='v').pack(side="left", fill="y")

        right = tk.Frame(main, bg=C['white'])
        right.pack(side="left", fill="both", expand=True)

        tk.Label(left_inner, text="РОЗДІЛИ", font=("Segoe UI", 8, "bold"),
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
            tk.Label(left_inner, text=section, font=("Segoe UI", 8, "bold"),
                     bg=C['ibg'], fg=C['sidebar']).pack(anchor="w", padx=16, pady=(14, 4))
            for q, a in pairs:
                b = tk.Button(left_inner, text=q, font=("Segoe UI", 9),
                              bg=C['ibg'], fg=C['text'], relief="flat", bd=0,
                              pady=6, padx=12, anchor="w", cursor="hand2",
                              wraplength=200, justify="left",
                              command=lambda qq=q, aa=a, btn_ref=None: self._show(qq, aa))
                b.pack(fill="x", padx=4)
                if first:
                    self._show(q, a)
                    self._highlight_btn(b)
                    first = False
                b.bind("<Enter>", lambda e, btn=b: btn.config(bg=C['border']) if btn != self.active_btn else None)
                b.bind("<Leave>", lambda e, btn=b: btn.config(bg=C['ibg']) if btn != self.active_btn else None)

        left_inner.bind("<Configure>", lambda e: scroll_left.config(scrollregion=scroll_left.bbox("all")))

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


def pg_faq(self):
    """In-app FAQ page using the same content as FAQWindow."""
    main = tk.Frame(self.page, bg=C['bg'])
    main.pack(fill="both", expand=True)
    main.columnconfigure(1, weight=1)
    main.rowconfigure(0, weight=1)

    left = tk.Frame(main, bg=C['card'], width=260,
                    highlightthickness=1, highlightbackground=C['border'])
    left.grid(row=0, column=0, sticky="ns", padx=(20, 0), pady=20)
    left.grid_propagate(False)

    scroll = tk.Canvas(left, bg=C['card'], highlightthickness=0)
    scroll.pack(fill="both", expand=True)
    left_inner = tk.Frame(scroll, bg=C['card'])
    scroll.create_window((0, 0), window=left_inner, anchor="nw", width=248)

    right = tk.Frame(main, bg=C['white'],
                     highlightthickness=1, highlightbackground=C['border'])
    right.grid(row=0, column=1, sticky="nsew", padx=(12, 20), pady=20)
    right.rowconfigure(1, weight=1)
    right.columnconfigure(0, weight=1)

    tk.Label(left_inner, text="РОЗДІЛИ", font=("Segoe UI", 8, "bold"),
             bg=C['card'], fg=C['muted']).pack(pady=(16, 6), padx=12, anchor="w")

    title_lbl = tk.Label(right, text="", font=("Segoe UI", 13, "bold"),
                          bg=C['white'], fg=C['text'], anchor="w")
    title_lbl.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))

    mk_sep(right).grid(row=0, column=0, sticky="ew", padx=24, pady=(8, 0))

    body_txt = tk.Text(right, font=("Segoe UI", 10), bg=C['white'], fg=C['text2'],
                        relief="flat", bd=0, wrap="word", state="disabled",
                        cursor="arrow", spacing1=4, spacing3=6)
    body_txt.grid(row=1, column=0, sticky="nsew", padx=24, pady=16)

    active = [None]

    def show_qa(q, a):
        title_lbl.config(text=q)
        body_txt.config(state="normal")
        body_txt.delete("1.0", "end")
        body_txt.insert("1.0", a)
        body_txt.config(state="disabled")

    def highlight(btn):
        if active[0]:
            active[0].config(bg=C['card'], fg=C['text'])
        active[0] = btn
        btn.config(bg=C['tree_sel'], fg=C['accent'])

    first = True
    for section, pairs in FAQ_SECTIONS:
        tk.Label(left_inner, text=section, font=("Segoe UI", 8, "bold"),
                 bg=C['card'], fg=C['accent']).pack(anchor="w", padx=12, pady=(12, 4))
        for q, a in pairs:
            b = tk.Button(left_inner, text=q, font=("Segoe UI", 9),
                          bg=C['card'], fg=C['text'], relief="flat", bd=0,
                          pady=5, padx=10, anchor="w", cursor="hand2",
                          wraplength=220, justify="left",
                          command=lambda qq=q, aa=a, bb=None: (show_qa(qq, aa), highlight(bb)))
            b.pack(fill="x", padx=4)
            b.configure(command=lambda qq=q, aa=a, bb=b: (show_qa(qq, aa), highlight(bb)))
            if first:
                show_qa(q, a)
                highlight(b)
                first = False
            b.bind("<Enter>", lambda e, btn=b: btn.config(bg=C['ibg']) if btn != active[0] else None)
            b.bind("<Leave>", lambda e, btn=b: btn.config(bg=C['card']) if btn != active[0] else None)

    left_inner.bind("<Configure>", lambda e: scroll.config(scrollregion=scroll.bbox("all")))
