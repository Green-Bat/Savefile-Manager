from tkinter import Event, Toplevel
from tkinter.ttk import Treeview, Label, Style
import tkinter.font as tkfont


class TVToolTip:
    """Tooltip for treeview objects"""

    def __init__(self, tree: Treeview, *, extra_width: int = 0):
        self.delay = 500
        self.delay_timeout = 4500
        self.padding = 5
        self.tree = tree
        self.extra_width = extra_width
        self.currItem = ""
        self.win = self.timer = None

        self.style = Style(tree)
        self.font = tkfont.Font(font=self.style.lookup("Treeview", "font"))
        indicator_margins = self.style.lookup("Treeview.Item", "indicatormargins")
        indicator_margins = str(indicator_margins[0]) if indicator_margins else ""
        self.indicator_margins = int(indicator_margins or 0)

    def bind(self):
        self.func_id_motion = self.tree.bind("<Motion>", self.schedule)
        self.func_id_leave = self.tree.bind("<Leave>", self.unschedule)

    def unbind(self):
        self.tree.unbind("<Motion>", self.func_id_motion)
        self.tree.unbind("<Leave>", self.func_id_leave)

    def schedule(self, event: Event):
        item = self.tree.identify("item", event.x, event.y)
        if self.currItem == self.tree.item(item, "text"):
            return
        self.unschedule()
        self.timer = self.tree.after(self.delay, self.show, item)

    def unschedule(self, event: Event = None):
        if self.timer:
            self.tree.after_cancel(self.timer)
            self.timer = None
        self.hide()

    def show(self, item: str):
        if not (item and self.tree.bbox(item)):
            return

        item_text = self.tree.item(item, "text")
        tree_width = self.tree.bbox(item)[2]
        text_size = self.font.measure(item_text)
        # Lookup treeview indent or default to 10
        # and multiply by level of indentation
        indet_lvl = int(
            self.style.lookup("Treeview", "indent") or 10
        ) * self.get_indentlvl(item)

        item_width = (
            text_size
            + indet_lvl
            + self.indicator_margins
            + self.padding
            + self.extra_width
        )

        if item_width < tree_width:
            return

        self.currItem = item_text
        x = self.tree.winfo_pointerx() + 20
        y = self.tree.winfo_rooty() + self.tree.bbox(item)[1] + 15
        self.win = Toplevel(self.tree)
        self.win.wm_overrideredirect(True)
        self.win.geometry(f"+{x}+{y}")
        self.label = Label(
            self.win,
            text=item_text,
            justify="left",
            background=self.style.lookup("TLabel", "background"),
            relief="solid",
            borderwidth=1,
        )
        self.label.pack()
        # self.tree.after(self.delay_timeout, self.unschedule)

    def hide(self):
        if self.win:
            self.label.forget()
            self.win.destroy()
            self.win = None
            self.currItem = ""

    def get_indentlvl(self, item_id: str) -> int:
        """
        Gets the indentation level of a treeview item,
        1 being the level of indentation of a top-level item
        """
        indent = 1
        cur = item_id
        while cur := self.tree.parent(cur):
            indent += 1
        return indent
