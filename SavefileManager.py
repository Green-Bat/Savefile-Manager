# Tkinter modules
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from tkinter.simpledialog import askstring

# from ttkthemes import ThemedStyle

# general modules
import json
from datetime import datetime, time, timedelta
import shutil
from pathlib import Path
import logging
from natsort import os_sorted


class SavefileManager:
    def __init__(self, root: Tk):

        self.fileCount = 0
        # load settings json
        configPath = Path(__file__).parent.resolve() / "config"
        self.settingsPath = configPath / "settings.json"
        self.logpath = configPath / "log.log"

        if not configPath.exists():
            configPath.mkdir()

        # setup logging
        fmt = "%(levelname)s %(asctime)s %(message)s"
        logging.basicConfig(
            filename=self.logpath, filemode="w", level=logging.DEBUG, format=fmt
        )
        # if json file isn't there for wahtever reason
        # create a new one
        if self.settingsPath.exists():
            with self.settingsPath.open() as f:
                self.settings = json.load(f)
            logging.info("Successful settings file load")
        else:
            self.settings = {
                "CurrFilesP": {},
                "CurrFilesG": {},
                "CurrProfile": [],
                "Profiles": {},
                "Xcoord": 0,
                "Ycoord": 0,
            }
            try:
                with self.settingsPath.open("w") as f:
                    json.dump(self.settings, f, indent=4)
                logging.info("Settings file successfully generated")
            except OSError as e:
                logging.error(f"Couldn't generate settings file {e.strerror}")
                messagebox.showerror(
                    "ERROR", "Couldn't make settings file. Check config\\log.log"
                )
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # -------------------- GUI INIT  -------------------------
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # keep a refrence of the base window
        self._root = root
        # styling
        # self.style = ThemedStyle(self._root)
        # self.style.theme_use("black")

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.title("Savefile Manager")
        root.resizable(False, False)
        self.geo = ("480", "480")
        root.geometry(
            f"{'x'.join(self.geo)}+{self.settings['Xcoord']}+{self.settings['Ycoord']}"
        )

        # -------------------- HEADER FRAME --------------------
        self.frame_header = ttk.Frame(root, width=self.geo[0], height=100)
        self.frame_header.pack()
        self.frame_header.grid_propagate(False)
        self.frame_header.columnconfigure(0, weight=1)
        self.frame_header.columnconfigure(1, weight=1)

        # MENUBAR
        root.option_add("*tearOff", False)
        self.menubar = Menu(self.frame_header)
        root.config(menu=self.menubar)
        self.options = Menu(self.menubar)
        self.options.add_command(label="Add", command=self.AddProfile)
        self.options.add_command(label="Edit", command=self.EditProfile)
        self.options.add_command(label="Remove", command=self.RemoveProfile)
        self.menubar.add_cascade(menu=self.options, label="Options")

        # DropDownList
        ttk.Label(self.frame_header, text="Savefile Manager").grid(
            row=0, column=0, sticky="ew"
        )

        self.ddlOpt = [x for x in self.settings["Profiles"].keys()]
        self.DDL = ttk.Combobox(
            self.frame_header, values=self.ddlOpt, height=6, width=20
        )

        if self.settings["CurrProfile"]:
            self.DDL.set(self.settings["CurrProfile"][0])
        self.DDL.state(["readonly"])
        self.DDL.bind("<<ComboboxSelected>>", self.updateDDL)
        self.DDL.bind("<<FocusOut>>", lambda e: self.DDL.selection_clear(0, END))
        self.DDL.grid(row=0, column=1, sticky="e", padx=5)

        # Path Labels
        label_p = (
            self.settings["CurrProfile"][1] if len(self.settings["CurrProfile"]) else ""
        )
        label_g = (
            self.settings["CurrProfile"][2] if len(self.settings["CurrProfile"]) else ""
        )
        self.PathLabel_g = ttk.Label(
            self.frame_header,
            text="Current game directory: " + label_g,
            wraplength=self.geo[0],
        )
        self.PathLabel_p = ttk.Label(
            self.frame_header,
            text="Current personal directory: " + label_p,
            wraplength=self.geo[0],
        )
        self.PathLabel_p.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        self.PathLabel_g.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)
        # -------------------- END OF HEADER FRAME --------------------

        # -------------------- BODY FRAME --------------------
        self.frame_body = ttk.Frame(self._root, width=self.geo[0])
        self.frame_body.pack(fill="x")
        self.frame_body.columnconfigure(1, weight=1)
        self.frame_body.rowconfigure((0, 1), weight=1)

        # Treeview
        self.treeview_p = ttk.Treeview(
            self.frame_body, selectmode="browse", height=15, show="tree"
        )
        self.treeview_g = ttk.Treeview(
            self.frame_body, selectmode="browse", height=10, show="tree"
        )

        # Treeview buttons
        # ------------- BUTTON SUB-FRAME -------------
        self.frame_button = ttk.Frame(self.frame_body)
        self.frame_button.grid(row=0, column=1)
        self.button_replace = Button(
            self.frame_button,
            bg="black",
            foreground="white",
            text="=>",
            command=self.Replace,
            height=2,
        )
        self.button_backup = Button(
            self.frame_button,
            bg="black",
            foreground="white",
            text="<=",
            command=self.Backup,
            height=2,
        )
        self.button_replace.grid(row=0, column=0, sticky="ns", pady=5)
        self.button_backup.grid(row=1, column=0, sticky="ns", pady=5)
        # ------------- END OF BUTTON SUB-FRAME -------------
        self.treeview_p.grid(row=0, rowspan=2, column=0, sticky="w", padx=5, pady=5)
        self.treeview_g.grid(row=0, rowspan=2, column=2, sticky="ne", padx=5, pady=5)
        # -------------------- END OF BODY FRAME --------------------
        # Fill tree
        if self.settings["CurrProfile"]:
            self.UpdateTree(init=True)
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # ---------------------- END OF INIT ---------------------
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def UpdateTree(self, init=False, tree: str = "Both"):
        """
        Initializes the treeviews and handles
        any updates when switching between profiles
        """
        # If initializing gui don't delete since tree already empty
        if not init:
            if tree == "P" or tree == "Both":
                for child in self.treeview_p.get_children():
                    self.treeview_p.delete(child)
            if tree == "G" or tree == "Both":
                print("here")
                for child in self.treeview_g.get_children():
                    self.treeview_g.delete(child)

        # Add subfolders for the personal directory
        if tree == "P" or tree == "Both":
            p = Path(self.settings["CurrProfile"][1])
            self.AddSubfolders(p)
            # Add the rest of the files
            for file in os_sorted(p.glob(f"*{self.settings['CurrProfile'][3]}")):
                self.treeview_p.insert("", "end", file.name, text=file.name)
                self.settings["CurrFilesP"][file.name] = str(file)
        # Add the files in the game's directory
        if tree == "G" or tree == "Both":
            g = Path(self.settings["CurrProfile"][2])
            for file in os_sorted(g.glob(f"*{self.settings['CurrProfile'][3]}")):
                self.treeview_g.insert("", "end", file.name, text=file.name)
                self.settings["CurrFilesG"][file.name] = str(file)

    # Recursively add files and subfolders for personal directory
    def AddSubfolders(self, path: Path, Parent=""):
        """
        Recursively adds subfolders in the personal directory
        to the treeview and adds all the save files in them
        """
        for folder in path.iterdir():
            if folder.is_dir():
                Parentiid = self.treeview_p.insert(
                    Parent, "end", Parent + folder.name, text=folder.name
                )
                self.settings["CurrFilesP"][Parentiid] = str(folder)
                self.AddSubfolders(folder, Parent=Parentiid)
                # fmt:off
                for file in os_sorted(folder.glob(f"*{self.settings['CurrProfile'][3]}")):
                # fmt:on
                    Parentiid2 = self.treeview_p.insert(
                        Parentiid, "end", Parentiid + file.name, text=file.name
                    )
                    self.settings["CurrFilesP"][Parentiid2] = str(file)

    def updateDDL(self, event: Event):
        """
        Updates treeviews and settings json
        when changing combobox option
        """
        self._root.focus_set()
        self.settings["CurrProfile"] = self.settings["Profiles"][self.DDL.get()]
        self.UpdateTree()
        print(f"{event}")
        print(self.DDL.get())
        self.Save()

    def AddProfile(self):
        """
        Ask user to add a profile by asking for two directories,
        a personal one and the game's save folder,
        a profile name, and a file extension, then save it
        """
        # Ask for folders
        dir_p = dir_g = ""
        while True:
            dir_p = filedialog.askdirectory(
                initialdir=self.settings["CurrProfile"][1],
                title="Please choose your OWN personal directory",
            )
            if not dir_p:
                return
            dir_g = filedialog.askdirectory(
                initialdir=self.settings["CurrProfile"][2],
                title="Please choose the GAME'S directory",
            )
            if not dir_g:
                return
            if dir_p == dir_g:
                messagebox.showwarning(
                    "Warning: Same folder", "The two directories cannot be the same"
                )
                logging.warning("Same folder chosen")
                continue
            else:
                break
        # Ask for a profile name
        while True:
            newProf = askstring("Profile name", "Choose a name for your new profile")
            # pressing cancel returns None so
            # distinguishing None vs an empty string here is important
            if newProf is None:
                return
            # pressing ok on an empty inputbox returns an empty string
            elif not newProf:
                messagebox.showwarning("No name", "Profile must have a name")
                logging.warning("No profile name")
                continue
            elif newProf in self.DDL["values"]:
                messagebox.showwarning(
                    "Profile already exists",
                    f"'{newProf}' already exists please chose another name",
                )
                logging.warning("Profile name already exists")
                continue
            else:
                break
        # Ask for the file extension
        while True:
            ext = askstring("Extenstion", "Enter the savefiles' extension")
            if ext is None:
                return
            elif not ext:
                messagebox.showwarning("No name", "Must choose a file extentsion")
                continue
            else:
                break
        if not ext.startswith("."):
            ext = "." + ext
        self.ddlOpt.append(newProf)
        self.ddlOpt.sort()
        self.DDL["values"] = self.ddlOpt
        self.DDL.set(newProf)
        self.settings["Profiles"][newProf] = [newProf, dir_p, dir_g, ext]
        self.DDL.event_generate("<<ComboboxSelected>>")
        self.Save()

    def EditProfile(self):
        pass

    def RemoveProfile(self):
        self.settings["Profiles"].pop(self.DDL.get())
        self.ddlOpt = [x for x in self.settings["Profiles"].keys()]
        self.ddlOpt.sort()
        self.DDL["values"] = self.ddlOpt 
        self.DDL.set(list(self.settings["Profiles"])[0])
        self.DDL.event_generate("<<ComboboxSelected>>")

    def Replace(self):
        pass

    def Backup(self):
        pass

    def Save(self):
        try:
            with open(self.settingsPath, "w") as f:
                json.dump(self.settings, f, indent=4)
        except OSError as e:
            messagebox.showerror(
                "Settings file error", "Couldn't save settings check log.log"
            )
            logging.error(f"Couldn't save settings {e.strerror}")

    def on_close(self):
        print("Closing")
        self.Save()
        self._root.destroy()


# for testing
def main():
    root = Tk()
    savefileManager = SavefileManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
