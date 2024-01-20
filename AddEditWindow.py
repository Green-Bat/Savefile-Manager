from logging import warning
from collections.abc import Callable
from tkinter import Tk, Toplevel, ttk, filedialog, messagebox, END
from tkinter.simpledialog import askstring
from Helpers import GetExt
from pathlib import Path


class AddEditWindow(Toplevel):
    def __init__(
        self,
        root: Tk,
        currProfile: list[str],
        ok_callback: Callable[["AddEditWindow"], None],
        title: str = None,
    ):
        super().__init__(root)
        root.wm_attributes("-disabled", True)
        self.wm_protocol("WM_DELETE_WINDOW", self.on_close)
        self.root = root
        self.style = ttk.Style(self)
        self.style.configure("Edit.TButton", font=("Arial", 10), width=7)
        self.configure(bg=self.style.lookup("Tk", "background"))
        self.resizable(False, False)
        self.wm_title(title)

        self.profile_added = False
        self.profile_updated = False
        self.currProfile = currProfile
        # get coords and dimensions of root window
        coords = root.geometry().split("+")
        w, h = list(map(int, coords[0].split("x")))
        coords.pop(0)
        x, y = list(map(int, coords))

        # set the geometry of window to half that of root
        # and spawn it centered with it
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

        self.button_profile = ttk.Button(
            self,
            text="Choose",
            style="Edit.TButton",
            command=lambda: self.Choose(0),
        )
        self.button_personal_folder = ttk.Button(
            self,
            text="Choose",
            style="Edit.TButton",
            command=lambda: self.Choose(1),
        )
        self.button_game_folder = ttk.Button(
            self,
            text="Choose",
            style="Edit.TButton",
            command=lambda: self.Choose(2),
        )
        self.button_extension = ttk.Button(
            self,
            text="Choose",
            style="Edit.TButton",
            command=lambda: self.Choose(3),
        )
        self.button_profile.grid(row=1, column=3, padx=5, pady=5, sticky="e")
        self.button_personal_folder.grid(row=3, column=3, padx=5, pady=5, sticky="e")
        self.button_game_folder.grid(row=5, column=3, padx=5, pady=5, sticky="e")
        self.button_extension.grid(row=7, column=3, padx=5, pady=5, sticky="e")

        ttk.Button(
            self,
            text="OK",
            style="Edit.TButton",
            command=lambda: ok_callback(self),
        ).grid(row=8, column=0, padx=5, pady=5)

        ttk.Button(self, text="Cancel", style="Edit.TButton", command=self.cancel).grid(
            row=8, column=1, padx=5, pady=5
        )
        self.focus_force()
        self.grab_set()
        # self.wait_window()

    def cancel(self):
        self.profile_added = False
        self.profile_updated = False
        self.on_close()

    def Choose(self, index: int):
        if index == 0:
            while True:
                new = askstring(
                    "Profile Name",
                    "Choose a profile name",
                    parent=self,
                    initialvalue=self.entry_profile.get(),
                )
                if new == "Add...":
                    warning(f"Invalid name choice '{new}'")
                    messagebox.showwarning(
                        "Invalid Name", "Please choose another profile name"
                    )
                    continue
                else:
                    break
            if new:
                self.entry_profile.state(["!readonly"])
                self.entry_profile.delete(0, END)
                self.entry_profile.insert(0, new)
                self.entry_profile.state(["readonly"])
        elif index == 1:
            startDir = self.currProfile[index] if self.currProfile else ""
            new = filedialog.askdirectory(
                initialdir=startDir,
                parent=self,
                title="Choose your OWN personal saves folder",
            )
            if new:
                self.entry_p.state(["!readonly"])
                self.entry_p.delete(0, END)
                self.entry_p.insert(0, new)
                self.entry_p.state(["readonly"])
        elif index == 2:
            startDir = self.currProfile[index] if self.currProfile else ""
            new = filedialog.askdirectory(
                initialdir=startDir,
                parent=self,
                title="Choose the GAME'S  saves folder",
            )
            if new:
                self.entry_g.state(["!readonly"])
                self.entry_g.delete(0, END)
                self.entry_g.insert(0, new)
                self.entry_g.state(["readonly"])
        elif index == 3:
            new = askstring(
                "File Extension",
                "Enter the file extension of the savefiles e.g. .sgd,.save,...\n For files with no extension use '*'",
                parent=self,
            )
            if new:
                if new == "*":
                    new = ""
                elif not new.startswith(".") and len(new) >= 1:
                    new = "." + new
                self.entry_ext.state(["!readonly"])
                self.entry_ext.delete(0, END)
                self.entry_ext.insert(0, new)
                self.entry_ext.state(["readonly"])
        if not new:
            self.grab_set()
            self.wait_window()
            return
        if not self.entry_ext.get() and (index == 1 or index == 2):
            self.entry_ext.state(["!readonly"])
            self.entry_ext.delete(0, END)
            self.entry_ext.insert(0, GetExt(Path(new)))
            self.entry_ext.state(["readonly"])
        self.grab_set()
        self.wait_window()

    def on_close(self):
        self.root.wm_attributes("-disabled", False)
        self.root.focus_set()
        self.destroy()
