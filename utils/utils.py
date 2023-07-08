import tkinter as tk
import tkinter.ttk as ttk
import customtkinter as ctk


def counter_decorator(fu):
    def inner(*a, **kw):
        inner.count += 1
        return fu(*a, **kw)

    inner.count = 0
    return inner


class PasswordEntry(ctk.CTkEntry):
    def __init__(self, master=None, show='\u2022', **kw):
        super().__init__(master, show=show, **kw)
        self.show = show
        self.password_visible = False

    def toggle_password_visibility(self):
        if self.password_visible:
            self.configure(show=self.show)
            self.password_visible = False
        else:
            self.configure(show='')
            self.password_visible = True


class Table(tk.Frame):
    def __init__(self, root, df):
        super().__init__(root)
        self.table = ttk.Treeview(self, show="headings", selectmode="browse")
        self.table["columns"] = list(df.columns)
        self.table["displaycolumns"] = list(df.columns)
        for head in list(df.columns):
            self.table.heading(head, text=head, anchor=tk.CENTER)
            self.table.column(head, anchor=tk.CENTER)
        for index, row in df.iterrows():
            r = []
            for col in list(df.columns):
                r.append(row[col])
            self.table.insert('', tk.END, values=tuple(row))
        scrolltable_y = ttk.Scrollbar(self, command=self.table.yview)
        scrolltable_x = ttk.Scrollbar(self, command=self.table.xview, orient='horizontal')
        self.table.configure(yscrollcommand=scrolltable_y.set, xscrollcommand=scrolltable_x.set)
        scrolltable_x.pack(side=tk.BOTTOM, fill=tk.X)
        scrolltable_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.table.pack(expand=tk.YES, fill=tk.BOTH)
        self.table.configure(height=5)


def center(win):
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()
