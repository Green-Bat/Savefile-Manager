# Tkinter modules
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from tkinter.simpledialog import askstring

# general modules
import shutil, logging, json
from pathlib import Path
from threading import Thread
from datetime import datetime, timedelta
from os import startfile
from natsort import natsorted

# my modules
from SFMTree import SFMTree
from Theme import Theme
from AddEditWindow import AddEditWindow
from TreeviewToolTip import TVToolTip
import Helpers

# TODO:
# -[x] Add label to ddl
# -[] rewrite logging
# -[] Resizing
# -[] Center message boxes
# -[] Auto convert for arkham?
# -[] Underline folder labels


class SavefileManager:
    VERSION = "v2.8"

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
        self.settings: dict = {
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
            with self.settingsPath.open("r", encoding="utf-8") as f:
                settings: dict = json.load(f)
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

                def CleanBackups():
                    self.settings["LogTime"] = str(datetime.now())
                    for file in self.bak.iterdir():
                        if file.is_file():
                            file.unlink()
                        elif file.is_dir() and not file.samefile(self.bakDeleted):
                            shutil.rmtree(file)
                    for file in self.bakDeleted.iterdir():
                        if file.is_file():
                            file.unlink()
                        elif file.is_dir():
                            shutil.rmtree(file)

                Thread(target=CleanBackups).start()
            logging.info("Settings file successfully loaded")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.basicConfig(filename=self.logpath, level=logging.DEBUG, format=fmt)
            logging.error(f"Settings file missing/corrupt")
            try:
                with self.settingsPath.open("w", encoding="utf-8") as f:
                    json.dump(self.settings, f, indent=4)
                logging.info("Settings file successfully generated")
            except OSError as e:
                logging.error(f"Couldn't generate settings file {e.strerror}")
                messagebox.showerror("ERROR", "Couldn't make settings file.")
                root.destroy()
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
        root.bind("<Button-1>", lambda e: root.focus_set())
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
        self.frame_header.grid_rowconfigure((0, 2), weight=1, uniform="row")

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

        ttk.Label(
            self.frame_header,
            text=f"Savefile Manager {self.VERSION}",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=0, sticky="ew")

        # DropDownList
        ttk.Label(
            self.frame_header,
            text="Profiles: ",
            font=("Arial", 9),
            width=20,
            padding=(0, 0, 0, 20),
            justify="center",
        ).grid(row=0, column=1, sticky="es", pady=7)
        self.ddlOpt = natsorted(self.settings["Profiles"].keys())
        self.ddlOpt.append("Add...")
        self.DDL = ttk.Combobox(
            self.frame_header,
            values=self.ddlOpt,
            height=6,
            width=20,
        )
        self.DDL.state(["readonly"])
        self.DDL.bind("<<ComboboxSelected>>", self.updateDDL)
        self.DDL.bind("<<FocusOut>>", lambda e: self.DDL.selection_clear(0, END))
        self.DDL.grid(row=0, column=1, sticky="es", padx=5, pady=2)

        # Path Labels
        self.PathLabel_p = ttk.Label(
            self.frame_header,
            wraplength=self.geo[0],
            style="Path.TLabel",
            cursor="hand2",
        )
        self.PathLabel_g = ttk.Label(
            self.frame_header,
            wraplength=self.geo[0],
            style="Path.TLabel",
            cursor="hand2",
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
        self.PathLabel_p.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        self.PathLabel_g.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        # -------------------- END OF HEADER FRAME --------------------

        # -------------------- BODY FRAME --------------------
        self.frame_body = ttk.Frame(self._root, width=self.geo[0])
        self.frame_body.pack(fill="x")
        self.frame_body.columnconfigure(1, weight=1)
        self.frame_body.rowconfigure(0, weight=1)
        self.frame_body.rowconfigure(1, weight=2)

        # Treeview
        # Add icons for files and folders
        self.fileIco = ImageTk.PhotoImage(
            Image.open("images/ico1.ico").resize((20, 20), Image.LANCZOS)
        )
        self.folderIco = ImageTk.PhotoImage(
            Image.open("images/ico4.ico").resize((22, 22), Image.LANCZOS)
        )
        self.treeview_p = SFMTree(
            self.frame_body,
            currFiles=self.settings["CurrFilesP"],
            backupFolder=self.bakDeleted,
            fileIco=self.fileIco,
            folderIco=self.folderIco,
            save_callback=self.Save,
            selectmode="browse",
            height=17,
            show="tree",
        )
        self.treeview_g = SFMTree(
            self.frame_body,
            currFiles=self.settings["CurrFilesG"],
            backupFolder=self.bakDeleted,
            subfolders=False,
            fileIco=self.fileIco,
            folderIco=self.folderIco,
            save_callback=self.Save,
            selectmode="browse",
            height=6,
            show="tree",
        )
        # Add scrollbar
        self.yscroll = ttk.Scrollbar(
            self.frame_body, orient=VERTICAL, command=self.treeview_p.yview
        )
        self.yscrollg = ttk.Scrollbar(
            self.frame_body, orient=VERTICAL, command=self.treeview_g.yview
        )
        self.treeview_p.config(yscrollcommand=self.yscroll.set)
        self.treeview_g.config(yscrollcommand=self.yscrollg.set)
        self.yscroll.grid(row=0, rowspan=2, column=0, sticky="nse", pady=5, padx=5)
        self.yscrollg.grid(row=0, rowspan=1, column=2, sticky="nse", pady=5, padx=5)
        # Treeview buttons
        # ------------- BUTTON SUB-FRAME -------------
        self.frame_button = ttk.Frame(self.frame_body)
        self.frame_button.grid(row=0, column=1)
        self.button_replace = ttk.Button(
            self.frame_button, text="=>", command=self.Replace, cursor="hand2"
        )
        self.button_backup = ttk.Button(
            self.frame_button, text="<=", command=self.Backup, cursor="hand2"
        )
        self.button_replace.grid(row=0, column=0, sticky="ns", pady=5)
        self.button_backup.grid(row=1, column=0, sticky="ns", pady=5)
        # ------------- END OF BUTTON SUB-FRAME -------------
        self.treeview_p.grid(
            row=0, rowspan=2, column=0, sticky="wns", padx=5, pady=5, ipady=5
        )
        self.treeview_g.grid(row=0, rowspan=1, column=2, sticky="nse", padx=5, pady=5)

        self.treeMenu_g = Menu()
        self.treeMenu_g.add_command(
            label="Rename", command=lambda: self.treeview_g.RenameFile(warn=True)
        )
        self.treeMenu_g.add_command(label="Delete", command=self.treeview_g.DeleteFile)
        self.treeMenu_g.add_command(
            label="Create Folder", command=self.treeview_g.CreateFolder
        )

        self.treeMenu_p = Menu()
        self.treeMenu_p.add_command(label="Rename", command=self.treeview_p.RenameFile)
        self.treeMenu_p.add_command(label="Delete", command=self.treeview_p.DeleteFile)
        self.treeMenu_p.add_command(
            label="Create Folder", command=self.treeview_p.CreateFolder
        )
        self.treeview_g.bind("<Button-3>", self.TreeviewMenu)
        self.treeview_p.bind("<Button-3>", self.TreeviewMenu)
        TVToolTip(
            self.treeview_p,
            extra_width=self.fileIco.width()
            + self.yscroll.winfo_reqwidth()
            + self.yscroll.grid_info()["padx"],
        ).bind()
        TVToolTip(
            self.treeview_g,
            extra_width=self.fileIco.width()
            + self.yscrollg.winfo_reqwidth()
            + self.yscrollg.grid_info()["padx"],
        ).bind()
        # -------------------- END OF BODY FRAME --------------------
        # Set theme
        if self.settings["Theme"]:
            self.currTheme.set(self.settings["Theme"])
        else:
            self.currTheme.set("Dark")
        # Fill tree if there is an exisiting profile
        # otherwise disable the buttons
        if self.settings["CurrProfile"]:
            self.DDL.set(self.settings["CurrProfile"][0])
            self.DDL.event_generate("<<ComboboxSelected>>")
        else:
            self.button_backup.state(["disabled"])
            self.button_replace.state(["disabled"])
        self.checker_id = root.after(1000, self.FileChecker)
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
        (
            self.treeview_g.selection_set(
                self.treeview_g.identify("item", event.x, event.y)
            )
            if inTree_g
            else ""
        )
        (
            self.treeview_p.selection_set(
                self.treeview_p.identify("item", event.x, event.y)
            )
            if inTree_p
            else ""
        )
        if inTree_g:
            if not self.treeview_g.selection():
                self.treeMenu_g.entryconfig("Rename", state="disabled")
                self.treeMenu_g.entryconfig("Delete", state="disabled")
            else:
                self.treeMenu_g.entryconfig("Rename", state="normal")
                self.treeMenu_g.entryconfig("Delete", state="normal")
            self.treeMenu_g.post(event.x_root, event.y_root)
        elif inTree_p:
            if not self.treeview_p.selection():
                self.treeMenu_p.entryconfig("Rename", state="disabled")
                self.treeMenu_p.entryconfig("Delete", state="disabled")
            else:
                self.treeMenu_p.entryconfig("Rename", state="normal")
                self.treeMenu_p.entryconfig("Delete", state="normal")
            self.treeMenu_p.post(event.x_root, event.y_root)

    def UpdateMissingFolder(self):
        logging.error("Game/Personal folder deleted")
        messagebox.showerror(
            "Missing Folder",
            "Game/Personal folder has been deleted/changed please update it",
        )

        def ok_callback(edit: AddEditWindow):
            prof = edit.entry_profile.get()
            dir_p = edit.entry_p.get()
            dir_g = edit.entry_g.get()
            if not (Path(dir_g).exists() and Path(dir_p).exists()):
                messagebox.showwarning(
                    "Folder Doesn't Exist",
                    "Chosen game/personal folder doesn't exist. Please change it.",
                )
                return
            edit.profile_updated = True
            self.settings["Profiles"][prof][1:3] = dir_p, dir_g
            self.DDL.event_generate("<<ComboboxSelected>>")
            edit.on_close()

        editwin = AddEditWindow(
            self._root, self.settings["CurrProfile"], ok_callback, "Update Folders"
        )
        editwin.button_profile.state(["disabled"])
        editwin.button_extension.state(["disabled"])
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
        editwin.wait_window()
        if not editwin.profile_updated:
            self.RemoveProfile(self.settings["CurrProfile"][0])

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

        self.settings["CurrProfile"] = self.settings["Profiles"].get(self.DDL.get(), [])
        if self.settings["CurrProfile"]:
            perosnal_folder = Path(self.settings["CurrProfile"][1])
            game_folder = Path(self.settings["CurrProfile"][2])
            if not (game_folder.exists() and perosnal_folder.exists()):
                self.UpdateMissingFolder()
                return
            self.PathLabel_p.config(
                text="Current personal directory: " + self.settings["CurrProfile"][1],
                width=self.geo[0],
            )
            self.PathLabel_g.config(
                text="Current game directory: " + self.settings["CurrProfile"][2],
                width=self.geo[0],
            )
            self.fileCount = self.treeview_p.Update(
                init=True,
                folderPath=self.settings["CurrProfile"][1],
                extension=self.settings["CurrProfile"][3],
            )
            self.treeview_g.Update(
                init=True,
                folderPath=self.settings["CurrProfile"][2],
                extension=self.settings["CurrProfile"][3],
            )
            logging.info(
                f"Profile loaded successfully ({self.settings["CurrProfile"][0]})"
            )
        else:
            self.PathLabel_p.config(text="", width=0)
            self.PathLabel_g.config(text="", width=0)
            self.fileCount = self.treeview_p.Update(init=True)
            self.treeview_g.Update(init=True)

    def AddProfile(self) -> bool:
        """
        Asks user to add a profile by asking for two directories,
        a personal one and the game's savefile folder,
        a profile name, and a file extension, then saves it
        """

        def ok_callback(add: AddEditWindow):
            dir_p = add.entry_p.get()
            dir_g = add.entry_g.get()
            ext = add.entry_ext.get()
            if not (dir_p and dir_g):
                logging.warning("Incomplete profile warning")
                messagebox.showwarning(
                    "Incomplete Profile",
                    "Please make sure you fill in all the necessary profile information",
                )
                return
            newProf = (
                add.entry_profile.get()
                if add.entry_profile.get()
                else f"Profile {self.settings['ProfileCount']+1}"
            )
            if newProf in self.settings["Profiles"]:
                logging.warning("Profile name already exists")
                messagebox.showwarning(
                    "Profile Name Exists",
                    "Profile name already exists please choose another one",
                )
                return
            self.settings["Profiles"][newProf] = [newProf, dir_p, dir_g, ext]
            self.ddlOpt = natsorted(self.settings["Profiles"].keys())
            self.ddlOpt.append("Add...")
            self.DDL["values"] = self.ddlOpt
            self.DDL.set(newProf)
            self.DDL.event_generate("<<ComboboxSelected>>")
            if self.button_replace.instate(["disabled"]):
                self.button_replace.state(["!disabled"])
                self.button_backup.state(["!disabled"])
            self.settings["ProfileCount"] = len(self.settings["Profiles"])
            add.profile_added = True
            add.on_close()

        addWin = AddEditWindow(
            self._root, self.settings["CurrProfile"], ok_callback, "Add Profile"
        )
        addWin.wait_window()
        logging.info(f"New profile added ({self.settings['CurrProfile'][0]})")
        return addWin.profile_added

    def EditProfile(self):
        """
        Allows user to edit the currently selected profile
        """
        if not self.settings["Profiles"]:
            logging.warning("attempt to edit when no profiles exist")
            messagebox.showwarning("No profiles", "No profiles exist. Add one first")
            return

        def ok_callback(edit: AddEditWindow):
            prof = edit.entry_profile.get()
            dir_p = edit.entry_p.get()
            dir_g = edit.entry_g.get()
            ext = edit.entry_ext.get()
            if (
                prof != self.settings["CurrProfile"][0]
                and prof in self.settings["Profiles"]
            ):
                logging.warning("Profile name already exists")
                messagebox.showwarning(
                    "Profile Name Exists",
                    "Profile name already exists please choose another one",
                )
                return
            if prof not in self.settings["Profiles"]:
                self.settings["Profiles"][prof] = self.settings["CurrProfile"]
                try:
                    self.settings["Profiles"].pop(self.DDL.get())
                except KeyError:
                    logging.debug("Current value of ddl doesn't exist in 'Profiles'")
                self.ddlOpt = natsorted(self.settings["Profiles"].keys())
                self.ddlOpt.append("Add...")
                self.DDL["values"] = self.ddlOpt
                self.DDL.set(prof)
            self.settings["Profiles"][prof] = prof, dir_p, dir_g, ext
            self.DDL.event_generate("<<ComboboxSelected>>")
            edit.on_close()

        editwin = AddEditWindow(
            self._root, self.settings["CurrProfile"], ok_callback, "Edit Profile"
        )

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
        logging.info(f"Profile updated ({self.settings['CurrProfile'][0]})")

    def RemoveProfile(self, to_remove: str = None):
        """
        Removes the currently selected profile
        then selects the next one in the list
        """
        if not (
            to_remove
            or messagebox.askyesno(
                "Removing Profile",
                "Are you sure you want to remove the current profile?",
            )
        ):
            return
        try:
            # Remove profile from settings
            self.settings["Profiles"].pop(to_remove or self.DDL.get())
            if not self.settings["Profiles"]:
                self.button_replace.state(["disabled"])
                self.button_backup.state(["disabled"])
            # Get the remaining profiles and sort them
            # then change the values in the combobox
            self.ddlOpt = natsorted(self.settings["Profiles"].keys())
            if not self.ddlOpt:
                self.DDL.set("")
            else:
                # Set combobox to the next profile
                self.DDL.set(self.ddlOpt[0])
            self.ddlOpt.append("Add...")
            self.DDL["values"] = self.ddlOpt
        except KeyError:
            messagebox.showwarning(
                "No profiles", "No profiles to remove. Add one first"
            )
        else:
            self.settings["ProfileCount"] = len(self.settings["Profiles"])
            # generate an event to update the current profile and treeviews
            self.DDL.event_generate("<<ComboboxSelected>>")
        logging.info(f"Profile deleted ({to_remove})")

    def Replace(self):
        """
        Overwrites the selected game file
        with the selected personal file
        """
        selection_p = self.treeview_p.selection()
        selection_g = self.treeview_g.selection()
        if not (selection_p and selection_g):
            messagebox.showwarning(
                "No selection",
                "Please choose a file/folder to copy from the left list\nand a file/folder to overwrite from the right list",
            )
            return
        selection_p, selection_g = selection_p[0], selection_g[0]
        src = Path(self.settings["CurrFilesP"][selection_p])
        dst = Path(self.settings["CurrFilesG"][selection_g])
        if (src.is_file() and dst.is_dir()) or (src.is_dir() and dst.is_file()):
            messagebox.showwarning(
                "Folder-to-File Warning",
                "Please make sure your copying folder-to-folder/file-to-file.",
            )
            logging.warning("Folder-to-File Error")
            return
        # Disable button to prevent it from being spammed
        self.button_replace.state(["disabled"])
        try:
            if "BAK" in dst.name:
                Helpers.AKReplace(src, dst, self.settings)
            elif src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            elif src.is_file():
                shutil.copy2(src, dst)
        except OSError as e:
            logging.error(f"Couldn't copy {e.strerror}")
            messagebox.showerror("COPY ERORR", "Couldn't copy. Check log file.")
            self._root.after(250, self.button_replace.state, ["!disabled"])
            return
        backup = self.bak / (
            datetime.now().strftime("%Y_%m_%d_%Hhr_%Mmin_%Ss_") + dst.name
        )
        try:
            if dst.is_dir():
                shutil.copytree(dst, backup)
            elif dst.is_file():
                shutil.copy2(dst, backup)
        except OSError as e:
            logging.error(f"Couldn't copy {e.strerror}")
            messagebox.showerror("COPY ERORR", "Couldn't copy. Check log file.")
            return
        finally:
            self._root.after(250, self.button_replace.state, ["!disabled"])

        # blink the selected game file to inidicate successful replace
        self.treeview_g.selection_remove(selection_g)
        self._root.after(250, self.treeview_g.selection_set, selection_g)

    def Backup(self):
        """
        Creates a copy of the selected game file
        and puts it in the personal folder
        """
        overwrite, toSub = False, True
        selection_p = self.treeview_p.selection()
        selection_p = selection_p[0] if selection_p else ""
        selection_g = self.treeview_g.selection()
        parent = self.treeview_p.parent(selection_p)
        toSelect_p = ""
        if not selection_g:
            messagebox.showwarning(
                "No selection",
                "Please choose a file/folder to backup from the right list",
            )
            return
        src = Path(self.settings["CurrFilesG"][selection_g[0]])
        # If no personal file is selected use the main folder
        # otherwise use the selected folder/subfolder
        if not selection_p:
            dst = Path(self.settings["CurrProfile"][1])
        else:
            dst = Path(self.settings["CurrFilesP"][selection_p])
            # if there are no files and only folders in the tree prompt user
            # to choose where the backup will go, either main folder or current selection
            if not parent and self.fileCount <= 0:
                toSub = messagebox.askyesno(
                    "Backup",
                    "Add to currently selected folder (yes) or main folder (no)?",
                )
                dst = Path(self.settings["CurrProfile"][1]) if not toSub else dst

        if dst.is_file():
            toSelect_p = parent
            dst = dst.parent
        else:
            toSelect_p = selection_p

        while True:
            backupName = askstring(
                "Backup file",
                "Choose a name for the backup file/folder",
                parent=self._root,
            )
            if backupName is None:
                return
            elif not backupName:
                messagebox.showwarning("No name", "Must choose a file name")
            else:
                if src.is_file() and not backupName.endswith(src.suffix):
                    backupName += src.suffix
                if (temp := dst / backupName).exists():
                    match [src.is_file(), temp.is_file()]:
                        case [1, 0] | [0, 1]:
                            messagebox.showwarning(
                                "Already exists",
                                "Can't use this name, choose another one.",
                            )
                        case [1, 1] | [0, 0]:
                            overwrite = messagebox.askyesno(
                                "Already exists",
                                "File/folder already exists would you like to overwrite it?",
                            )
                            if overwrite:
                                break
                else:
                    break

        if not dst.samefile(self.settings["CurrProfile"][1]):
            toSelect_p += backupName
        else:
            toSelect_p = backupName

        dst = dst / backupName
        try:
            if src.is_file():
                if "BAK" in src.name:
                    Helpers.AKBackup(src, dst, self.settings)
                else:
                    shutil.copy(src, dst)
            elif src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=overwrite)
        except OSError as e:
            logging.error(f"Couldn't copy {e.strerror}")
            messagebox.showerror("COPY ERORR", "Couldn't copy the file. Check log file")
            return
        self.fileCount = self.treeview_p.Update(toSelect=toSelect_p)

    def Save(self):
        """Save all the settings to the settings file"""
        coords = self._root.geometry().split("+")
        geo = coords[0].split("x")
        self.settings["Xcoord"] = int(coords[1])
        self.settings["Ycoord"] = int(coords[2])
        self.settings["Theme"] = self.currTheme.get()
        try:
            with self.settingsPath.open("w", encoding="utf-8") as f:
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
            self.checker_id = self._root.after(1000, self.FileChecker)
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
        path_g = Path(self.settings["CurrProfile"][2])
        if not (path_g.exists() and path_p.exists()):
            self.UpdateMissingFolder()
            self.checker_id = self._root.after(1000, self.FileChecker)
            return
        time_p = datetime.fromtimestamp(path_p.stat().st_mtime)
        time_g = datetime.fromtimestamp(path_g.stat().st_mtime)

        # if last modified time is greater than one second update the treeview
        if now - time_p > timedelta(seconds=1) and now - time_p < timedelta(seconds=3):
            logging.info("Personal folder updated/modified")
            self.fileCount = self.treeview_p.Update(toSelect=toSelect_p)
        if now - time_g > timedelta(seconds=1) and now - time_g < timedelta(seconds=3):
            logging.info("Game folder updated/modified")
            self.treeview_g.Update(toSelect=toSelect_g)

        # check all subfolders recursively
        for folder in (f for f in path_p.rglob("*") if f.is_dir()):
            time = datetime.fromtimestamp(folder.stat().st_mtime)
            if now - time > timedelta(seconds=1) and now - time < timedelta(seconds=3):
                logging.info(f"Personal Sub-folder updated/modified ({str(folder)})")
                self.fileCount = self.treeview_p.Update(toSelect=toSelect_p)
        for folder in (f for f in path_g.rglob("*") if f.is_dir()):
            time = datetime.fromtimestamp(folder.stat().st_mtime)
            if now - time > timedelta(seconds=1) and now - time < timedelta(seconds=3):
                logging.info(f"Game Sub-folder updated/modified ({str(folder)})")
                self.treeview_g.Update(toSelect=toSelect_g)

        self.checker_id = self._root.after(1000, self.FileChecker)

    def on_close(self):
        self.Save()
        self._root.destroy()


def main():
    import ctypes, sys

    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

    import requests, requests.exceptions, webbrowser
    from packaging import version

    latest_release = (
        "https://api.github.com/repos/Green-Bat/Savefile-Manager/releases/latest"
    )
    releases_page = "https://github.com/Green-Bat/Savefile-Manager/releases"
    root = Tk()
    savefileManager = SavefileManager(root)
    try:
        response = requests.get(latest_release, timeout=5)
        cur_version = response.json()["name"]
        if version.parse(savefileManager.VERSION) < version.parse(cur_version):
            if messagebox.askyesno(
                "New Version Available",
                "A new version of the Savefile Manager is available, would you like to download it?",
            ):
                webbrowser.open(releases_page)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to check for new version {e.strerror}")
    except webbrowser.Error:
        logging.error("Failed to open webpage")
        messagebox.showerror(
            "Failed",
            f"Failed to open webpage. To download new version go to {releases_page}",
        )
    finally:
        root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical("Unexpected error", exc_info=e)
        messagebox.showerror(
            "CRITICAL ERROR", "Unexpected error, check log file for more info"
        )
