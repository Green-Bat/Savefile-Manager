from tkinter import ttk, Widget, Tk


class Theme:
    def __init__(self, root: Tk):
        self.root = root
        self.style = ttk.Style(root)
        self.style.theme_settings(
            "vista",
            settings={
                "TButton": {
                    "configure": {
                        "width": 4,
                        "font": ("Arial", 10),
                        "anchor": "center",
                    }
                },
                "Treeview": {"configure": {"indent": 10}},
            },
        )
        self.themes = {
            # font, background1, background2, foreground/text color, treeview selection
            "Dark": [("Arial", 9), "#212020", "#1f1f1f", "white", "#4287f5"],
            "Dark (Alt)": [("Arial", 9), "#212020", "#1f1f1f", "white", "#4287f5"],
            "vista": [(), "#f0f0f0", "#f0f0f0", "black"],
            "Classic": [(), "#f0f0f0", "#f0f0f0", "black"],
            "Solarized": [("Arial", 9), "#002b36", "#073642", "white", "#586e75"],
        }
        self.style.theme_create(
            "Dark",
            parent="clam",
            settings={
                "Tk": {"configure": {"background": self.themes["Dark"][2]}},
                "TButton": {
                    "configure": {
                        "background": self.themes["Dark"][1],
                        "foreground": self.themes["Dark"][3],
                        "font": ("Courier", 14),
                        "relief": "raised",
                        "shiftrelief": 2,
                        "width": 2,
                        "anchor": "center",
                    },
                    "map": {"relief": [("pressed", "solid")]},
                },
                "TCombobox": {
                    "configure": {
                        "background": self.themes["Dark"][2],
                        "arrowcolor": self.themes["Dark"][3],
                        "selectbackground": "white",
                        "selectforeground": "black",
                    }
                },
                "TFrame": {"configure": {"background": self.themes["Dark"][2]}},
                "TLabel": {
                    "configure": {
                        "background": self.themes["Dark"][2],
                        "foreground": self.themes["Dark"][3],
                    }
                },
                "Treeview": {
                    "configure": {
                        "background": self.themes["Dark"][1],
                        "foreground": self.themes["Dark"][3],
                        "font": self.themes["Dark"][0],
                        "fieldbackground": self.themes["Dark"][1],
                        "indent": 10,
                    },
                    "map": {"background": [("selected", self.themes["Dark"][4])]},
                },
                "Treeview.Item": {"configure": {"indicatormargins": 5}},
                "Vertical.TScrollbar": {
                    "configure": {
                        "background": self.themes["Dark"][1],
                        "arrowcolor": self.themes["Dark"][3],
                        "troughcolor": self.themes["Dark"][2],
                        "gripcount": 0,
                    }
                },
                "TRadiobutton": {"configure": {"indicatorcolor": "white"}},
            },
        )
        self.style.theme_create(
            "Dark (Alt)",
            parent="alt",
            settings={
                "Tk": {"configure": {"background": self.themes["Dark"][2]}},
                "TButton": {
                    "configure": {
                        "background": self.themes["Dark"][1],
                        "foreground": self.themes["Dark"][3],
                        "font": ("Courier", 14),
                        "relief": "raised",
                        "shiftrelief": 2,
                        "width": 2,
                        "anchor": "center",
                    },
                    "map": {"relief": [("pressed", "solid")]},
                },
                "TCombobox": {
                    "configure": {
                        "background": self.themes["Dark"][2],
                        "arrowcolor": self.themes["Dark"][3],
                        "selectbackground": "white",
                        "selectforeground": "black",
                    }
                },
                "TFrame": {"configure": {"background": self.themes["Dark"][2]}},
                "TLabel": {
                    "configure": {
                        "background": self.themes["Dark"][2],
                        "foreground": self.themes["Dark"][3],
                    }
                },
                "Treeview": {
                    "configure": {
                        "background": self.themes["Dark"][1],
                        "foreground": self.themes["Dark"][3],
                        "font": self.themes["Dark"][0],
                        "fieldbackground": self.themes["Dark"][1],
                        "indent": 10,
                    },
                    "map": {"background": [("selected", self.themes["Dark"][4])]},
                },
                "Treeview.Item": {"configure": {"indicatormargins": 5}},
                "Vertical.TScrollbar": {
                    "configure": {
                        "background": self.themes["Dark"][1],
                        "arrowcolor": self.themes["Dark"][3],
                        "troughcolor": self.themes["Dark"][2],
                    }
                },
                "TRadiobutton": {"configure": {"indicatorcolor": "white"}},
            },
        )
        self.style.theme_create(
            "Solarized",
            parent="default",
            settings={
                "Tk": {"configure": {"background": self.themes["Solarized"][2]}},
                "TButton": {
                    "configure": {
                        "background": self.themes["Solarized"][1],
                        "foreground": self.themes["Solarized"][3],
                        "font": ("Courier", 14),
                        "relief": "raised",
                        "shiftrelief": 2,
                        "width": 2,
                        "anchor": "center",
                    },
                    "map": {"relief": [("pressed", "solid")]},
                },
                "TCombobox": {
                    "configure": {
                        "background": self.themes["Solarized"][2],
                        "arrowcolor": self.themes["Solarized"][3],
                        "selectbackground": "white",
                        "selectforeground": "black",
                    }
                },
                "TFrame": {"configure": {"background": self.themes["Solarized"][2]}},
                "TLabel": {
                    "configure": {
                        "background": self.themes["Solarized"][2],
                        "foreground": self.themes["Solarized"][3],
                    }
                },
                "Treeview": {
                    "configure": {
                        "background": self.themes["Solarized"][1],
                        "foreground": self.themes["Solarized"][3],
                        "font": self.themes["Solarized"][0],
                        "fieldbackground": self.themes["Solarized"][1],
                        "indent": 10,
                    },
                    "map": {"background": [("selected", self.themes["Solarized"][4])]},
                },
                "Treeview.Item": {"configure": {"indicatormargins": 5}},
                "Vertical.TScrollbar": {
                    "configure": {
                        "background": self.themes["Solarized"][1],
                        "arrowcolor": self.themes["Solarized"][3],
                        "troughcolor": self.themes["Solarized"][2],
                    }
                },
            },
        )

    def SetTheme(self, theme, *widgets: Widget):
        if theme == "Classic":
            theme = "vista"
        if theme in self.themes:
            for widget in widgets:
                widget.configure(
                    background=self.themes[theme][1],
                    foreground=self.themes[theme][3],
                )
            self.style.theme_use(theme)
