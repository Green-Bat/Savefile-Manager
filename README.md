# Savefile-Manager
A program to help manage savefiles (backup/replace), originally made for the Batman: Arkham series, but can now be used with any type of file or folders.

## How to Use:

## Options
- ### Add
  - A popup window will appear asking you for the name of the profile, your own personal saves folder, the game's saves folder, and the file extension for the game's save files.\
    If dealing with folders, or files with no extension, use a '*' for the extension choice.

  - When choosing the GAME'S savefiles folder, if you're not sure where this is, check PCGamingWiki: http://pcgamingwiki.com/

- ### Edit
    Edit the current profile.

- ### Remove
    Remove the current profile.

---
## Backup & Replace
- ## <=
    The Backup Button:\
    You choose a file/folder from the game files list (on the right) 
    then click the button. You then enter the name you want for your backup file/folder.\
    \
    If a sub-folder is highlighted the backup file will go in the sub-folder instead of the main folder.

- ## =>
    The Replace Button:\
    You choose a file/folder from your personal files list (on the left) and a 
    file/folder from the game files list (on the right) and then click the button. It will overwrite* 
    the game's file/folder.\
    A backup of the replaced file will be created in the config folder under /backups.

---
## Context Menu
- ## Rename
    Allows you to rename files/folders
- ## Delete
    Delete a file/folder, the program will creat a backup copy of any deleted file/folder under in the config folder under /backups/Deleted
---

*Specifically for Batman: Arkham Knight it will also overwrite any of the game's backup savefiles 
for that specific slot.
For example: if you replace BAK1Save0x0.sgd it will also overwrite BAK1Save0x1.sgd and BAK1Save0x2.sgd

*When backing up a savefile for Arkham Knight it does not matter which one you choose, 
the program will automatically choose the most recent one out of the available backups.

## \*Important Note
If you're using Steam, it is recommended to disable steam cloud saves as they have been known to cause some issues.