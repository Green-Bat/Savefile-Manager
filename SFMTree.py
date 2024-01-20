from tkinter import Misc, messagebox
from tkinter.ttk import Treeview
from tkinter.simpledialog import askstring
from PIL.ImageTk import PhotoImage

import logging
from pathlib import Path
from shutil import copytree, copy2, rmtree
from datetime import datetime
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from SavefileManager import SavefileManager

from natsort import os_sorted


class SFMTree(Treeview):
    def __init__(
        self,
        master: Misc | None = None,
        *,
        currFiles: dict[str, str],
        backupFolder: Path,
        subfolders: bool = True,
        fileIco: PhotoImage = None,
        folderIco: PhotoImage = None,
        save_callback: Callable[["SavefileManager"], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self.backupFolder = backupFolder
        self.currFiles = currFiles
        self.subfolders = subfolders
        self.fileIco = fileIco
        self.folderIco = folderIco
        self.save = save_callback

    def Update(
        self,
        *,
        init: bool = False,
        folderPath: str = "",
        extension: str = "",
        toSelect: str = "",
    ) -> int:
        """
        Initializes the treeview and handles
        any updates or switching between profiles

        Args:
            init: Used when initializing treeview for the first time, or with
                    each profile switch

            folderPath: New folder path, passed when initializing

            extension: Extension of files in the treeview, passed when initializing

            toSelect: id of item to select after updating

        Return number of files added
        """
        if init:
            self.mainFolder = folderPath
            self.ext = extension
        else:
            isOpen = {p for p in self.currFiles if self.item(p, "open")}
        for child in self.get_children():
            self.delete(child)
        self.currFiles.clear()
        # If no folder path means all profiles deleted so nothing to add
        if not (folderPath or self.mainFolder):
            self.save()
            return 0
        folder = Path(self.mainFolder)
        # Recursively add subfolders if flag is set or
        # there are files of specified extension in the tree
        if self.subfolders or len(list(folder.glob(f"**/*{self.ext}"))) > 0:
            self.AddSubfolders(folder)
        files = [Path(f) for f in os_sorted(folder.glob(f"*{self.ext}")) if f.is_file()]
        for file in files:
            self.insert("", "end", file.name, text=file.name, image=self.fileIco)
            self.currFiles[file.name] = str(file)
        if not init and isOpen:
            for toOpen in isOpen:
                self.item(toOpen, open=True)
        if toSelect and toSelect in self.currFiles:
            self.selection_set(toSelect)
            self.see(toSelect)
        self.save()
        return len(files)

    def AddSubfolders(self, path: Path, parent: str = "") -> None:
        """
        Recursively adds subfolders to the treeview
        and adds all the save files in them

        Args:
            path: Path object, originally the personal/game directory
                then called recursively with its subfolders

            parent: The id of the parent in the treeview.
                Initially '' which is the root, then it is the id
                of added subfolders to be able to add their subfolders
        """
        folders = [Path(f) for f in os_sorted(path.iterdir()) if f.is_dir()]
        for folder in folders:
            parentiid = self.insert(
                parent,
                "end",
                parent + folder.name,
                text=folder.name,
                image=self.folderIco,
            )
            self.currFiles[parentiid] = str(folder)
            self.AddSubfolders(folder, parentiid)
            files = [
                Path(f) for f in os_sorted(folder.glob(f"*{self.ext}")) if f.is_file()
            ]
            for file in files:
                parentiid2 = self.insert(
                    parentiid,
                    "end",
                    parentiid + file.name,
                    text=file.name,
                    image=self.fileIco,
                )
                self.currFiles[parentiid2] = str(file)

    def RenameFile(self, warn: bool = False) -> None:
        if warn and not messagebox.askyesno(
            "Renaming Game file",
            "The game may not recognize the file if you rename it\n\nDo you want to rename?",
        ):
            logging.warning("Game file name changed")
            return
        selection = self.selection()[0]
        newname = askstring(
            "New File Name",
            "Enter a new name for the file",
            parent=self.master.master,
            initialvalue=self.item(selection, "text"),
        )
        if not newname:
            return
        rename = Path(self.currFiles[selection])
        # If user didn't add extension add it only if selection is a file
        if not newname.endswith(self.ext) and rename.is_file():
            newname += self.ext
        toSelect = self.parent(selection) + newname
        renamed = rename.parent / newname
        if renamed.exists():
            if not messagebox.askyesno(
                "Already Exists",
                "File/Folder already exists, would you like to overwrite?",
            ):
                return
            if renamed.is_dir() and len(list(renamed.iterdir())) > 0:
                try:
                    rmtree(renamed)
                except OSError as e:
                    logging.error(f"Failed directory rename/delete {e.strerror}")
                    messagebox.showerror(
                        "Failed Overwrite", "Failed to overwrite folder."
                    )
                    return
        renamed = rename.replace(renamed)
        self.Update(toSelect=toSelect)

    def DeleteFile(self) -> None:
        if not messagebox.askyesno("Deleting File", "Are you sure you want to delete?"):
            return
        selection = self.selection()[0]
        parent = self.parent(selection)
        index = self.index(selection) - 1
        index = 1 if index < 0 else index
        deleted = Path(self.currFiles[selection])
        backup = self.backupFolder / (
            datetime.now().strftime("%Y_%m_%d_%Hhr_%Mmin_%Ss_") + deleted.name
        )
        try:
            if deleted.is_dir():
                copytree(deleted, backup)
            elif deleted.is_file():
                copy2(deleted, backup)
        except OSError as e:
            logging.error(f"Couldn't backup file {e.strerror}")
            messagebox.showerror(
                "FAILED BACKUP ERROR",
                "Couldn't backup file before deleting. Check log file.",
            )
            return
        try:
            if deleted.is_dir():
                rmtree(deleted)
            elif deleted.is_file():
                deleted.unlink()
        except OSError as e:
            logging.error(f"Couldn't delete file {e.strerror}")
            messagebox.showerror(
                "FAILED DELETE ERROR", "Couldn't delete. Check log file."
            )
            return
        if parent:
            self.selection_set(parent)
        elif len(self.get_children()) > 1:
            self.selection_set(self.get_children()[index])
        for child in self.get_children(selection):
            self.currFiles.pop(child)
        self.currFiles.pop(selection)
        self.delete(selection)
        self.save()
