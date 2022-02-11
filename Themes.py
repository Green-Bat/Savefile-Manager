from tkinter import *
from tkinter import ttk


class Theme:
    def __init__(self, root):
        self.style = ttk.Style(root)
        self.style.theme_create(
            "Dark",
            parent="clam",
            settings={
                "TCombobox": {
                    "configure": {
                        "selectbackground": "#383636",
                        "fieldbackground": "white",
                        "background": "#383636",
                    }
                },
                "TFrame": {"configure": {"background": "#383636"}},
                "TLabel": {
                    "configure": {"background": "#383636", "foreground": "white"}
                },
                "Treeview": {
                    "configure": {
                        "background": "#212020",
                        "foreground": "white",
                        "font": ("Arial", 9),
                        "fieldbackground": "#212020",
                    },
                    "map": {"background": [("selected", "#4287f5")]},
                },
                "Vertical.TScrollbar": {
                    "configure": {
                        "background": "#212020",
                        "arrowcolor": "white",
                        "troughcolor": "#383636",
                    }
                },
            },
        )

    def SetTheme(self, theme):
        self.style.theme_use(theme)
