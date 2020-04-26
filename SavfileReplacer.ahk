#include JSON.ahk
#Include SFR_Functions.ahk

/**
*Savefile Replacer 
*By GreenBat
*Version:
*	1.3.7 (Last updated 25/04/2020)
*	https://github.com/Green-Bat/Savefile-Replacer
*/
#Warn
#NoEnv
#NoTrayIcon
#SingleInstance, Ignore
ListLines, Off
SetBatchLines, -1
SetWorkingDir, % A_ScriptDir

settingsfile := FileOpen(A_ScriptDir "\settings.JSON" , "r")
if !(IsObject(settingsfile)){
	MsgBox, 16, Savefile Replacer, ERROR: Failed to load settings file! Please make sure it's in the same directory as the program's exe file.
	ExitApp
}
global settings := JSON.Load(settingsfile.Read())
settingsfile.Close()

SetTimer, CheckFiles, 1000 ; Timer to detect any changes the user might make to the folders manually.

ImageListID := IL_Create(2)
IL_Add(ImageListID, "shell32.dll", 1)
IL_Add(ImageListID, "shell32.dll", 4)
;**************************************************************************************************************************************************************************************
Gui, Main:New, +HwndMainHwnd, Savefile Replacer
Gui, Font, s11
Gui, Main:Add, Button, Default xp+30 yp+10 w100 h60 gadd_game, Add a game
Gui, Main:Add, Button, xp+120 yp wp hp gremove_game, Remove current game
Gui, Font
Gui, Main:Add, DDL, xp+145 yp+25 w135 vc_Dirs gchange_dirs
Gui, Font, s10
Gui, Main:Add, Text, xp yp-20 w150, Saved Games:
Gui, Font
; If any saved games exist, populate the DropDownList
if (settings.SavedDirs.Count()){
	for savedname in settings.SavedDirs{
		GuiControl,, c_Dirs, %savedname%
	}
}
GuiControl, Choose, c_Dirs, % settings.LastChosenGame ; Make the current choice in the DropDown be whatever the user chose last.
Gui, Main:Add, Text, xm yp+70 w450 r2 vptext, % "Current personal directory: " settings.pSaveDir
Gui, Main:Add, Text, xm yp+30 wp r2 vgtext, % "Current game directory: " settings.gSaveDir
Gui, Main:Add, TreeView, r19 xm yp+40 w220 -HScroll -Lines -Buttons +0x800 +0x1000 ImageList%ImageListID% vTVp
Gui, Main:Add, TreeView, r15 xp+250 yp wp-20 -HScroll -Lines +0x800 +0x1000 ImageList%ImageListID% vTVg
; Populate the TreeView with the files in the currently chosen personal/game directories, if they exist
if (settings.gSaveDir && settings.pSaveDir){
	UpdateTVg()
	UpdateTVp()
	TV_Modify(TV_GetNext())
	GuiControl, Focus, TVp
}
Gui, Font, s16
Gui, Main:Add, Button, xp-30 yp+20 w30 h30 greplace, =>
Gui, Main:Add, Button, xp yp+60 wp hp gcreate_backup, <=
Gui, Font
Gui, Main:Show, W470 H470
return

;*************************************************************************| G-LABELS |**************************************************************************************************

add_game: ; Adds a game and saves it
	; Let user choose the personal directory, if they cancel the dialog then return
	if !(newPersonalDir := SelectFolderEx(A_Desktop, "Select a directory that contains your own personal save files", MainHwnd))
		return
	; Let user choose the game directory, if they cancel the dialog then return
	if !(newGameDir := SelectFolderEx(A_Desktop, "Select the directory that contains the game's save files", MainHwnd))
		return

	Gui +OwnDialogs ; Makes any dialogs like, MsgBox, InputBox...etc, modal
	; Let the user choose the name that will be saved, if blank then return
	if !(SavedName := SaveDir(newGameDir, newPersonalDir))
		return
	; Update the DropDown and make whatever the user just saved be the current choice
	GuiControl,, c_Dirs, |
	for savedgame in settings.SavedDirs {
		GuiControl,, c_Dirs, % (savedgame == SavedName) ? SavedName "||" : savedgame
	}
	; Use AltSubmit to get the position of the currently chosen item in the DropDown and make it the LastChosenGame
	GuiControl, +AltSubmit, c_Dirs
	Gui, Main:Submit, NoHide
	settings.LastChosenGame := c_Dirs
	GuiControl, -AltSubmit, c_Dirs
	; Update the text and the TreeViews
	GuiControl, Text, ptext, % "Current personal directory: " settings.pSaveDir
	GuiControl, Text, gtext, % "Current game directory: " settings.gSaveDir
	UpdateTVg()
	UpdateTVp()
	return
;**************************************************************************************************************************************************************************************

remove_game: ; Deletes the currently selected game in the DropDown
	Gui, Main:Submit, NoHide
	settings.pSaveDir := settings.gSaveDir := settings.LastChosenGame := ""
	, settings.pCurrentFilePaths := settings.gCurrentFilePaths := {}
	settings.SavedDirs.Delete(c_Dirs)
	; Empty the DropDown and refill it again with the other saved games
	GuiControl,, c_Dirs, |
	for savedgame in settings.SavedDirs {
		GuiControl,, c_Dirs, %savedgame%
	}
	; Empty the TreeView
	Gui, TreeView, TVg
	TV_Delete()
	Gui, TreeView, TVp
	TV_Delete()
	; Update the the text
	GuiControl, Text, ptext, % "Current personal directory: "
	GuiControl, Text, gtext, % "Current game directory: "
	return
;**************************************************************************************************************************************************************************************

create_backup: ; Create a backup from the currently highlighted file in the game files TreeView
	Gui +OwnDialogs
	Gui, TreeView, TVg
	if !(TV_GetSelection()) { ; Return if nothing is highlighted
		MsgBox, 48, Savefile Replacer, Select a game file to backup
		return
	}
	TV_GetText(FileToBackup, TV_GetSelection()) ; Get the name of the file the user highlighted so it can be used to get the full path
	; Let the user choose the name of the backup file, if they cancel the dialog (i.e., ErrorLevel = 1), return
	Gui, TreeView, TVp
	TV_GetText(SubFolder, parentID := TV_GetSelection())
	Loop {
		InputBox, BackupName, Savefile Replacer, Choose backup name,, 200, 150
		childID := 0
		if !(SubFIsHighlighted := InStr(SubFolder, ".sgd")) { ; If a sub-folder is highlighted check if the chosen backup name already exists in the sub-folder and not in the main directory
			childID := TV_GetChild(parentID)
			Loop {
				(A_Index == 1) ? TV_GetText(ExistingName, childID) : TV_GetText(ExistingName, childID := TV_GetNext(childID))
				if (InStr(ExistingName, ".sgd") && BackupName == SubStr(ExistingName, 1, -4)){
					MsgBox, 52, Savefile Replacer, The name you chose already exists. Would you like to overwrite the file?
					IfMsgBox, Yes
						break
					else {
						BackupName := ""
						break
					}
				}
			} until !(childID)
		} else {
			Loop, % TV_GetCount() {
				(A_Index == 1) ? TV_GetText(ExistingName, childID) : TV_GetText(ExistingName, childID := TV_GetNext(childID))
				if ( InStr(ExistingName, ".sgd") && BackupName == SubStr(ExistingName, 1, -4)){
					MsgBox, 52, Savefile Replacer, The name you chose already exists. Would you like to overwrite the file?
					IfMsgBox, Yes
						break
					else {
						BackupName := ""
						break
					}
				}
			}
		}
	} until (BackupName || ErrorLevel)
	if (ErrorLevel == 1)
		return
	; If a subfolder is highlighted add the backup file to it instead of the root directory
	if !(SubFIsHighlighted){
		AddID := TV_Add(BackupName ".sgd", parentID, "Icon1")
		TV_GetText(BackupName, AddID)
		TV_GetText(prevName, TV_GetPrev(AddID))
		if (BackupName < prevName)
			AddID := TV_CustomSort(AddID, 1)
		else
			TV_Modify(AddID, "+Select +VisFirst")
		FileCopy, % settings.gCurrentFilePaths[FileToBackup], % settings.pCurrentFilePaths[AddID] := settings.pCurrentFilePaths[parentID] "\" BackupName, 1
	} else {	; Create a copy from the game file and put it in the current personal directory then update the personal file TreeView
		FileCopy, % settings.gCurrentFilePaths[FileToBackup], % settings.pSaveDir "\" BackupName ".sgd", 1
		UpdateTVp(BackupName . ".sgd")
	}
	SoundPlay, *-1
	GuiControl, Focus, TVp
	return
;**************************************************************************************************************************************************************************************

replace: ; Replace the currently highlighted file in the game file TreeView with the currently highlighted file in the personal file TreeView
	Gui +OwnDialogs
	Gui, TreeView, TVg
	if !(gID := TV_GetSelection()) {
		MsgBox, 48, Savefile Replacer, Select a game file to replace
		return
	}
	TV_GetText(FileToReplace, gID)
	Gui, TreeView, TVp
	TV_GetText(FileToReplaceWith, pID := TV_GetSelection())
	if !(pID && InStr(FileToReplaceWith, ".sgd", true)) {
		MsgBox, 48, Savefile Replacer, Select a personal file to replace with
		return
	}
	;Special Case for Batman: Arkahm Knight*******************************************************************************************
	if (InStr(FileToReplace, "BAK"))
		SpecialCaseAK(FileToReplace, pID)
	;**************************************************************************************************************************************
	else ; Creates a copy of the personal file, renames it and overwrites the selected game file then updates the game files TreeView
		FileCopy, % settings.pCurrentFilePaths[pID], % settings.gCurrentFilePaths[FileToReplace], 1
	SoundPlay, *-1
	UpdateTVg(FileToReplace)
	return
;**************************************************************************************************************************************************************************************

change_dirs: ; Runs when the user changes the DropDownList choice
	Gui, Main:Submit, NoHide ; Get the new choice of the DropDownList and update everything accordingly
	; AltSubmit used to get the current position of the choice then makes it the last chosen game
	GuiControl, +AltSubmit, c_Dirs
	GuiControlGet, ChosenNum,, c_Dirs
	GuiControl, -AltSubmit, c_Dirs
	if (ChosenNum == settings.LastChosenGame) ; If the user clicks on a game that was already chosen, do nothing
		return
	UpdateDirs(c_Dirs)
	settings.LastChosenGame := ChosenNum
	return
;**************************************************************************************************************************************************************************************

MainGuiClose:
	settingsfile := FileOpen(A_ScriptDir "\settings.JSON" , "w")
	if !(IsObject(settingsfile)){
		MsgBox, 16, Savefile Replacer, 
		( LTrim
		ERROR: Failed to load settings file! Please make sure it's in the correct directory.
		You can use Ctrl+Esc to force close the program, but any changes you made will not be saved.
		)
		return
	}
	settingsfile.Seek(0)
	settingsfile.Write((JSON.Dump(settings,, 4)))
	settingsfile.Close()
	ExitApp

#If WinActive("ahk_id " MainHwnd)
^Esc::ExitApp
#If
