from utils.neural_network.neuralnet_gui import RealTimeGUIDetect, VideoGUIDetect, ImageGUIDetect
from utils.database.database_gui import DatabaseMenu
import tkinter as tk
from utils.utils import center
import customtkinter as ctk
from ttkthemes import ThemedTk

ctk.set_appearance_mode("dark")

# root = tk.Tk()
root = ThemedTk(theme="black")
root.config(bg='black')
root.title('Детекция запрещенных объектов багажа в аэропорту')
root.geometry('1250x1000')
center(root)
root.resizable(width=False, height=False)
root.iconbitmap("Default.ico")

mainmenu = tk.Menu(root)
root.config(menu=mainmenu)

db_menu = DatabaseMenu(root, mainmenu)
db_menu()

tabControl = ctk.CTkTabview(root)
tab_realtime = tabControl.add('Детекция в реальном времени')
tab_video = tabControl.add('Видеодетекция')
tab_image = tabControl.add('Фотодетекция')
tabControl.pack(expand=1, fill="both", pady=10)

RealTimeGUIDetect(tab_realtime, db_menu)()
VideoGUIDetect(tab_video, db_menu)()
ImageGUIDetect(tab_image, db_menu)()

root.mainloop()
