# Tkinter modules
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from tkinter.simpledialog import askstring

# from ttkthemes import ThemedStyle

# general modules
import json
from datetime import datetime, timedelta
import shutil
from os import startfile
from pathlib import Path
import logging
from natsort import os_sorted, natsorted

# my modules
from Theme import Theme
from AddEditWindow import AddEditWindow
from TreeviewToolTip import TVToolTip
import Helpers

# TODO:
# -[] Add support for files with no extension
# -[] Keep subfolders open after tree auto-update
# -[/] Tooltips
# -[] Resizing
# -[] Auto convert for arkham?
# -[] Center message boxes


class SavefileManager:
    def __init__(self, root: Tk):

        self.fileCount = 0
        # load settings json
        self.configPath = Path().resolve() / "config"
        self.settingsPath = self.configPath / "settings.json"
        self.logpath = self.configPath / "log.log"
        self.bak = self.configPath / "backups"
        self.bakDeleted = self.configPath / "backups/Deleted"
        # create any directories if they are missing
        self.configPath.mkdir(exist_ok=True)
        self.bak.mkdir(exist_ok=True)
        self.bakDeleted.mkdir(exist_ok=True)

        # if json file isn't there for wahtever reason
        # create a new one
        self.settings = {
            "CurrFilesP": {},
            "CurrFilesG": {},
            "CurrProfile": [],
            "Profiles": {},
            "Xcoord": 0,
            "Ycoord": 0,
            "Theme": "",
            "ProfileCount": 0,
            "LogTime": str(datetime.now()),
        }
        # log format
        fmt = "%(levelname)s %(asctime)s %(message)s"
        try:
            with self.settingsPath.open("r") as f:
                settings = json.load(f)
            # initialize settings with default values if they are missing
            for key, val in self.settings.items():
                if key not in settings:
                    settings[key] = val
            # make sure settings don't have extra/unwanted values
            for key in list(settings.keys()):
                if key not in self.settings:
                    del settings[key]
            self.settings = settings
            self.settings["ProfileCount"] = len(self.settings["Profiles"])
            # setup logging
            # purge the log file and backups every week
            weekAgo = (
                datetime.now()
                - datetime.strptime(self.settings["LogTime"], "%Y-%m-%d %H:%M:%S.%f")
            ) > timedelta(weeks=1)
            logging.basicConfig(
                filename=self.logpath,
                filemode="w" if weekAgo else "a",
                level=logging.DEBUG,
                format=fmt,
            )
            if weekAgo:
                self.settings["LogTime"] = str(datetime.now())
                for file in self.bak.iterdir():
                    if file.is_file():
                        file.unlink()
                for file in self.bakDeleted.iterdir():
                    if file.is_file():
                        file.unlink()
            logging.info("Settings file successfully loaded")
        except (FileNotFoundError, json.JSONDecodeError):
            logging.basicConfig(filename=self.logpath, level=logging.DEBUG, format=fmt)
            logging.error("Settings file missing/corrupt")
            try:
                with self.settingsPath.open("w") as f:
                    json.dump(self.settings, f, indent=4)
                logging.info("Settings file successfully generated")
            except OSError as e:
                logging.error(f"Couldn't generate settings file {e.strerror}")
                messagebox.showerror("ERROR", "Couldn't make settings file.")
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # -------------------- GUI INIT  -------------------------
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # keep a refrence of the base window
        self._root = root
        self._root.iconbitmap(
            default=Path().resolve() / "images/Savefile Replacer Icon.ico"
        )
        self.theme = Theme(self._root)

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.title("Savefile Manager")
        root.resizable(False, False)
        root.minsize(490, 485)
        self.geo = ("490", "485")

        if self.settings["Xcoord"] + 490 > root.winfo_screenwidth():
            self.settings["Xcoord"] = root.winfo_screenwidth() - 490

        if self.settings["Ycoord"] + 485 > root.winfo_screenheight():
            self.settings["Ycoord"] = root.winfo_screenheight() - 485

        geo = "x".join(self.geo)
        # print(f"{geo}+{self.settings['Xcoord']}+{self.settings['Ycoord']}")
        root.geometry(f"{geo}+{self.settings['Xcoord']}+{self.settings['Ycoord']}")

        # -------------------- HEADER FRAME --------------------
        self.frame_header = ttk.Frame(root, width=self.geo[0], height=100)
        self.frame_header.pack(expand=True, fill=BOTH)
        self.frame_header.grid_propagate(False)
        self.frame_header.grid_columnconfigure((0, 1), weight=1)
        self.frame_header.grid_rowconfigure((0, 3), weight=1)

        # MENUBAR
        root.option_add("*tearOff", False)
        self.menubar = Menu(self.frame_header)
        root.config(menu=self.menubar)
        self.options = Menu(self.menubar)
        self.options.add_command(label="Add", command=self.AddProfile)
        self.options.add_command(label="Edit", command=self.EditProfile)
        self.options.add_command(label="Remove", command=self.RemoveProfile)
        # String var for the theme
        self.currTheme = StringVar()
        self.themesMenu = Menu(self.menubar)
        self.themesMenu.add_radiobutton(
            label="Dark",
            variable=self.currTheme,
            selectcolor="white",
        )
        self.themesMenu.add_radiobutton(
            label="Dark (Alt)",
            variable=self.currTheme,
            selectcolor="white",
        )
        self.themesMenu.add_radiobutton(label="Classic", variable=self.currTheme)
        self.themesMenu.add_radiobutton(
            label="Solarized",
            variable=self.currTheme,
            selectcolor="#93a1a1",
        )
        self.menubar.add_cascade(menu=self.options, label="Options")
        self.menubar.add_cascade(menu=self.themesMenu, label="Themes")

        # Whenever the string var changes change the theme
        self.currTheme.trace_add(
            "write",
            callback=lambda var, index, mode: self.theme.SetTheme(
                self.currTheme.get(),
                self.options,
                self.themesMenu,
                self.treeMenu_g,
                self.treeMenu_p,
            ),
        )

        # DropDownList
        ttk.Label(
            self.frame_header,
            text="Savefile Manager",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=0, sticky="ew")

        self.ddlOpt = [x for x in self.settings["Profiles"].keys()]
        self.ddlOpt = natsorted(self.ddlOpt)
        self.ddlOpt.append("Add...")
        self.DDL = ttk.Combobox(
            self.frame_header,
            values=self.ddlOpt,
            height=6,
            width=20,
        )

        if self.settings["CurrProfile"]:
            self.DDL.set(self.settings["CurrProfile"][0])
        self.DDL.state(["readonly"])
        self.DDL.bind("<<ComboboxSelected>>", self.updateDDL)
        self.DDL.bind("<<FocusOut>>", lambda e: self.DDL.selection_clear(0, END))
        self.DDL.grid(row=0, column=1, sticky="e", padx=5, pady=2)

        # Path Labels
        label_p = (
            self.settings["CurrProfile"][1] if self.settings["CurrProfile"] else ""
        )
        label_g = (
            self.settings["CurrProfile"][2] if self.settings["CurrProfile"] else ""
        )
        self.PathLabel_p = ttk.Label(
            self.frame_header,
            text="Current personal directory: " + label_p,
            wraplength=self.geo[0],
        )
        self.PathLabel_g = ttk.Label(
            self.frame_header,
            text="Current game directory: " + label_g,
            wraplength=int(self.geo[0]),
        )
        # double clicking the paths will open the folder in file explorer
        self.PathLabel_p.bind(
            "<Double-Button-1>",
            lambda e: startfile(self.settings["CurrProfile"][1]),
        )
        self.PathLabel_g.bind(
            "<Double-Button-1>",
            lambda e: startfile(self.settings["CurrProfile"][2]),
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
        from PIL import Image, ImageTk

        # Add icons for files and folders
        self.fileIco = ImageTk.PhotoImage(
            Image.open("images/ico1.ico").resize((20, 20), Image.ANTIALIAS)
        )
        self.folderIco = ImageTk.PhotoImage(
            Image.open("images/ico4.ico").resize((22, 22), Image.ANTIALIAS)
        )
        self.treeview_p = ttk.Treeview(
            self.frame_body, selectmode="browse", height=17, show="tree"
        )
        self.treeview_g = ttk.Treeview(
            self.frame_body, selectmode="browse", height=10, show="tree"
        )
        # Add scrollbar
        self.yscroll = ttk.Scrollbar(
            self.frame_body, orient=VERTICAL, command=self.treeview_p.yview
        )
        self.treeview_p.config(yscrollcommand=self.yscroll.set)
        self.yscroll.grid(row=0, rowspan=2, column=0, sticky="nse", pady=5, padx=5)
        # Treeview buttons
        # ------------- BUTTON SUB-FRAME -------------
        self.frame_button = ttk.Frame(self.frame_body)
        self.frame_button.grid(row=0, column=1)
        self.button_replace = ttk.Button(
            self.frame_button, text="=>", command=self.Replace
        )
        self.button_backup = ttk.Button(
            self.frame_button, text="<=", command=self.Backup
        )
        self.button_replace.grid(row=0, column=0, sticky="ns", pady=5)
        self.button_backup.grid(row=1, column=0, sticky="ns", pady=5)
        # ------------- END OF BUTTON SUB-FRAME -------------
        self.treeview_p.grid(row=0, rowspan=2, column=0, sticky="w", padx=5, pady=5)
        self.treeview_g.grid(row=0, rowspan=2, column=2, sticky="ne", padx=5, pady=5)

        self.treeMenu_g = Menu()
        self.treeMenu_g.add_command(
            label="Rename", command=lambda: self.TreeviewRename("G", self.treeview_g)
        )
        self.treeMenu_g.add_command(
            label="Delete", command=lambda: self.TreeviewDelete("G")
        )
        self.treeMenu_p = Menu()
        self.treeMenu_p.add_command(
            label="Rename", command=lambda: self.TreeviewRename("P", self.treeview_p)
        )
        self.treeMenu_p.add_command(
            label="Delete", command=lambda: self.TreeviewDelete("P")
        )
        self.treeview_g.bind("<Button-3>", self.TreeviewMenu)
        self.treeview_p.bind("<Button-3>", self.TreeviewMenu)
        TVToolTip(root, self.treeview_p, self.treeview_g)
        # -------------------- END OF BODY FRAME --------------------
        # Fill tree if there is an exisiting profile
        # otherwise disable the buttons
        if self.settings["CurrProfile"]:
            self.UpdateTree()
        else:
            self.button_backup.state(["disabled"])
            self.button_replace.state(["disabled"])
        root.after(1000, self.FileChecker)
        # Set theme
        if self.settings["Theme"]:
            self.currTheme.set(self.settings["Theme"])
        else:
            self.currTheme.set("Dark")
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # --------------------- END OF INIT ----------------------
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def TreeviewMenu(self, event: Event):
        """Context menu for treeview"""
        bounds_g = (
            self.treeview_g.winfo_rootx(),
            self.treeview_g.winfo_rootx() + self.treeview_g.winfo_width(),
            self.treeview_g.winfo_rooty(),
            self.treeview_g.winfo_rooty() + self.treeview_g.winfo_height(),
        )
        bounds_p = (
            self.treeview_p.winfo_rootx(),
            self.treeview_p.winfo_rootx() + self.treeview_p.winfo_width(),
            self.treeview_p.winfo_rooty(),
            self.treeview_p.winfo_rooty() + self.treeview_p.winfo_height(),
        )
        inTree_g = (
            event.x_root > bounds_g[0]
            and event.x_root < bounds_g[1]
            and event.y_root > bounds_g[2]
            and event.y_root < bounds_g[3]
        )
        inTree_p = (
            event.x_root > bounds_p[0]
            and event.x_root < bounds_p[1]
            and event.y_root > bounds_p[2]
            and event.y_root < bounds_p[3]
        )
        if inTree_g and self.treeview_g.selection():
            self.treeMenu_g.post(event.x_root, event.y_root)
        elif inTree_p and self.treeview_p.selection():
            self.treeMenu_p.post(event.x_root, event.y_root)

    def TreeviewDelete(self, tree: str):
        if not messagebox.askyesno(
            "Deleting file", "Are you sure you want to delete the file?"
        ):
            return
        if tree == "G":
            selection = self.treeview_g.selection()[0]
            removed = Path(self.settings["CurrFilesG"][selection])
            backup = self.bakDeleted / (
                datetime.now().strftime("%Y_%m_%d_%Hhr_%Mmin_%Ss_") + removed.name
            )
            try:
                shutil.copy2(removed, backup)
            except OSError as e:
                logging.error(f"Couldn't copy file {e.strerror}")
                messagebox.showerror("FAILED DELETE ERROR", "Couldn't delete file")
                return
            self.settings["CurrFilesG"].pop(selection)
            self.treeview_g.delete(selection)
            removed.unlink()
        elif tree == "P":
            selection = self.treeview_p.selection()[0]
            removed = Path(self.settings["CurrFilesP"][selection])
            backup = self.bakDeleted / (
                datetime.now().strftime("%Y_%m_%d_%Hhr_%Mmin_%Ss_") + removed.name
            )
            try:
                shutil.copy2(removed, backup)
            except OSError as e:
                logging.error(f"Couldn't copy file {e.strerror}")
                messagebox.showerror("FAILED DELET ERROR", "Couldn't delete file")
                return
            self.settings["CurrFilesP"].pop(selection)
            self.treeview_p.delete(selection)
            removed.unlink()

    def TreeviewRename(self, tree: str, treeview: ttk.Treeview):
        if tree == "G":
            change = messagebox.askyesno(
                "Changing game file name",
                "The game may not recognize the savefile if you rename it.\nAre you sure you want to rename?",
            )
            if not change:
                return

        selection = treeview.selection()[0]
        defaultVal = treeview.item(selection, "text")
        newname = askstring(
            "New name",
            "Enter new name for the file",
            parent=self._root,
            initialvalue=defaultVal,
        )
        if not newname:
            return

        # add file extention to newname if it isn't a folder
        if not newname.endswith(f"{self.settings['CurrProfile'][3]}"):
            if (
                tree == "P"
                and not Path(self.settings["CurrFilesP"][selection]).is_dir()
            ) or tree == "G":
                newname += self.settings["CurrProfile"][3]
        overwrite = True
        if tree == "P":
            toSelect = self.treeview_p.parent(selection) + newname
            renamed = Path(self.settings["CurrFilesP"][selection])
            lowerCaseDict = set(k.lower() for k in self.settings["CurrFilesP"])
            # if selection is a file in a subfolder only check name in that subfolder
            if self.treeview_p.parent(selection):
                exists = toSelect.lower() in lowerCaseDict
            else:
                exists = newname.lower() in lowerCaseDict
            if exists:
                overwrite = messagebox.askyesno(
                    "Already exists",
                    "File name already exists would you like to overwrite it?",
                )
            if overwrite:
                renamed = renamed.replace(renamed.parent / newname)
                self.UpdateTree(tree="P", toSelect_p=toSelect)
        elif tree == "G":
            renamed = Path(self.settings["CurrFilesG"][selection])
            lowerCaseDict = set(k.lower() for k in self.settings["CurrFilesG"])
            if newname.lower() in lowerCaseDict:
                overwrite = messagebox.askyesno(
                    "Already exists",
                    "File name already exists would you like to overwrite it?",
                )
            if overwrite:
                renamed = renamed.replace(renamed.parent / newname)
                self.UpdateTree(tree="G", toSelect_g=newname)
            logging.warning("Game file name changed")

    def UpdateTree(
        self, tree: str = "Both", toSelect_p: str = None, toSelect_g: str = None
    ):
        """
        Initializes the treeviews and handles
        any updates when switching between profiles

        Args:
            init: used when initializing
                prevents deleting of treeview items
                since they wouldn't have any items

            tree: Determines which tree to update.
                Can be ['G', 'P', 'Both']

            toSelect_p: id of item to select after updating left treeview

            toSelect_g: id of item to select after updating right treeview
        """
        if tree == "P" or tree == "Both":
            # Delete treeview items and clear the CurrFiles dicts
            # then repopulate the treeviews
            for child in self.treeview_p.get_children():
                self.treeview_p.delete(child)
            self.settings["CurrFilesP"].clear()
            if self.settings["CurrProfile"]:
                # Add subfolders for the personal directory
                p = Path(self.settings["CurrProfile"][1])
                self.AddSubfolders(p)
                # Add the rest of the files
                for file in os_sorted(p.glob(f"*{self.settings['CurrProfile'][3]}")):
                    # uses file name as tree id
                    self.treeview_p.insert(
                        "", "end", file.name, text=file.name, image=self.fileIco
                    )
                    self.settings["CurrFilesP"][file.name] = str(file)
                if toSelect_p and toSelect_p in self.settings["CurrFilesP"]:
                    self.treeview_p.selection_set(toSelect_p)
                    self.treeview_p.see(toSelect_p)
        if tree == "G" or tree == "Both":
            for child in self.treeview_g.get_children():
                self.treeview_g.delete(child)
            self.settings["CurrFilesG"].clear()
            if self.settings["CurrProfile"]:
                # Add the files in the game's directory
                g = Path(self.settings["CurrProfile"][2])
                for file in os_sorted(g.glob(f"*{self.settings['CurrProfile'][3]}")):
                    self.fileCount += 1
                    self.treeview_g.insert(
                        "", "end", file.name, text=file.name, image=self.fileIco
                    )
                    self.settings["CurrFilesG"][file.name] = str(file)
                if toSelect_g and toSelect_g in self.settings["CurrFilesG"]:
                    self.treeview_g.selection_set(toSelect_g)
                    self.treeview_g.see(toSelect_g)
                    self.treeview_g.focus(toSelect_g)

    def AddSubfolders(self, path: Path, Parent=""):
        """
        Recursively adds subfolders in the personal directory
        to the treeview and adds all the save files in them

        Args:
            path: Path object, originally the personal directory
                then called recursively with its subfolders

            Parent: The id of the parent in the treeview.
                Initially '' which is the root, then it is the id
                of added subfolders to be able to add their subfolders
        """
        for folder in path.iterdir():
            if folder.is_dir():
                # use folder name as tree iid
                # for subfolder use folder name concatenated with subfolder name
                Parentiid = self.treeview_p.insert(
                    Parent,
                    "end",
                    Parent + folder.name,
                    text=folder.name,
                    image=self.folderIco,
                )
                self.settings["CurrFilesP"][Parentiid] = str(folder)
                self.AddSubfolders(folder, Parent=Parentiid)
                # fmt: off
                for file in os_sorted(folder.glob(f"*{self.settings['CurrProfile'][3]}")):
                    Parentiid2 = self.treeview_p.insert(
                        Parentiid, "end", Parentiid + file.name, text=file.name, image=self.fileIco
                    )
                    self.settings["CurrFilesP"][Parentiid2] = str(file)
                # fmt: on

    def updateDDL(self, event: Event):
        """
        Updates treeviews and settings json
        when changing combobox option
        """
        if self.DDL.get() == "Add...":
            if not self.AddProfile():
                self.DDL.set(
                    self.settings["CurrProfile"][0]
                    if self.settings["CurrProfile"]
                    else ""
                )
            return
        # Change current profile
        self.settings["CurrProfile"] = self.settings["Profiles"].get(self.DDL.get(), [])
        # Change path labels
        if self.settings["CurrProfile"]:
            self.PathLabel_p.config(
                text="Current personal directory: " + self.settings["CurrProfile"][1]
            )
            self.PathLabel_g.config(
                text="Current game directory: " + self.settings["CurrProfile"][2]
            )
        else:
            self.PathLabel_p.config(text="Current personal directory: ")
            self.PathLabel_g.config(text="Current game directory: ")
        self.UpdateTree()
        # Save to settings.json
        self.Save()

    def Choose(self, index, win: AddEditWindow):
        if index == 0:
            while True:
                new = askstring(
                    "Profile Name",
                    "Choose a profile name",
                    parent=win,
                    initialvalue=win.entry_profile.get(),
                )
                if new == "Add...":
                    logging.warning(f"Invalid name choice '{new}'")
                    messagebox.showwarning(
                        "Invalid Name", "Please choose another profile name"
                    )
                    continue
                else:
                    break
            if new:
                win.entry_profile.state(["!readonly"])
                win.entry_profile.delete(0, END)
                win.entry_profile.insert(0, new)
                win.entry_profile.state(["readonly"])
        elif index == 1:
            startDir = (
                self.settings["CurrProfile"][index]
                if self.settings["CurrProfile"]
                else ""
            )
            new = filedialog.askdirectory(
                initialdir=startDir,
                parent=win,
                title="Choose your OWN personal saves folder",
            )
            if new:
                win.entry_p.state(["!readonly"])
                win.entry_p.delete(0, END)
                win.entry_p.insert(0, new)
                win.entry_p.state(["readonly"])
        elif index == 2:
            startDir = (
                self.settings["CurrProfile"][index]
                if self.settings["CurrProfile"]
                else ""
            )
            new = filedialog.askdirectory(
                initialdir=startDir,
                parent=win,
                title="Choose the GAME'S  saves folder",
            )
            if new:
                win.entry_g.state(["!readonly"])
                win.entry_g.delete(0, END)
                win.entry_g.insert(0, new)
                win.entry_g.state(["readonly"])
        elif index == 3:
            new = askstring(
                "File Extension",
                "Enter the file extension of the savefiles e.g. .sgd,.save,...",
                parent=win,
            )
            if new:
                if not new.startswith("."):
                    new = "." + new
                win.entry_ext.state(["!readonly"])
                win.entry_ext.delete(0, END)
                win.entry_ext.insert(0, new)
                win.entry_ext.state(["readonly"])
        if not new:
            win.grab_set()
            win.wait_window()
            return
        if not win.entry_ext.get() and (index == 1 or index == 2):
            win.entry_ext.state(["!readonly"])
            win.entry_ext.delete(0, END)
            win.entry_ext.insert(0, Helpers.GetExt(Path(new)))
            win.entry_ext.state(["readonly"])
        win.grab_set()
        win.wait_window()

    def AddProfile(self):
        """
        Asks user to add a profile by asking for two directories,
        a personal one and the game's savefile folder,
        a profile name, and a file extension, then saves it
        """

        def ok_callback():
            dir_p = addWin.entry_p.get()
            dir_g = addWin.entry_g.get()
            ext = addWin.entry_ext.get()
            if not (dir_p and dir_g and ext):
                logging.warning("Incomplete profile warning")
                messagebox.showwarning(
                    "Incomplete Profile",
                    "Please make sure you fill in all the necessary profile information",
                )
                return
            newProf = (
                addWin.entry_profile.get()
                if addWin.entry_profile.get()
                else f"Profile {self.settings['ProfileCount']+1}"
            )
            if newProf in self.settings["Profiles"]:
                logging.warning("Profile name already exists")
                messagebox.showwarning(
                    "Profile Name Exists",
                    "Profile name already exists please choose anothe one",
                )
            self.settings["Profiles"][newProf] = [newProf, dir_p, dir_g, ext]
            self.ddlOpt = [x for x in self.settings["Profiles"].keys()]
            self.ddlOpt = natsorted(self.ddlOpt)
            self.ddlOpt.append("Add...")
            self.DDL["values"] = self.ddlOpt
            self.DDL.set(newProf)
            self.DDL.event_generate("<<ComboboxSelected>>")
            if self.button_replace.instate(["disabled"]):
                self.button_replace.state(["!disabled"])
                self.button_backup.state(["!disabled"])
            self.settings["ProfileCount"] = len(self.settings["Profiles"])
            addWin.on_close()
            return True

        addWin = AddEditWindow(self._root, self.Choose, ok_callback, "Add Profile")
        return False

    def EditProfile(self):
        """
        Allows user to edit the currently selected profile
        """
        if not self.settings["Profiles"]:
            logging.warning("attempt to edit when no profiles exist")
            messagebox.showwarning("No profiles", "No profiles exist. Add one first")
            return

        def ok_callback():
            prof = editwin.entry_profile.get()
            dir_p = editwin.entry_p.get()
            dir_g = editwin.entry_g.get()
            ext = editwin.entry_ext.get()
            if prof not in self.settings["Profiles"]:
                self.settings["Profiles"][prof] = self.settings["CurrProfile"]
                try:
                    self.settings["Profiles"].pop(self.DDL.get())
                except KeyError:
                    logging.debug("Current value of ddl doesn't exist in 'Profiles'")
                self.ddlOpt = [x for x in self.settings["Profiles"].keys()]
                self.ddlOpt = natsorted(self.ddlOpt)
                self.ddlOpt.append("Add...")
                self.DDL["values"] = self.ddlOpt
                self.DDL.set(prof)
            self.settings["Profiles"][prof] = prof, dir_p, dir_g, ext
            self.DDL.event_generate("<<ComboboxSelected>>")
            editwin.on_close()

        editwin = AddEditWindow(self._root, self.Choose, ok_callback, "Edit Profile")

        editwin.entry_profile.state(["!readonly"])
        editwin.entry_profile.insert(0, self.settings["CurrProfile"][0])
        editwin.entry_profile.state(["readonly"])
        editwin.entry_p.state(["!readonly"])
        editwin.entry_p.insert(0, self.settings["CurrProfile"][1])
        editwin.entry_p.state(["readonly"])
        editwin.entry_g.state(["!readonly"])
        editwin.entry_g.insert(0, self.settings["CurrProfile"][2])
        editwin.entry_g.state(["readonly"])
        editwin.entry_ext.state(["!readonly"])
        editwin.entry_ext.insert(0, self.settings["CurrProfile"][3])
        editwin.entry_ext.state(["readonly"])

    def RemoveProfile(self):
        """
        Removes the currently selected profile
        then selects the next one in the list
        """
        remove = messagebox.askyesno(
            "Removing Profile", "Are you sure you want to remove the current profile"
        )
        if not remove:
            return
        try:
            # Remove profile from settings
            self.settings["Profiles"].pop(self.DDL.get())
            if not self.settings["Profiles"]:
                self.button_replace.state(["disabled"])
                self.button_backup.state(["disabled"])
            # Get the remaining profiles and sort them
            # then change the values in the combobox
            self.ddlOpt = [x for x in self.settings["Profiles"].keys()]
            self.ddlOpt = natsorted(self.ddlOpt)
            self.ddlOpt.append("Add...")
            self.DDL["values"] = self.ddlOpt
            # Set combobox to the next profile and generate
            # an event to update the current profile and treeviews
            self.DDL.set(list(self.settings["Profiles"])[0])
        except IndexError:
            # If all profiles dict is empty
            # set ddl to empty string
            self.DDL.set("")
        except KeyError:
            messagebox.showwarning(
                "No profiles", "No profiles to remove. Add one first"
            )
            return
        self.settings["ProfileCount"] = len(self.settings["Profiles"])
        self.DDL.event_generate("<<ComboboxSelected>>")

    def Replace(self):
        """
        Overwrites the selected game file
        with the selected personal file
        """
        # Get selection from treeviews
        selection_p = self.treeview_p.selection()
        selection_g = self.treeview_g.selection()
        # Make sure there is an actual selection
        if not (selection_p and selection_g):
            messagebox.showwarning(
                "No selection",
                "Please choose a file to copy from the left list\nand a file to overwrite from the right list",
            )
            return
        src = self.settings["CurrFilesP"][selection_p[0]]
        if Path(src).is_dir():
            messagebox.showwarning(
                "Choose a file", "Please choose a file not a folder from the left list"
            )
            return
        # Disable button to prevent it from being spammed
        self.button_replace.state(["disabled"])
        dst = self.settings["CurrFilesG"][selection_g[0]]
        try:
            shutil.copy2(src, dst)
            backup = self.bak / (
                datetime.now().strftime("%Y_%m_%d_%Hhr_%Mmin_%Ss_") + Path(dst).name
            )
            shutil.copy2(dst, backup)
            if "BAK" in dst:
                Helpers.AKReplace(src, dst, self.settings)
        except OSError as e:
            logging.error(f"Couldn't copy {e.strerror}")
            messagebox.showerror("COPY ERORR", "Couldn't copy the file.")

        # blink the selected game file to inidicate successful replace
        self.treeview_g.selection_remove(selection_g[0])
        self._root.after(250, self.treeview_g.selection_set, selection_g[0])
        self._root.after(250, self.button_replace.state, ["!disabled"])

    def Backup(self):
        """
        Creates a copy of the selected game file
        and puts it in the personal folder
        """
        overwrite, toSub = False, True
        ext = self.settings["CurrProfile"][3]
        selection_p = self.treeview_p.selection()
        selection_g = self.treeview_g.selection()
        parent = self.treeview_p.parent(selection_p[0]) if selection_p else ""
        # Warn user if a game file is not selected
        if not selection_g:
            messagebox.showwarning(
                "No selection", "Please choose a file to backup from the right list"
            )
            return
        src = self.settings["CurrFilesG"][selection_g[0]]
        # If no personal file is selected use the main folder
        # otherwise use the selection
        if not selection_p:
            toSub = False
            dst = Path(self.settings["CurrProfile"][1])
        elif parent:
            dst = Path(self.settings["CurrFilesP"][parent])
        else:
            dst = Path(self.settings["CurrFilesP"][selection_p[0]])

        while True:
            backupName = askstring(
                "Backup file", "Choose a name for the backup file", parent=self._root
            )
            if backupName is None:
                return
            elif not backupName:
                messagebox.showwarning("No name", "Must choose a file name")
                continue
            # Check if chosen name already exists whether in the main folder
            # or if subfolder is selected check inside the subfolder
            else:
                lowerCaseDict = set(k.lower() for k in self.settings["CurrFilesP"])
                exists = (
                    (backupName + ext).lower() in lowerCaseDict
                    and (
                        dst == Path(self.settings["CurrProfile"][1]) or not dst.is_dir()
                    )
                ) or (dst.name + backupName + ext).lower() in lowerCaseDict
                if exists:
                    overwrite = messagebox.askyesno(
                        "Already exists",
                        "File name already exists would you like to overwrite it?",
                    )
                    if overwrite:
                        break
                    else:
                        continue
                else:
                    break
        # append extension to chosen name
        backupName += ext
        # if the selection is a subfolder use it as the path
        # otherwise it's the main folder
        if dst.is_dir() or self.treeview_p.parent(selection_p[0]):
            # if there are no files in the main folder
            # ask user if they want to add to the subfolder or the main one
            if self.fileCount <= 0:
                toSub = messagebox.askyesno(
                    "Backup",
                    "Add to currently selected subfolder (yes) or main folder (no)?",
                )
            if toSub:
                toSelect_p = dst.name + backupName
                dst = dst / backupName
            else:
                toSelect_p = backupName
                dst = Path(self.settings["CurrProfile"][1]) / backupName
        else:
            toSelect_p = backupName
            dst = Path(self.settings["CurrProfile"][1]) / backupName

        try:
            if "BAK" in src:
                Helpers.AKBackup(src, dst, self.settings)
            else:
                shutil.copy(src, dst)
        except OSError as e:
            logging.error(f"Couldn't copy {e.strerror}")
            messagebox.showerror("COPY ERORR", "Couldn't copy the file.")
        self.UpdateTree(tree="P", toSelect_p=toSelect_p)
        self.Save()

    def Save(self):
        """Save all the settings to the settings file"""
        coords = self._root.geometry().split("+")
        geo = coords[0].split("x")
        self.settings["Xcoord"] = int(coords[1])
        self.settings["Ycoord"] = int(coords[2])
        self.settings["Theme"] = self.currTheme.get()
        try:
            with open(self.settingsPath, "w") as f:
                json.dump(self.settings, f, indent=4)
            logging.info("Settings saved correctly")
        except OSError as e:
            logging.error(f"Couldn't save settings {e.strerror}")
            messagebox.showerror("SAVE ERROR", "Couldn't save settings.")

    def FileChecker(self):
        """
        Checks the last modified time of the personal and game folders
        then updates the treeviews if the folders were modified recently
        """
        if not self.settings["CurrProfile"]:
            self._root.after(1000, self.FileChecker)
            return
        toSelect_p = (
            self.treeview_p.selection()[0] if self.treeview_p.selection() else ""
        )
        toSelect_g = (
            self.treeview_g.selection()[0] if self.treeview_g.selection() else ""
        )

        # get current time
        now = datetime.now()
        # get last modified time of each folder
        path_p = Path(self.settings["CurrProfile"][1])
        time_p = datetime.fromtimestamp(path_p.stat().st_mtime)
        time_g = datetime.fromtimestamp(
            Path(self.settings["CurrProfile"][2]).stat().st_mtime
        )

        # if last modified time is greater than one second update the treeview
        if now - time_p > timedelta(seconds=1) and now - time_p < timedelta(seconds=3):
            self.UpdateTree(tree="P", toSelect_p=toSelect_p)
        if now - time_g > timedelta(seconds=1) and now - time_g < timedelta(seconds=3):
            self.UpdateTree(tree="G", toSelect_g=toSelect_g)

        # check all subfolders recursively
        for file in path_p.rglob("*"):
            time = datetime.fromtimestamp(file.stat().st_mtime)
            if now - time > timedelta(seconds=1) and now - time < timedelta(seconds=3):
                self.UpdateTree(tree="P", toSelect_p=toSelect_p)

        self._root.after(1000, self.FileChecker)

    def on_close(self):
        self.Save()
        self._root.destroy()


# for testing
def main():
    root = Tk()
    savefileManager = SavefileManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
