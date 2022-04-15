# Savefile-Manager
A program to help manage savefiles (backup/replace), originally made for the Batman: Arkham series, but can now be used with any type of file.

## How to Use:

## Options
### Add
- A popup window will appear asking you for the name of the profile, your own personal saves folder, and the game's saves folder

- When choosing GAME'S savefiles folder, if you're not sure where this is, check PCGamingWiki: http://pcgamingwiki.com/

### Edit
Allows you to edit the current profile

### Remove
Removes the profile you currently have selected.

---

## =>
is the replace button. You choose a file from your personal files list (on the left) and a 
file from the game files list (on the right) and then click the button. It will overwrite* 
the game file with whatever you chose from your personal files.

## <=
is the backup button. You choose a file from the game files list (on the right) 
then click the button. You then enter the name you want for your backup file. 

If a sub-folder is highlighted the backup file will go in the sub-folder instead of the main folder.

---

*Specifically for Batman: Arkham Knight it will also overwrite any of the game's backup savefiles 
for that specific slot.
For example: if you replace BAK1Save0x0.sgd it will also overwrite BAK1Save0x1.sgd and BAK1Save0x2.sgd

*When backing up a savefile for Arkham Knight it does not matter which one you choose, 
the program will automatically choose the most recent one.

## \*Important Note
If you're using Steam, it is recommended to disable steam cloud saves as they have been known to cause some issues.