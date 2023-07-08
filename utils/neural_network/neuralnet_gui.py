import tkinter as tk
import tkinter.messagebox as mb
from tkinter import filedialog
import time
import cv2
import pandas as pd
import os
import mimetypes
from io import BytesIO
from PIL import ImageTk, Image, UnidentifiedImageError
from config import YOLOv7_PATH, SIZE, CLASS_LIST
from utils.utils import center, Table
from logger.logger_config import logger
from utils.neural_network.neuralnet_moduls import RealTimeObjectDetection, VideoObjectDetection, ImageObjectDetection
from utils.database.database_gui import DatabaseMenu
import customtkinter as ctk


class RealTimeGUIDetect(RealTimeObjectDetection):

    def __init__(self,
                 win,
                 menu,
                 class_list=CLASS_LIST,
                 size=SIZE):
        """
        Класс, который представляет собой графическое взаимодействие с моделью нейронной сети для детекции объектов
        в реальном времени. Он графически реализует методы из класса RealTimeObjectDetection.
        :param win: Главное окно, которое представляет собой экземпляр класса tkinter.Tk.
        :param menu: Главное меню, которое представляет собой экземпляр класса tkinter.Menu.
        :param class_list: Список классов, которые должны быть обнаружены.
        :param size: Кортеж с шириной и высотой видео.
        """
        assert isinstance(menu, DatabaseMenu), "Параметр menu должен быть объектом класса DatabaseMenu"
        assert isinstance(class_list, list | tuple), "class_list должен иметь тип list или tuple"
        assert isinstance(size, list | tuple), "Размеры должны иметь тип list или tuple"
        assert len(size) == 2 and isinstance(size[0], int) and isinstance(size[1], int), \
            "Список/кортёж size должен иметь 2 элемента, и эти элементы должны иметь тип int"

        self.menu = menu
        self.win = win
        self.class_list = class_list
        self.size = size

    def __call__(self):
        self.frame_buts = ctk.CTkFrame(self.win)
        self.start_display_but = ctk.CTkButton(self.frame_buts, text='Начать поток', command=self._start_display)
        self.frame_buts.pack(expand=True)
        self.start_display_but.pack()

    @staticmethod
    def model_choice_frame(win):
        topframe = tk.Toplevel(win)
        topframe.config(bg='black')
        topframe.iconbitmap("MAI.ico")
        topframe.resizable(width=False, height=False)
        topframe.title('Настройка нейронной сети')
        scroe_threshold, nms_threshold, confidence_threshold = tk.IntVar(value=60), tk.IntVar(value=55), \
                                                               tk.IntVar(value=60)
        ctk.CTkLabel(topframe, text='Score threshold', anchor="w", width=20).grid(column=0, row=0)
        ctk.CTkLabel(topframe, text='NMS threshold', anchor="w", width=20).grid(column=0, row=1)
        ctk.CTkLabel(topframe, text='Confidence threshold', anchor="w", width=20).grid(column=0, row=2)
        ctk.CTkSlider(topframe, variable=scroe_threshold, from_=1, to=100).grid(column=1, row=0)
        ctk.CTkSlider(topframe, variable=nms_threshold, from_=1, to=100).grid(column=1, row=1)
        ctk.CTkSlider(topframe, variable=confidence_threshold, from_=1, to=100).grid(column=1, row=2)
        return topframe, scroe_threshold, nms_threshold, confidence_threshold

    def _start_display(self):
        topframe, scroe_threshold, nms_threshold, confidence_threshold = self.model_choice_frame(self.win)

        def get_model():
            topframe.destroy()
            try:
                super(RealTimeGUIDetect, self).__init__(YOLOv7_PATH, self.class_list, scroe_threshold.get() / 100,
                                                        nms_threshold.get() / 100, confidence_threshold.get() / 100,
                                                        self.size)
                self.net, self.output_layers, self.capture = self.init_model()
                self.width, self.height = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH), \
                                          self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
                self.stop_display_but = ctk.CTkButton(self.frame_buts, text='Остановить поток',
                                                      command=self._stop_display)
                self.stop_display_but.pack(side=ctk.BOTTOM, pady=5)
                self.start_display_but.pack_forget()
                self.frame_buts.pack_configure(expand=False)
                self._create_widgets_and_start_display()
            except IOError:
                mb.showerror('Невозможно открыть веб-камеру')

        choice_but = ctk.CTkButton(topframe, text='Подтвердить', command=get_model)
        choice_but.grid(column=0, row=5, columnspan=2)

        topframe.update()
        topframe.geometry(f"{topframe.winfo_reqwidth()}x{topframe.winfo_reqheight()}")
        center(topframe)

    def _stop_display(self):
        self.stop_display_but.pack_forget()
        self.win.after_cancel(self.performance_control)
        self.continue_display_but = ctk.CTkButton(self.frame_buts, text='Продолжить поток',
                                                  command=self._continue_display)
        self.continue_display_but.pack(side=ctk.TOP, pady=5)
        self.apply_model_but = ctk.CTkButton(self.frame_buts, text='Детектировать объекты', command=self._apply_model)
        self.apply_model_but.pack(side=ctk.TOP, pady=5)

    def _apply_model(self):
        self.apply_model_but.pack_forget()
        self.frame, self.meta = self.get_detected_frame(self.net, self.output_layers, self.frame)

        topframe = tk.Toplevel(self.win)
        topframe.iconbitmap("MAI.ico")
        topframe.resizable(width=False, height=False)
        topframe.title('Скриншот')
        image_toplvl = ImageGUIDetect(topframe, self.menu)
        image_toplvl()
        image_toplvl.start_display_but.pack_forget()
        if self.video_name:
            image_toplvl.initialfilename = f"{self.video_name}_frame{self.count_frames}"
        else:
            image_toplvl.initialfilename = "frame_" + time.strftime("%d-%m-%Y_%H-%M-%S")
        image_toplvl.img_path = self.frame
        image_toplvl.create_image_panel(self.frame, self.meta)

        topframe.update()
        topframe.geometry(f"{topframe.winfo_reqwidth()}x{topframe.winfo_reqheight()}")
        center(topframe)

    def _continue_display(self):
        self.continue_display_but.pack_forget()
        self.apply_model_but.pack_forget()
        self.stop_display_but = ctk.CTkButton(self.frame_buts, text='Остановить поток',
                                              command=self._stop_display)
        self.stop_display_but.pack(side=ctk.TOP, pady=5)
        self._update()

    def _create_widgets_and_start_display(self, videoname=False):
        self.video_name = videoname
        self.count_frames = 0
        self.panel = tk.Label(self.win, width=int(self.width), height=int(self.height))
        self.panel.pack(side=ctk.TOP)
        self.starting_time = time.time()
        self.frame_timer = int(self.capture.get(cv2.CAP_PROP_FPS))
        self._update()

    def _update(self):
        self.frame = self.get_frame(self.capture, self.starting_time)
        if self.frame is not None:
            self.count_frames += 1
            frame = ImageTk.PhotoImage(Image.fromarray(self.frame))
            self.panel.configure(image=frame)
            self.panel.image = frame

        self.performance_control = self.win.after(self.frame_timer, self._update)


class VideoGUIDetect(RealTimeGUIDetect, VideoObjectDetection):

    def __init__(self,
                 win,
                 menu,
                 class_list=CLASS_LIST,
                 size=SIZE):
        """
        Класс, который представляет собой графическое взаимодействие с моделью нейронной сети для детекции объектов
        на видео. Он графически реализует методы из класса VideoObjectDetection.
        :param win: Главное окно, которое представляет собой экземпляр класса tkinter.Tk.
        :param menu: Главное меню, которое представляет собой экземпляр класса tkinter.Menu.
        :param class_list: Список классов, которые должны быть обнаружены.
        :param size: Кортеж с шириной и высотой видео.
        """

        assert isinstance(menu, DatabaseMenu), "Параметр menu должен быть объектом класса DatabaseMenu"
        assert isinstance(class_list, list | tuple), "class_list должен иметь тип list или tuple"
        assert isinstance(size, list | tuple), "Размеры должны иметь тип list или tuple"
        assert len(size) == 2 and isinstance(size[0], int) and isinstance(size[1], int), \
            "Список/кортёж size должен иметь 2 элемента, и эти элементы должны иметь тип int"

        self.class_list = class_list
        self.size = size
        self.menu = menu
        self.win = win

    def __call__(self):
        self.frame_buts = ctk.CTkFrame(self.win)
        self.frame_buts.pack(expand=True)
        self.start_display_but = ctk.CTkButton(self.frame_buts, text='Выбрать видеоролик', command=self._start_display)
        self.start_display_but.pack(pady=5)

    def _start_display(self):
        try:
            self.continue_display_but.pack_forget()
        except:
            pass
        try:
            self.apply_model_but.pack_forget()
        except:
            pass
        try:
            self.stop_display_but.pack_forget()
        except:
            pass
        topframe, scroe_threshold, nms_threshold, confidence_threshold = self.model_choice_frame(self.win)

        def get_model():
            topframe.destroy()
            super(RealTimeGUIDetect, self).__init__(YOLOv7_PATH, self.class_list, scroe_threshold.get() / 100,
                                                    nms_threshold.get() / 100, confidence_threshold.get() / 100,
                                                    self.size)
            self.net, self.output_layers = self.init_model()

            video_path = filedialog.askopenfilename(title='Выбор видео', defaultextension='mp4', initialdir='.')
            if not mimetypes.guess_type(video_path)[0].startswith('video'):
                mb.showwarning('Предупреждение!', 'Вы пытаетесь открыть не видео!')
            else:
                video_name = video_path.split('/')[-1]
                try:
                    logger.info(f"Успешное открытие {video_path.split('/')[-1]} видео")
                    widget_list = self.win.winfo_children()
                    if len(widget_list) > 1:
                        self.win.after_cancel(self.performance_control)
                        for i in range(1, len(widget_list)):
                            widget_list[i].pack_forget()
                    self.capture = self.load_capture(video_path)
                    self.width, self.height = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH), \
                                              self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

                    self.save_frame_but.pack_forget()
                    self.stop_display_but.pack_forget()
                    self.continue_display_but.pack_forget()
                except AttributeError:
                    pass
                except IOError:
                    mb.showerror(f"Невозможно открыть видео {video_path.split('/')[-1]}")
                    exit()
                finally:
                    self.frame_buts.pack_configure(expand=False)
                    self.stop_display_but = ctk.CTkButton(self.frame_buts, text='Остановить поток',
                                                          command=self._stop_display)
                    self.stop_display_but.pack(side=ctk.BOTTOM, pady=5)
                    self._create_widgets_and_start_display(video_name)

        choice_but = ctk.CTkButton(topframe, text='Подтвердить', command=get_model)
        choice_but.grid(column=0, row=5, columnspan=2)

        topframe.update()
        topframe.geometry(f"{topframe.winfo_reqwidth()}x{topframe.winfo_reqheight()}")
        center(topframe)


class ImageGUIDetect(ImageObjectDetection):

    def __init__(self,
                 win,
                 menu,
                 class_list=CLASS_LIST,
                 size=SIZE):
        """
        Класс, который представляет собой графическое взаимодействие с моделью нейронной сети для детекции объектов
        на изображении. Он графически реализует методы из класса ImageObjectDetection.
        :param win: Главное окно, которое представляет собой экземпляр класса tkinter.Tk.
        :param menu: Главное меню, которое представляет собой экземпляр класса tkinter.Menu.
        :param class_list: Список классов, которые должны быть обнаружены.
        :param size: Кортеж с шириной и высотой изображения.
        """
        assert isinstance(menu, DatabaseMenu), "Параметр menu должен быть объектом класса DatabaseMenu"
        assert isinstance(class_list, list | tuple), "class_list должен иметь тип list или tuple"
        assert isinstance(size, list | tuple), "Размеры должны иметь тип list или tuple"
        assert len(size) == 2 and isinstance(size[0], int) and isinstance(size[1], int), \
            "Список/кортёж size должен иметь 2 элемента, и эти элементы должны иметь тип int"

        self.class_list = class_list
        self.size = size
        self.menu = menu
        self.win = win

    def __call__(self):
        self.start_display_but = ctk.CTkButton(self.win, text='Выбрать изображение', command=self._open_img)
        self.start_display_but.pack(expand=True)

    def _open_img(self):
        topframe, scroe_threshold, nms_threshold, confidence_threshold = RealTimeGUIDetect.model_choice_frame(self.win)


        def get_model():
            topframe.destroy()
            try:
                self.img_path = filedialog.askopenfilename(title='Выбор изображения', defaultextension='jpg',
                                                           initialdir='.')

                img = Image.open(self.img_path)
                img = img.resize((640, 640), Image.LANCZOS)
                img = ImageTk.PhotoImage(img)
                self.initialfilename = f"detected_{self.img_path.split('/')[-1].split('.')[0]}"
                logger.info(f"Успешное открытие {self.img_path.split('/')[-1]} изображения")

                super(ImageGUIDetect, self).__init__(YOLOv7_PATH, self.class_list, scroe_threshold.get() / 100,
                                                     nms_threshold.get() / 100, confidence_threshold.get() / 100,
                                                     self.size)
                self.net, self.output_layers = self.init_model()
                self.capture = self.load_capture(self.img_path)

                widget_list = self.win.winfo_children()
                if len(widget_list) > 1:
                    for i in range(1, len(widget_list)):
                        widget_list[i].pack_forget()
                self.create_image_panel()
            except UnidentifiedImageError:
                mb.showwarning('Предупреждение', 'Вы пытаетесь открыть не изображение!')
            except AttributeError:
                pass

        choice_but = ctk.CTkButton(topframe, text='Подтвердить', command=get_model)
        choice_but.grid(column=0, row=5, columnspan=2)

        topframe.update()
        topframe.geometry(f"{topframe.winfo_reqwidth()}x{topframe.winfo_reqheight()}")
        center(topframe)

    def _save_img(self, img):
        if not os.path.isdir('saved_data'):
            os.mkdir('saved_data')
        if not os.path.isdir('saved_data/images'):
            os.mkdir('saved_data/images')
        result = filedialog.asksaveasfilename(title="Сохранение изображения", filetypes=(
            ('JPEG', ('*.jpg', '*.jpeg', '*.jpe')), ('PNG', '*.png'), ('BMP', ('*.bmp', '*.jdib')),
            ('GIF', '*.gif')), initialdir=os.path.join(os.getcwd(), 'saved_data/images'),
                                              initialfile=self.initialfilename + ".jpg")
        if result:
            img = ImageTk.getimage(img)
            img = img.convert('RGB')
            img.save(result)
            try:
                logger.info(f"Успешное сохранения {self.img_path.split('/')[-1]} изображения")
            except AttributeError:
                logger.info(f"Успешное сохранения кадра")

    def create_image_panel(self, image=None, frame=None):
        self.panel = tk.Label(self.win)
        self.panel.pack()
        self.starting_time = time.time()
        self._update(image, frame)

    def _update(self, image=None, meta=None):
        if image is None and meta is None:
            image, meta = self.get_detected_frame(self.capture, self.net, self.output_layers, )
        frame_table_buts = ctk.CTkFrame(self.win)
        frame_table_buts.pack()

        save_img_but = ctk.CTkButton(frame_table_buts, text='Сохранить изображение',
                                     command=lambda: self._save_img(image))
        save_img_but.pack(side=ctk.TOP, pady=5)
        if image is not None:
            image = ImageTk.PhotoImage(Image.fromarray(image))
            self.panel.configure(image=image)
            self.panel.image = image
            meta_dict = {'class_obj': [],
                         'confidence': [],
                         'x_min': [],
                         'y_min': [],
                         'x_max': [],
                         'y_max': []}
            if len(meta) > 0:
                for (classid, confidence, box) in meta:
                    meta_dict['class_obj'].append(self.class_list[classid])
                    meta_dict['confidence'].append(confidence)
                    meta_dict['x_min'].append(box[0])
                    meta_dict['y_min'].append(box[1])
                    meta_dict['x_max'].append(box[2])
                    meta_dict['y_max'].append(box[3])
                df_meta = pd.DataFrame(meta_dict)

                frame_table = ctk.CTkFrame(frame_table_buts)
                frame_table.pack()

                table_widget = Table(frame_table, df_meta)
                table_widget.pack()

                save_table_buts_frame = ctk.CTkFrame(frame_table_buts)
                save_table_buts_frame.pack()

                save_table_csv_but = ctk.CTkButton(save_table_buts_frame, text='Сохранить таблицу в формате csv',
                                                   command=lambda: self._save_table_csv(df_meta, image))
                save_table_csv_but.pack(padx=4, side=ctk.RIGHT)

                save_table_sql_but = ctk.CTkButton(save_table_buts_frame, text='Сохранить таблицу в формате SQL',
                                                   command=lambda: self._save_table_sql(df_meta, image))
                save_table_sql_but.pack(padx=4, side=ctk.RIGHT)

            return image, meta

    def _make_full_df(self, dataframe, tk_img):
        img = ImageTk.getimage(tk_img)
        img = img.convert('RGB')
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()

        # --------------------------------------------------------------------------------------------------------------
        # Код для вывода на экран байтового изображения
        # image = Image.open(BytesIO(img_bytes))
        # image.show()
        # --------------------------------------------------------------------------------------------------------------

        image_df = pd.DataFrame(columns=['image'], data=[[img_bytes]] * len(dataframe))
        full_df = pd.merge(image_df, dataframe, left_index=True, right_index=True)

        return full_df

    def _save_table_csv(self, dataframe, tk_img):
        table_df = self._make_full_df(dataframe, tk_img)
        if not os.path.isdir('saved_data'):
            os.mkdir('saved_data')
        if not os.path.isdir('saved_data/tables'):
            os.mkdir('saved_data/tables')
        result = filedialog.asksaveasfilename(title="Сохранение таблицы",
                                              filetypes=[('All tyes(*.*)', '*.*'), ("csv file(*.csv)", "*.csv")],
                                              initialdir=os.path.join(os.getcwd(), 'saved_data/tables'),
                                              initialfile=self.initialfilename + ".csv",
                                              defaultextension=[('All tyes(*.*)', '*.*'), ("csv file(*.csv)", "*.csv")])
        if result:
            table_df.to_csv(result)
            logger.info("Успешное сохранения таблицы в формате csv")

    def _save_table_sql(self, dataframe, tk_img):
        if self.menu.db_funtional == None or self.menu.db_funtional.engine == None:
            mb.showerror('Ошибка', 'Вы не подключились к базе данных!')
        else:
            names_tables = self.menu.db_funtional.get_table_names()
            if len(names_tables) > 0:
                table_df = self._make_full_df(dataframe, tk_img)

                topframe = ctk.CTkToplevel(self.win)
                topframe.iconbitmap("MAI.ico")
                topframe.resizable(width=False, height=False)
                topframe.title('Выбор таблицы')

                frame = ctk.CTkFrame(topframe)
                frame.pack(expand=True)

                ctk.CTkLabel(frame, text='Имя таблицы', anchor=ctk.CENTER, width=20).pack(pady=5)
                combo = ctk.CTkComboBox(frame, width=200, values=names_tables, state="readonly")
                combo.pack(pady=5)

                def get_info():
                    table_name = combo.get()
                    if not table_name:
                        mb.showwarning('Предупреждение', 'Вы не выбрали таблицу!')
                    else:
                        result = self.menu.db_funtional.insert_data(table_name, table_df)
                        if result:
                            mb.showinfo('Успех', f'Вы успешно записали данные в таблицу {table_name}!')
                            topframe.destroy()
                        else:
                            mb.showerror('Ошибка', f'Невозможно записать данные в таблицу {table_name}!')

                choice_but = ctk.CTkButton(frame, text='Подтвердить', command=get_info)
                choice_but.pack(pady=5)

                topframe.update()
                topframe.geometry(f"{topframe.winfo_reqwidth() + 30}x{topframe.winfo_reqheight() + 30}")
                center(topframe)
            else:
                mb.showwarning('Предупреждение', f'В базе данных {self.menu.db_info["db_name"]} нет таблиц!')
