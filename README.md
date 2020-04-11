# Savefile-Replacer
A program to help manage savefiles (backup/replace), specifically made for the Batman: Arkham series, but it can be repurposed since it's just a glorified copy-paste program.

## How to Use:

Click `Add a game`, which will then prompt you to choose a folder which will be your own personal folder that stores backedup savefiles, you will then choose the folder that contains the game's savefiles. Then you choose the name you want it to be saved as.

`Remove current game` will remove the game you currently have selected.

`=>` is the replace button. You choose a file from your personal files list (on the left) and a file from the game files list (on the right) and then click the button. It will overwrite* the game file with whatever you chose from your personal files.

`<=` is the backup button. You choose a file from the game files list (on the right) then click the button. You then enter the name you want for your backup file.
If a sub-folder is highlighted the backup file will go in the sub-folder instead of the
main folder.

\*Specifically for Batman: Arkham Knight it will also overwrite any of the game's backup savefiles for that specific slot.\
For example: if you replace `BAK1Save0x0.sgd` it will also overwrite `BAK1Save0x1.sgd` and `BAK1Save0x2.sgd`

## \*\*Important Note
Keep the main exe and the `settings.JSON` file in the same directory.\
If you want to move the program somewhere else create a shortcut and move that.

### Kill-Switch:
Ctrl+Esc will terminate the program without saving any settings.
