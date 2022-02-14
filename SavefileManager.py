# Tkinter modules
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from tkinter import font
from tkinter.simpledialog import askstring

# from ttkthemes import ThemedStyle

# general modules
import json
from datetime import datetime, time, timedelta
import shutil
from os import startfile
from pathlib import Path
import logging
from natsort import os_sorted, natsorted

# my modules
from Theme import Theme

# TODO:
# -[x] Replace method
# -[x] Backup method
# -[x] Add treeview scrollbar
# -[x] Edit method
# -[x] Double clicking labels opens directory
# auto update treeviews
# Maintain selection after update
# create backups of files before replacing and backup
# Resizing
# - [/] Remember window coordinates (& dimensions)
# Arkham version
#   auto convert for arkham version?
# center message boxes
# -[x] Themes
# Add context menu for treeview


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
                "Theme": "",
            }
            try:
                with self.settingsPath.open("w") as f:
                    json.dump(self.settings, f, indent=4)
                logging.info("Settings file successfully generated")
            except OSError as e:
                logging.error(f"Couldn't generate settings file {e.strerror}")
                messagebox.showerror(
                    "ERROR", "Couldn't make settings file. Check log file"
                )
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # -------------------- GUI INIT  -------------------------
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # keep a refrence of the base window
        self._root = root
        self.theme = Theme(self._root)

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.title("Savefile Manager")
        root.resizable(False, False)
        self.geo = ("490", "485")

        if int(self.settings["Xcoord"]) + 480 > root.winfo_screenwidth():
            self.settings["Xcoord"] = root.winfo_screenwidth() - 480

        if int(self.settings["Ycoord"]) + 480 > root.winfo_screenheight():
            self.settings["Ycoord"] = root.winfo_screenheight() - 480

        root.geometry(
            f"{'x'.join(self.geo)}+{self.settings['Xcoord']}+{self.settings['Ycoord']}"
        )

        # -------------------- HEADER FRAME --------------------
        self.frame_header = ttk.Frame(root, width=self.geo[0], height=100)
        self.frame_header.pack()
        self.frame_header.grid_propagate(False)
        self.frame_header.columnconfigure((0, 1), weight=1)

        # MENUBAR
        root.option_add("*tearOff", False)
        self.menubar = Menu(
            self.frame_header,
        )
        root.config(menu=self.menubar)
        self.options = Menu(self.menubar)
        self.options.add_command(label="Add", command=self.AddProfile)
        self.options.add_command(label="Edit", command=self.EditProfile)
        self.options.add_command(label="Remove", command=self.RemoveProfile)
        self.currTheme = StringVar(value="Dark")
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

        # Set the theme
        self.currTheme.trace_add(
            "write",
            callback=lambda var, index, mode: self.theme.SetTheme(
                self.currTheme.get(), self.options, self.themesMenu
            ),
        )
        if self.settings["Theme"]:
            self.currTheme.set(self.settings["Theme"])
        else:
            self.currTheme.set("Dark")

        # DropDownList
        ttk.Label(
            self.frame_header,
            text="Savefile Manager",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=0, sticky="ew")

        self.ddlOpt = [x for x in self.settings["Profiles"].keys()]
        self.ddlOpt = natsorted(self.ddlOpt)
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
        self.treeview_p = ttk.Treeview(
            self.frame_body, selectmode="browse", height=17, show="tree"
        )
        self.treeview_g = ttk.Treeview(
            self.frame_body,
            selectmode="browse",
            height=10,
            show="tree",
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
            self.frame_button,
            text="=>",
            command=self.Replace,
        )
        self.button_backup = ttk.Button(
            self.frame_button,
            text="<=",
            command=self.Backup,
        )
        self.button_replace.grid(row=0, column=0, sticky="ns", pady=5)
        self.button_backup.grid(row=1, column=0, sticky="ns", pady=5)
        # ------------- END OF BUTTON SUB-FRAME -------------
        self.treeview_p.grid(row=0, rowspan=2, column=0, sticky="w", padx=5, pady=5)
        self.treeview_g.grid(row=0, rowspan=2, column=2, sticky="ne", padx=5, pady=5)
        # -------------------- END OF BODY FRAME --------------------
        # Fill tree if there is an exisiting profile
        if self.settings["CurrProfile"]:
            self.UpdateTree(init=True)
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # --------------------- END OF INIT ----------------------
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def UpdateTree(self, init=False, tree: str = "Both", toSelect: str = None):
        """
        Initializes the treeviews and handles
        any updates when switching between profiles

        Args:
            init: used when initializing
                prevents deleting of treeview items
                since they wouldn't have any items

            tree: Determines which tree to update.
                Can be ['G', 'P', 'Both']

            toSelect: id of item to select after updating
        """
        # If initializing gui don't delete since tree already empty
        if not init:
            if tree == "P" or tree == "Both":
                for child in self.treeview_p.get_children():
                    self.treeview_p.delete(child)
                self.settings["CurrFilesP"].clear()
            if tree == "G" or tree == "Both":
                for child in self.treeview_g.get_children():
                    self.treeview_g.delete(child)
                self.settings["CurrFilesG"].clear()

        # Add subfolders for the personal directory
        if tree == "P" or tree == "Both":
            p = Path(self.settings["CurrProfile"][1])
            self.AddSubfolders(p)
            # Add the rest of the files
            for file in os_sorted(p.glob(f"*{self.settings['CurrProfile'][3]}")):
                # uses file name as tree id
                self.treeview_p.insert("", "end", file.name, text=file.name)
                self.settings["CurrFilesP"][file.name] = str(file)
        # Add the files in the game's directory
        if tree == "G" or tree == "Both":
            g = Path(self.settings["CurrProfile"][2])
            for file in os_sorted(g.glob(f"*{self.settings['CurrProfile'][3]}")):
                self.fileCount += 1
                self.treeview_g.insert("", "end", file.name, text=file.name)
                self.settings["CurrFilesG"][file.name] = str(file)
        if toSelect:
            self.treeview_p.selection_set(toSelect)
            self.treeview_p.see(toSelect)

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
                # use folder name as tree id
                # for subfolder use folder name concatenated with subfolder name
                Parentiid = self.treeview_p.insert(
                    Parent, "end", Parent + folder.name, text=folder.name
                )
                self.settings["CurrFilesP"][Parentiid] = str(folder)
                self.AddSubfolders(folder, Parent=Parentiid)
                # fmt: off
                for file in os_sorted(folder.glob(f"*{self.settings['CurrProfile'][3]}")):
                    Parentiid2 = self.treeview_p.insert(
                        Parentiid, "end", Parentiid + file.name, text=file.name
                    )
                    self.settings["CurrFilesP"][Parentiid2] = str(file)
                # fmt: on

    def updateDDL(self, event: Event):
        """
        Updates treeviews and settings json
        when changing combobox option
        """
        # Change current profile
        self.settings["CurrProfile"] = self.settings["Profiles"][self.DDL.get()]
        # Change path labels
        self.PathLabel_p.config(
            text="Current personal directory: " + self.settings["CurrProfile"][1]
        )
        self.PathLabel_g.config(
            text="Current game directory: " + self.settings["CurrProfile"][2]
        )
        # Update treeviews
        self.UpdateTree()
        print(self.DDL.get())
        # Save to settings.json
        self.Save()

    def AddProfile(self):
        """
        Ask user to add a profile by asking for two directories,
        a personal one and the game's save folder,
        a profile name, and a file extension, then save it
        """
        # Ask for folders
        dir_p = self.settings["CurrProfile"][1] if self.settings["CurrProfile"] else ""
        dir_g = self.settings["CurrProfile"][2] if self.settings["CurrProfile"] else ""
        while True:
            dir_p = filedialog.askdirectory(
                initialdir=dir_p,
                title="Please choose your OWN personal directory",
            )
            if not dir_p:
                return
            dir_g = filedialog.askdirectory(
                initialdir=dir_g,
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
            newProf = askstring(
                "Profile name", "Choose a name for your new profile", parent=self._root
            )
            # pressing cancel returns None so
            # distinguishing None vs an empty string here is important
            if newProf is None:
                return
            # pressing ok on an empty inputbox returns an empty string
            elif not newProf:
                logging.warning("No profile name")
                messagebox.showwarning("No name", "Profile must have a name")
                continue
            elif newProf in self.DDL["values"]:
                logging.warning("Profile name already exists")
                messagebox.showwarning(
                    "Profile already exists",
                    f"'{newProf}' already exists please chose another name",
                )
                continue
            else:
                break
        # Ask for the file extension
        while True:
            ext = askstring(
                "Extenstion", "Enter the savefiles' extension", parent=self._root
            )
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
        self.ddlOpt = natsorted(self.ddlOpt)
        self.DDL["values"] = self.ddlOpt
        self.DDL.set(newProf)
        self.settings["Profiles"][newProf] = [newProf, dir_p, dir_g, ext]
        self.DDL.event_generate("<<ComboboxSelected>>")
        self.Save()

    def EditProfile(self):
        if not self.settings["Profiles"]:
            logging.warning("attempt to edit when no profiles exist")
            messagebox.showwarning("No profiles", "No profiles exist. Add one first")
            return

        def Change(name: str, index: int):
            newval = askstring("Update", f"Change the {name}", parent=self._root)
            self.editwin.grab_set()
            self.editwin.wait_window()
            if not newval:
                return
            if name == "extension" and not name.startswith("."):
                newval = "." + newval
            elif name == "profile name":
                self.settings["Profiles"][newval] = self.settings["CurrProfile"]
                try:
                    self.settings["Profiles"].pop(self.DDL.get())
                except KeyError:
                    logging.debug("Current value of ddl doesn't exist in 'Profiles'")
                self.ddlOpt = [x for x in self.settings["Profiles"].keys()]
                self.ddlOpt = natsorted(self.ddlOpt)
                self.DDL["values"] = self.ddlOpt
                self.DDL.set(newval)
            self.settings["CurrProfile"][index] = newval
            self.settings["Profiles"][self.DDL.get()][index] = newval

        def ChangeFile(folder, index):
            newfolder = filedialog.askdirectory(
                initialdir=self.settings["CurrProfile"][index],
                title=f"Please choose {folder} directory",
            )
            if not newfolder:
                return
            self.settings["CurrProfile"][index] = newfolder
            self.settings["Profiles"][self.DDL.get()][index] = newfolder

        def ok_callback():
            self.UpdateTree()
            self.Save()
            self.editwin.destroy()

        self.editwin = Toplevel(self._root)
        editStyle = ttk.Style(self.editwin)
        editStyle.configure("Edit.TButton", font=("Arial", 10), width=7)
        self.editwin.configure(background=self.theme.themes[self.currTheme.get()][2])
        self.editwin.resizable(False, False)
        coords = self._root.geometry().split("+")
        geo = list(map(int, coords[0].split("x")))
        coords.pop(0)
        coords = list(map(int, coords))
        w, h = geo
        x, y = coords
        self.editwin.geometry(f"260x200+{x+((w//2) - 130)}+{y+((h//2) - 100)}")

        ttk.Label(self.editwin, text="Change personal directory").grid(
            row=0, column=0, pady=5, padx=5, sticky="w"
        )
        ttk.Label(self.editwin, text="Change game's directory").grid(
            row=1, column=0, pady=5, padx=5, sticky="w"
        )
        ttk.Label(self.editwin, text="Change profile name").grid(
            row=2, column=0, pady=5, padx=5, sticky="w"
        )
        ttk.Label(self.editwin, text="Change extension").grid(
            row=3, column=0, pady=5, padx=5, sticky="w"
        )

        ttk.Button(
            self.editwin,
            text="Change",
            style="Edit.TButton",
            command=lambda: ChangeFile("personal", 1),
        ).grid(row=0, column=1, pady=5, padx=5, sticky="e")
        ttk.Button(
            self.editwin,
            text="Change",
            style="Edit.TButton",
            command=lambda: ChangeFile("game", 2),
        ).grid(row=1, column=1, pady=5, padx=5, sticky="e")
        ttk.Button(
            self.editwin,
            text="Change",
            style="Edit.TButton",
            command=lambda: Change("profile name", 0),
        ).grid(row=2, column=1, pady=5, padx=5, sticky="e")
        ttk.Button(
            self.editwin,
            text="Change",
            style="Edit.TButton",
            command=lambda: Change("extension", 3),
        ).grid(row=3, column=1, pady=5, padx=5, sticky="e")

        ttk.Button(
            self.editwin, text="OK", style="Edit.TButton", command=ok_callback
        ).grid(row=4, column=0)
        ttk.Button(
            self.editwin,
            text="Cancel",
            style="Edit.TButton",
            command=self.editwin.destroy,
        ).grid(row=4, column=1, sticky="w")
        self.editwin.grid_columnconfigure(1, weight=1)

        self.editwin.focus_force()
        self.editwin.grab_set()
        self.editwin.wait_window()

    def RemoveProfile(self):
        """
        Removes the currently selected profile
        then selects the next one in the list
        """
        # Remove profile from settings
        self.settings["Profiles"].pop(self.DDL.get())
        # Get the remaining profiles and sort them
        # then change the values in the combobox
        self.ddlOpt = [x for x in self.settings["Profiles"].keys()]
        self.ddlOpt = natsorted(self.ddlOpt)
        self.DDL["values"] = self.ddlOpt
        # Set combobox to the next profile and generate
        # an event to update the treeviews
        self.DDL.set(list(self.settings["Profiles"])[0])
        self.DDL.event_generate("<<ComboboxSelected>>")
        self.Save()

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
            logging.warning("No selection warning")
            messagebox.showwarning(
                "No selection",
                "Please choose a file to copy from the left list\nand a file to overwrite from the right list",
            )
            return
        src = self.settings["CurrFilesP"][selection_p[0]]
        if Path(src).is_dir():
            logging.warning("Folder chosen warning")
            messagebox.showwarning(
                "Choose a file", "Please choose a file not a folder from the left list"
            )
            return
        dst = self.settings["CurrFilesG"][selection_g[0]]
        try:
            shutil.copy2(src, dst)
            logging.info("Successful replace")
        except OSError as e:
            logging.error(f"Couldn't copy {e.strerror}")
            messagebox.showerror("COPY ERORR", "Couldn't copy the file. Check log file")

    def Backup(self):
        overwrite, toSub = False, True
        ext = self.settings["CurrProfile"][3]
        selection_p = self.treeview_p.selection()
        selection_g = self.treeview_g.selection()

        # Warn use if a game file is not selected
        if not selection_g:
            logging.warning("No selection warning")
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
            elif (
                (backupName + ext) in self.settings["CurrFilesP"] and not dst.is_dir()
            ) or (dst.name + backupName + ext) in self.settings["CurrFilesP"]:
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
        if dst.is_dir():
            # if there are no files in the main folder
            # ask user if they want to add to the subfolder or the main one
            if self.fileCount <= 0:
                toSub = messagebox.askyesno(
                    "Backup",
                    "Add to currently selected subfolder (yes) or main folder (no)?",
                )
            if toSub:
                toSelect = dst.name + backupName
                dst = dst / backupName
            else:
                toSelect = backupName
                dst = Path(self.settings["CurrProfile"][1]) / backupName
        else:
            toSelect = backupName
            dst = Path(self.settings["CurrProfile"][1]) / backupName

        try:
            shutil.copy(src, dst)
            logging.info("Successful backup")
        except OSError as e:
            logging.error(f"Couldn't copy {e.strerror}")
            messagebox.showerror("COPY ERORR", "Couldn't copy the file. Check log file")
        self.UpdateTree(tree="P", toSelect=toSelect)
        self.Save()

    def Save(self):
        coords = self._root.geometry().split("+")
        geo = coords[0].split("x")
        self.settings["Xcoord"] = coords[1]
        self.settings["Ycoord"] = coords[2]
        self.settings["Theme"] = self.currTheme.get()
        try:
            with open(self.settingsPath, "w") as f:
                json.dump(self.settings, f, indent=4)
            logging.info("Settings saved correctly")
        except OSError as e:
            logging.error(f"Couldn't save settings {e.strerror}")
            messagebox.showerror(
                "Settings file error", "Couldn't save settings. Check log file"
            )

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
