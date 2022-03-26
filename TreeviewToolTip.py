from tkinter import *
from tkinter import ttk
import tkinter.font as tkfont

#####################
# WORK IN PROGRESS
#####################


class TVToolTip:
    """Tooltip for treeview items"""

    def __init__(self, root: Tk, *trees: ttk.Treeview):
        self.delay = 1000
        self.delay_timeout = 4500
        self.root = root
        self.style = ttk.Style(root)
        self.font = tkfont.Font(font=self.style.lookup("Treeview", "font"))
        self.trees = trees
        root.bind("<Motion>", self.hide)
        for tree in trees:
            tree.bind("<Motion>", self.schedule)
        self.timer = self.scheduledItem = self.prevItem = ""

    def schedule(self, event: Event):
        tree = self.root.nametowidget(event.widget)
        item = tree.identify_row(event.y)
        # if cursor is still on the same item do nothing
        # else if item changes, cancel the queued tooltip
        # and make a new one for the new item
        if self.scheduledItem:
            if self.scheduledItem == item:
                return
            else:
                self.root.after_cancel(self.timer)
        self.timer = self.root.after(self.delay, self.show, event)
        self.scheduledItem = item

    def show(self, event: Event):
        self.scheduledItem = ""
        tree = self.root.nametowidget(event.widget)
        item = tree.identify_row(event.y)
        size = self.font.measure(item)
        # print(f"{item=} {size=} {self.style.lookup('Treeview','indent')=}")
        if not item or (item == self.prevItem) or tree.get_children(item):
            return
        if self.prevItem != item:
            self.hide()
        self.prevItem = item
        x = tree.winfo_rootx() + tree.winfo_width()
        # y = self.tree.winfo_pointery() - self.tree.winfo_vrooty()
        # y = tree.winfo_pointery()
        y = tree.winfo_rooty() + tree.bbox(item)[1]
        self.win = Toplevel(tree)
        self.win.wm_overrideredirect(True)
        self.win.geometry(f"+{x}+{y}")
        self.label = ttk.Label(
            self.win,
            text=tree.item(item, "text"),
            justify=LEFT,
            background=self.style.lookup("TLabel", "background"),
            relief=SOLID,
            borderwidth=1,
        )
        self.label.pack()
        # tree.after(self.delay_timeout, self.hide)

    def hide(self, event: Event = ""):
        if self.prevItem:
            self.label.forget()
            self.win.destroy()
