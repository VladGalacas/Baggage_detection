import customtkinter as ctk
import tkinter as tk
import tkinter.messagebox as mb
from utils.database.database_moduls import DatabaseFunctionality
from utils.utils import PasswordEntry, Table, center

class DatabaseMenu:

    def __init__(self, root, menu):
        """
        Класс, который представляет собой графическое взаимодействие с базами данных путем создания меню,
        определяемое в библиотеке tkinter. Он графически реализует методы из класса DatabaseFunctionality.
        :param root: Главное окно, которое представляет собой экземпляр класса tkinter.Tk.
        :param menu: Главное меню, которое представляет собой экземпляр класса tkinter.Menu.
        """
        assert isinstance(root, tk.Tk), "Параметр win должен быть объектом класса tkinter.Tk"
        assert isinstance(menu, tk.Menu), "Параметр menu должен быть объектом класса tkinter.Menu"

        self.root = root
        self.menu = menu
        self.db_funtional = None
        self.selected_db_menu = None

    def __call__(self, *args, **kwargs):
        # Меню "База данных"
        self.database_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="База данных", menu=self.database_menu)

        # Подменю "Подключение к БД"
        connection_menu = tk.Menu(self.database_menu, tearoff=0)
        connection_menu.add_command(label="PostgreSQL", command=lambda: self._connect_or_create_database('postgresql',
                                                                                                         'connect'))
        connection_menu.add_command(label="MySQL",
                                    command=lambda: self._connect_or_create_database('mysql', 'connect'))
        # self.connection_menu.add_command(label="SQLite", command=lambda: self._connect_or_create_database('sqlite', 'connect'))
        connection_menu.add_command(label="Oracle",
                                    command=lambda: self._connect_or_create_database('oracle', 'connect'))
        connection_menu.add_command(label="Microsoft SQL Server",
                                    command=lambda: self._connect_or_create_database('mssql', 'connect'))
        self.database_menu.add_cascade(label="Подключение к БД", menu=connection_menu)
        # self.database_menu.add_command(label="Подключение к БД")


        # Подменю "Создание БД"
        create_database_menu = tk.Menu(self.database_menu, tearoff=0)
        create_database_menu.add_command(label="PostgreSQL",
                                         command=lambda: self._connect_or_create_database('postgresql', 'create'))
        create_database_menu.add_command(label="MySQL",
                                         command=lambda: self._connect_or_create_database('mysql', 'create'))
        # self.create_database_menu.add_command(label="SQLite", command=lambda: self._connect_or_create_database('sqlite', 'create'))
        create_database_menu.add_command(label="Oracle",
                                         command=lambda: self._connect_or_create_database('oracle', 'create'))
        create_database_menu.add_command(label="Microsoft SQL Server",
                                         command=lambda: self._connect_or_create_database('mssql', 'create'))
        self.database_menu.add_cascade(label="Создание БД", menu=create_database_menu)
        # self.database_menu.add_command(label="Создание БД")

    def _connect_or_create_database(self, type_db, type_event):
        topframe = tk.Toplevel(self.root)
        topframe.config(bg='black')
        topframe.iconbitmap("MAI.ico")
        topframe.resizable(width=False, height=False)
        topframe.title('Данные базы данных')
        ctk.CTkLabel(topframe, text='Имя пользователя', anchor="w", width=17).grid(column=0, row=0)
        ctk.CTkLabel(topframe, text='Пароль', anchor="w", width=17).grid(column=0, row=1)
        ctk.CTkLabel(topframe, text='Имя базы данных', anchor="w", width=17).grid(column=0, row=2)
        ctk.CTkLabel(topframe, text='Хост', anchor="w", width=17).grid(column=0, row=3)
        ctk.CTkLabel(topframe, text='Порт', anchor="w", width=17).grid(column=0, row=4)

        enter_dict = {}
        enter_dict['user_ent'] = ctk.CTkEntry(topframe, width=200)
        enter_dict['user_ent'].grid(column=1, row=0)
        enter_dict['password_ent'] = PasswordEntry(topframe, width=200)
        visibility_pass_but = ctk.CTkButton(topframe, text='👁',
                                         command=enter_dict['password_ent'].toggle_password_visibility, width=2)
        visibility_pass_but.grid(column=2, row=1)
        enter_dict['password_ent'].grid(column=1, row=1)
        enter_dict['name_ent'] = ctk.CTkEntry(topframe, width=200)
        enter_dict['name_ent'].grid(column=1, row=2)
        enter_dict['host_ent'] = ctk.CTkEntry(topframe, width=200)
        enter_dict['host_ent'].grid(column=1, row=3)
        enter_dict['port_ent'] = ctk.CTkEntry(topframe, width=200)
        enter_dict['port_ent'].grid(column=1, row=4)

        db_info_names = ['db_user', 'db_password', 'db_name', 'db_host', 'db_port']

        def get_info():
            db_info_list = []
            for ents in list(enter_dict.values()):
                db_info_list.append(ents.get())
            self.db_info = dict(zip(db_info_names, db_info_list))
            db_funtional_try = DatabaseFunctionality(type_db, self.db_info)
            if type_event == 'connect':
                event_result_try = db_funtional_try.connect_database()
            else:
                event_result_try = db_funtional_try.create_database()
            if event_result_try == False:
                if type_event == 'connect':
                    mb.showerror('Ошибка',
                                 f'Либо базы данных {self.db_info["db_name"]} не существует, либо вы ввели неверные данные!')
                else:
                    mb.showerror('Ошибка', 'Вы ввели неверные данные!')
            elif event_result_try == None:
                mb.showerror('Ошибка', f"База данных {self.db_info['db_name']} уже существует")
            else:
                self.db_funtional = db_funtional_try
                if type_event == 'connect':
                    mb.showinfo('Успех', f'Вы успешно подключились к базе данных {self.db_info["db_name"]}!')
                else:
                    mb.showinfo('Успех',
                                f'Вы успешно создали базу данных {self.db_info["db_name"]} и подключились к ней!')
                topframe.destroy()
                if self.selected_db_menu != None:
                    self.database_menu.delete(2)
                self.selected_db_menu = tk.Menu(self.database_menu, tearoff=0)
                self.database_menu.add_cascade(label=self.db_info['db_name'], menu=self.selected_db_menu)
                self.view_menu = tk.Menu(self.selected_db_menu, tearoff=0)
                self.delete_table_menu = tk.Menu(self.selected_db_menu, tearoff=0)
                self.table_names = self.db_funtional.get_table_names()
                if len(self.table_names) > 0:
                    for name in self.table_names:
                        self.view_menu.add_command(label=name,
                                                   command=lambda nameview=name: self._view_table(nameview))
                        self.delete_table_menu.add_command(label=name,
                                                           command=lambda namedel=name: self._delete_table(namedel))
                else:
                    self.view_menu.add_command(label="В данной БД таблиц нет")
                    self.delete_table_menu.add_command(label="В данной БД таблиц нет")
                self.selected_db_menu.add_cascade(label="Просмотр таблицы", menu=self.view_menu)
                self.selected_db_menu.add_cascade(label="Удаление таблицы", menu=self.delete_table_menu)
                self.selected_db_menu.add_command(label="Создать таблицу", command=self._create_table)
                # self.selected_db_menu.add_command(label="Удалить базу данных", command=self._delete_db)

        if type_event == 'connect':
            save_but = ctk.CTkButton(topframe, text='Подключиться', command=get_info)
        else:
            save_but = ctk.CTkButton(topframe, text='Создать БД', command=get_info)
        save_but.grid(column=0, row=5, columnspan=2)

        topframe.update()
        topframe.geometry(f"{topframe.winfo_reqwidth()}x{topframe.winfo_reqheight()}")
        center(topframe)

    def _create_table(self):
        topframe = tk.Toplevel(self.root)
        topframe.config(bg='black')
        topframe.iconbitmap("MAI.ico")
        topframe.resizable(width=False, height=False)
        topframe.title('Создание таблицы')

        frame = tk.Frame(topframe)
        frame.pack(expand=True)

        ctk.CTkLabel(frame, text='Имя таблицы', anchor=tk.CENTER, width=20).pack(pady=5)
        ent = ctk.CTkEntry(frame, width=200)
        ent.pack(pady=5)

        def get_info():
            table_name = ent.get()
            result = self.db_funtional.create_table(table_name)
            if result:
                self.table_names = self.db_funtional.get_table_names()

                self.view_menu.delete(0, tk.END)
                self.delete_table_menu.delete(0, tk.END)

                if len(self.table_names) > 0:
                    for name in self.table_names:
                        self.view_menu.add_command(label=name,
                                                   command=lambda nameview=name: self._view_table(nameview))
                        self.delete_table_menu.add_command(label=name,
                                                           command=lambda namedel=name: self._delete_table(namedel))
                else:
                    self.view_menu.add_command(label="В данной БД таблиц нет")
                    self.delete_table_menu.add_command(label="В данной БД таблиц нет")

                mb.showinfo('Успех', f'Вы успешно создали таблицу {table_name}')
                topframe.destroy()
            else:
                mb.showerror('Ошибка', f'Таблица {table_name} уже существует в базе данных {self.db_info["db_name"]}!')

        create_but = ctk.CTkButton(frame, text='Создать таблицу', command=get_info)
        create_but.pack(pady=5)

        topframe.update()
        topframe.geometry(f"{topframe.winfo_reqwidth() + 30}x{topframe.winfo_reqheight() + 30}")
        center(topframe)

    def _view_table(self, name_table):
        topframe = tk.Toplevel(self.root)
        topframe.config(bg='black')
        topframe.iconbitmap("MAI.ico")
        topframe.resizable(width=False, height=False)
        topframe.title(f'Таблица {name_table}')

        df_table = self.db_funtional.get_table(name_table)
        table_widget = Table(topframe, df_table)
        table_widget.table.configure(height=20)
        table_widget.pack()

        topframe.update()
        topframe.geometry(f"{topframe.winfo_reqwidth()}x{topframe.winfo_reqheight()}")
        center(topframe)

    def _delete_table(self, name_table):
        ask_drop_table = mb.askyesno('Удаление таблицы', f'Вы действительно хотите удалить таблицу {name_table}?')
        if ask_drop_table:
            drop_result = self.db_funtional.delete_table(name_table)
            if drop_result:
                self.table_names = self.db_funtional.get_table_names()

                self.view_menu.delete(0, tk.END)
                self.delete_table_menu.delete(0, tk.END)

                if len(self.table_names) > 0:
                    for name in self.table_names:
                        self.view_menu.add_command(label=name,
                                                   command=lambda nameview=name: self._view_table(nameview))
                        self.delete_table_menu.add_command(label=name,
                                                           command=lambda namedel=name: self._delete_table(namedel))
                else:
                    self.view_menu.add_command(label="В данной БД таблиц нет")
                    self.delete_table_menu.add_command(label="В данной БД таблиц нет")

                mb.showinfo('Успех', f'Вы успешно удалили таблицу {name_table}')
            else:
                mb.showerror('Ошибка', f'Ошибка при удалении таблицы {name_table}')

    def _delete_db(self):
        ask_drop_db = mb.askyesno('Удаление базы данных',
                                  f'Вы действительно хотите удалить базу данных {self.db_info["db_name"]}?')
        if ask_drop_db:
            drop_result = self.db_funtional.delete_database()
            if drop_result:
                self.database_menu.delete(2)
                mb.showinfo('Успех', f'Вы успешно удалили базу данных {self.db_info["db_name"]}')
