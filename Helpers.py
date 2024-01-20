from pathlib import Path
import shutil
from datetime import datetime
from collections import defaultdict


def GetExt(p: Path | str) -> str:
    """Gets the most common extension in a given directory"""
    if isinstance(p, str):
        p = Path(p)
        if not p.exists():
            raise FileNotFoundError
    # if a file is given return its extension
    if p.is_file():
        return p.suffix

    exts = defaultdict(int)
    for file in p.iterdir():
        if file.is_file():
            exts[file.suffix] += 1

    return max(exts, key=exts.get) if exts else ""


def AKReplace(src: Path | str, dst: Path | str, settings):
    """
    Special replace function for Batman: Arkham Knight.
    Replaces the game's file and all its backups
    """
    if isinstance(src, str):
        src = Path(src)
    if isinstance(dst, str):
        dst = Path(dst)
    for i in range(3):
        file = f"{dst.stem[0:-1]}{i}.sgd"
        if file in settings["CurrFilesG"]:
            try:
                shutil.copy2(src, dst.parent / file)
            except OSError:
                raise


def AKBackup(src: Path | str, dst: Path | str, settings):
    """
    Special backup function for Batman: Arkham Knight.
    Uses the most up to date file out of the game's backups
    """
    if isinstance(src, str):
        src = Path(src)
    if isinstance(dst, str):
        dst = Path(dst)

    filetimes = {}
    for i in range(3):
        file = f"{src.stem[0:-1]}{i}.sgd"
        if file in settings["CurrFilesG"]:
            src = src.parent / file
            filetimes[file] = datetime.fromtimestamp(src.stat().st_mtime)
    file = max(filetimes, key=filetimes.get)
    try:
        shutil.copy2(src.parent / file, dst)
    except OSError:
        raise
