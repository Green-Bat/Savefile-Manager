from tkinter import *
from tkinter import ttk


class AddEditWindow:
    def __init__(self, root: Tk, callback, ok_callback):
        self.tp = Toplevel(root)
        self.style = ttk.Style(self.tp)
        self.style.configure("Edit.TButton", font=("Arial", 10), width=7)
        self.tp.resizable(False, False)

        coords = root.geometry().split("+")
        w, h = list(map(int, coords[0].split("x")))
        coords.pop(0)
        x, y = list(map(int, coords))
        self.tp.geometry(f"350x300+{x+((w//2)-175)}+{y+((h//2)-150)}")
        self.tp.grid_columnconfigure((0, 1), weight=1)

        ttk.Label(self.tp, text="Profile name: ").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_profile = ttk.Entry(self.tp, state="readonly", width=40)
        self.entry_profile.grid(
            row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w"
        )
        ttk.Label(self.tp, text="Personal saves folder: ").grid(
            row=2, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_p = ttk.Entry(self.tp, state="readonly", width=40)
        self.entry_p.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        ttk.Label(self.tp, text="Game's saves folder: ").grid(
            row=4, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_g = ttk.Entry(self.tp, state="readonly", width=40)
        self.entry_g.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        ttk.Label(self.tp, text="File extentsion: ").grid(
            row=6, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_ext = ttk.Entry(self.tp, state="readonly", width=40)
        self.entry_ext.grid(row=7, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        ttk.Button(
            self.tp, text="Choose", style="Edit.TButton", command=lambda: callback(0)
        ).grid(row=1, column=3, padx=5, pady=5, sticky="e")
        ttk.Button(
            self.tp, text="Choose", style="Edit.TButton", command=lambda: callback(1)
        ).grid(row=3, column=3, padx=5, pady=5, sticky="e")
        ttk.Button(
            self.tp, text="Choose", style="Edit.TButton", command=lambda: callback(2)
        ).grid(row=5, column=3, padx=5, pady=5, sticky="e")
        ttk.Button(
            self.tp, text="Choose", style="Edit.TButton", command=lambda: callback(3)
        ).grid(row=7, column=3, padx=5, pady=5, sticky="e")

        ttk.Button(self.tp, text="OK", style="Edit.TButton", command=ok_callback).grid(
            row=8, column=0, padx=5, pady=5
        )
        ttk.Button(
            self.tp, text="Cancel", style="Edit.TButton", command=self.tp.destroy
        ).grid(row=8, column=1, padx=5, pady=5)
