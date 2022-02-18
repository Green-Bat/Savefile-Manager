from pathlib import Path


def GetExt(p: Path) -> str:
    """Gets the most common extension in a given directory"""
    if not p.is_dir():
        return

    exts = {}
    for file in p.iterdir():
        if file.is_dir():
            continue
        if not exts.get(file.suffix):
            exts[file.suffix] = 1
        else:
            exts[file.suffix] += 1
    return max(exts, key=exts.get)
