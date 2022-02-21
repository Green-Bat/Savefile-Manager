from tkinter import *
from tkinter import ttk


class AddEditWindow(Toplevel):
    def __init__(self, root: Tk, callback, ok_callback):
        super().__init__()
        self.style = ttk.Style(self)
        self.style.configure("Edit.TButton", font=("Arial", 10), width=7)
        self.resizable(False, False)

        coords = root.geometry().split("+")
        w, h = list(map(int, coords[0].split("x")))
        coords.pop(0)
        x, y = list(map(int, coords))
        self.geometry(f"350x300+{x+((w//2)-175)}+{y+((h//2)-150)}")
        self.grid_columnconfigure((0, 1), weight=1)

        ttk.Label(self, text="Profile name: ").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_profile = ttk.Entry(self, state="readonly", width=40)
        self.entry_profile.grid(
            row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w"
        )
        ttk.Label(self, text="Personal saves folder: ").grid(
            row=2, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_p = ttk.Entry(self, state="readonly", width=40)
        self.entry_p.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        ttk.Label(self, text="Game's saves folder: ").grid(
            row=4, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_g = ttk.Entry(self, state="readonly", width=40)
        self.entry_g.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        ttk.Label(self, text="File extentsion: ").grid(
            row=6, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_ext = ttk.Entry(self, state="readonly", width=40)
        self.entry_ext.grid(row=7, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        ttk.Button(
            self,
            text="Choose",
            style="Edit.TButton",
            command=lambda: callback(0, self),
        ).grid(row=1, column=3, padx=5, pady=5, sticky="e")
        ttk.Button(
            self,
            text="Choose",
            style="Edit.TButton",
            command=lambda: callback(1, self),
        ).grid(row=3, column=3, padx=5, pady=5, sticky="e")
        ttk.Button(
            self,
            text="Choose",
            style="Edit.TButton",
            command=lambda: callback(2, self),
        ).grid(row=5, column=3, padx=5, pady=5, sticky="e")
        ttk.Button(
            self,
            text="Choose",
            style="Edit.TButton",
            command=lambda: callback(3, self),
        ).grid(row=7, column=3, padx=5, pady=5, sticky="e")

        ttk.Button(self, text="OK", style="Edit.TButton", command=ok_callback).grid(
            row=8, column=0, padx=5, pady=5
        )
        ttk.Button(
            self, text="Cancel", style="Edit.TButton", command=self.destroy
        ).grid(row=8, column=1, padx=5, pady=5)
