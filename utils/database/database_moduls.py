import pandas as pd
from sqlalchemy import inspect, create_engine, Table, Column, Integer, String, Float, LargeBinary, MetaData
from sqlalchemy.exc import OperationalError, ProgrammingError, InvalidRequestError
from sqlalchemy_utils import create_database, database_exists, drop_database
from logger.logger_config import logger


class DatabaseFunctionality:

    def __init__(self, db_type, db_info):
        """
        Класс, определяющий методы для взаимодействия с базами данных, такие как подключение к БД, создание БД,
        удаление БД, создание таблиц в БД, внесение данных в эти таблицы, получение информации из них и их удаление.
        :param db_type: строка, представляющая собой тип базы данных длф подключения
        ("postgres", "mysql", "mssql", "oracle").
        :param db_info: словарь, содержащий информацию о соединении, необходимую для подключения к базе данных.
        """

        assert isinstance(db_type, str), "Параметр db_type должен иметь тип str и быть названием базы данных"
        assert db_type in ("postgresql", "mysql", "mssql", "oracle"), \
            'Параметр db_type должен быть или "postgres" или, "mysql" или, "mssql" или, "oracle"'
        assert isinstance(db_info, dict), \
            "Параметр db_info должен иметь тип dict и содержать информацию о базе данных для подключения"

        self.db_type = db_type
        self.db_user = db_info['db_user']
        self.db_password = db_info['db_password']
        self.db_name = db_info['db_name']
        self.db_host = db_info['db_host']
        self.db_port = db_info['db_port']

        self.engine = None
        self.inspector = None
        self.metadata = None

    def create_database(self):
        db_url = f"://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        if self.db_type != 'mssql':
            db_url = self.db_type + db_url
        else:
            db_url = "oracle+pyodbc" + db_url
        try:
            create_database(db_url)
            self.engine = create_engine(db_url)
            self.metadata = MetaData()
            self.metadata.bind = self.engine
            self.inspector = inspect(self.engine)

            logger.info(f'Успешное создание базы данных {self.db_name} и подключение к ней')
            return self.engine.connect()

        # ProgrammingError - БД уже существует
        except ProgrammingError as exc:
            logger.error(
                f'База данных {self.db_name} уже существует, либо введены неверные данные для подключения к ней')
            return None

        # OperationalError - неправильно введены данные
        except OperationalError as exc:
            logger.error(f'Возникла ошибка {exc}. Неверно введены данные базы данных {self.db_name}')
            return False

    def connect_database(self):
        connect_db_url = f"://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        if self.db_type != 'mssql':
            connect_db_url = self.db_type + connect_db_url
        else:
            connect_db_url = "oracle+pyodbc" + connect_db_url
        if database_exists(connect_db_url):
            self.engine = create_engine(connect_db_url)
            self.metadata = MetaData()
            self.metadata.bind = self.engine
            self.inspector = inspect(self.engine)

            logger.info(f'Успешное подключение к базе данных {self.db_name}')
            return self.engine.connect()
        else:
            logger.error(f'Базы данных {self.db_name} не существует')
            return False  # Такая БД уже есть, либо неправильно введены данные

    def create_table(self, table_name):
        assert isinstance(table_name, str), "Переменная table_name должна иметь тип str"

        # if self.inspector.has_table(table_name):
        #     logger.error(f'В базе данных {self.db_name} уже имеется таблица с именем {table_name}')
        #     return False
        # else:
        try:
            Table(table_name, self.metadata,
                  Column('id', Integer, primary_key=True, autoincrement=True),
                  Column('image', LargeBinary, nullable=False),
                  Column('class_obj', String(20), nullable=False),
                  Column('confidence', Float, nullable=False),
                  Column('x_min', Integer, nullable=False),
                  Column('y_min', Integer, nullable=False),
                  Column('x_max', Integer, nullable=False),
                  Column('y_max', Integer, nullable=False),
                  )

            self.metadata.create_all(self.engine)
            self.metadata.reflect(bind=self.engine)

            logger.info(f'Успешное создание таблицы {table_name} в базе данных {self.db_name}')
            return True
        except InvalidRequestError:
            logger.error(f'В базе данных {self.db_name} уже имеется таблица с именем {table_name}')
            return False

    def insert_data(self, table_name, df_data):
        assert isinstance(table_name, str), "Переменная table_name должна иметь тип str и обозначать имя таблицы"
        assert isinstance(df_data, pd.DataFrame), \
            "Переменная df_data должна иметь тип pd.DataFrame и включать в себя данные для внесения в таблицу"

        try:
            with self.engine.connect() as conn:
                df_data.to_sql(table_name, conn, if_exists="append", index=False)
                conn.commit()

            logger.info(f'Успешно внесение данных в таблицу {table_name} из базы данных {self.db_name}')
            return True
        except Exception as exc:
            logger.error(
                f'Возникла ошибка {exc}. Ошибка при внесении данных в таблицу {table_name} из базы данных {self.db_name}')
            return False

    def get_table(self, table_name):
        assert isinstance(table_name, str), "Переменная table_name должна иметь тип str и обозначать имя таблицы"

        table = Table(table_name, self.metadata, autoload_with=self.engine)
        query = table.select()
        table_df = pd.read_sql_query(query, self.engine.connect())
        return table_df

    def get_table_names(self):
        # result = self.inspector.get_table_names()
        self.metadata.reflect(bind=self.engine)
        result = list(self.metadata.tables.keys())
        return result

    def delete_table(self, table_name):
        assert isinstance(table_name, str), "Переменная table_name должна иметь тип str и обозначать имя таблицы"

        try:
            self.metadata.reflect(bind=self.engine)
            table_to_drop = self.metadata.tables[table_name]
            self.metadata.drop_all(bind=self.engine, tables=[table_to_drop])
            self.metadata.remove(table_to_drop)

            logger.info(f'Успешное удаление таблицы {table_name} из базы данных {self.db_name}')
            return True
        except Exception as exc:
            logger.error(
                f'Возникла ошибка {exc}. Не получилось удалить таблицу {table_name} из базы данных {self.db_name}')
            return False

    def get_datbase_names(self):
        self.metadata.reflect(bind=self.engine)
        # schema_names = self.engine.dialect.get_schema_names(connection=self.engine.connect())
        schema_names = self.metadata.bind.dialect.get_schema_names(connection=self.metadata.bind.connect())
        return schema_names

    def delete_database(self):
        try:
            drop_database(self.metadata.bind.url)
            self.engine = None
            self.metadata = None
            self.inspector = None

            logger.info(f'Успешное удаление базы данных {self.db_name}')
            return True
        except Exception as exc:
            logger.error(f'Возникла ошибка {exc}. Не получилось удалить базу данных {self.db_name}')
            return False
