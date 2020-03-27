#Include SFR_Functions.ahk
#include JSON.ahk

/**
*Savefile Replacer 
*By GreenBat
*Version:
*	1.1 (Last updated 27/03/2020)
*/
#Warn
#NoEnv
#NoTrayIcon
SetWorkingDir, % A_ScriptDir
SetBatchLines, -1

settingsfile := FileOpen(A_ScriptDir "\settings.JSON" , "r")
if !(IsObject(settingsfile)){
	MsgBox, 16, Savefile Replacer, ERROR: Failed to load settings file! Please make sure it's in the same directory as the program's exe file.
	ExitApp
}
settings := JSON.Load(settingsfile.Read())
settingsfile.Close()

SetTimer, CheckFiles, 1000 ; Timer to detect any changes the user might make to the folders manually.

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
Gui, Main:Add, Text, xm yp+30 w450 r2 vgtext, % "Current game directory: " settings.gSaveDir
Gui, Main:Add, ListView, r18 xm yp+40 w220 -Hdr -Multi  +LV0x400 +LV0x4000 vLVp, Personal Files
; Populate the ListView with the files in the currently chosen personal/game directories, if they exist
if (settings.pSaveDir){
	Loop, Files, % settings.pSaveDir "\*.sgd", R  ; Get all files in the directory, including subfolders
	{
		LV_Add("", A_LoopFileNAme)
		settings.pCurrentFilePaths[A_LoopFileName] := A_LoopFileLongPath ; Save the file paths and use their names as keys
	}
}
LV_ModifyCol(1, 195)
Gui, Main:Add, ListView, r15 xp+250 yp w200 -Hdr -Multi +LV0x400 +LV0x4000 vLVg, Game Files
if (settings.gSaveDir){
	Loop, Files, % settings.gSaveDir "\*.sgd"
	{
		LV_Add("", A_LoopFileNAme)
		settings.gCurrentFilePaths[A_LoopFileName] := A_LoopFileLongPath
	}
}
LV_ModifyCol(1, 195)
Gui, Font, s16
Gui, Main:Add, Button, xp-30 yp+60 w30 h30 gcreate_backup, <=
Gui, Main:Add, Button, xp yp+60 wp hp greplace, =>
Gui, Font
Gui, Main:Show, W470 H470
return

;***********************************************************************************| G-LABELS |*****************************************************************************************************

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
	; Update the directories in the settings
	settings.pSaveDir := newPersonalDir
	settings.gSaveDir := newGameDir
	; Update the DropDown and make whatever the user just saved be the current choice
	GuiControl,, c_Dirs, |
	for savedgame in settings.SavedDirs {
		GuiControl,, c_Dirs, % (savedgame == SavedName) ? SavedName "||" : savedgame
	}
	; Use AltSubmit to get the position of the currently chosen item in the DropDown and make it the LastChosenGame
	GuiControl, +AltSubmit, c_Dirs
	GuiControlGet, savednum,, c_Dirs
	settings.LastChosenGame := savednum
	GuiControl, -AltSubmit, c_Dirs
	; Update the text and the ListViews
	GuiControl, Text, ptext, % "Current personal directory: " settings.pSaveDir
	GuiControl, Text, gtext, % "Current game directory: " settings.gSaveDir
	UpdateLVg()
	UpdateLVp()
	return
;**************************************************************************************************************************************************************************************

remove_game: ; Deletes the currently selected game in the DropDown
	GuiControlGet, GameToRemove,, c_Dirs
	settings.pSaveDir := ""
	settings.gSaveDir := ""
	settings.SavedDirs.Delete(GameToRemove)
	; Empty the DropDown and refill it again with the other saved games
	GuiControl,, c_Dirs, |
	for savedgame in settings.SavedDirs {
		GuiControl,, c_Dirs, %savedgame%
	}
	; Empty the ListView
	Gui, ListView, LVg
	LV_Delete()
	Gui, ListView, LVp
	LV_Delete()
	; Update the the text and the LastChosenGame
	GuiControl, Text, ptext, % "Current personal directory: " settings.pSaveDir
	GuiControl, Text, gtext, % "Current game directory: " settings.gSaveDir
	settings.LastChosenGame := ""
	return
;**************************************************************************************************************************************************************************************

create_backup: ; Create a backup from the currently highlighted file in the game files ListView
	Gui, ListView, LVg
	if !(LV_GetNext()) { ; Return if nothing is highlighted
		MsgBox, 48, Savefile Replacer, Select a game file to backup
		return
	}
	LV_GetText(FileToBackup, LV_GetNext()) ; Get the name of the file the user highlighted so it can be used to get the full path
	; Let the user choose the name of the backup file, if they cancel the dialog (i.e., ErrorLevel = 1), return
	Gui, ListView, LVp
	loop {
		InputBox, BackupName, Savefile Replacer, Choose backup name,, 200, 150
		Loop, % LV_GetCount() {
			LV_GetText(ExistingName, A_Index)
			if (BackupName == SubStr(ExistingName, 1, -4)){
				MsgBox, 52, Savefile Replacer, The name you chose already exists. Would you like to overwrite the file?
				IfMsgBox, Yes
					break
				else {
					BackupName := ""
					break
				}
			}
		}
	} until (BackupName || ErrorLevel)
	if (ErrorLevel == 1)
		return
	; Create a copy from the game file and put it in the current personal directory then update the personal file ListView
	FileCopy, % settings.gCurrentFilePaths[FileToBackup], % settings.pCurrentFilePaths[BackupName ".sgd"] := settings.pSaveDir "\" BackupName ".sgd", 1
	UpdateLVp()
	return
;**************************************************************************************************************************************************************************************

replace: ; Replace the currently highlighted file in the game file ListView with the currently highlighted file in the personal file ListView
	Gui, ListView, LVg
	if !(SelectedRow := LV_GetNext()) {
		MsgBox, 48, Savefile Replacer, Select a game file to replace
		return
	}
	LV_GetText(FileToReplace, SelectedRow)
	Gui, ListView, LVp
	if !(LV_GetNext()) {
		MsgBox, 48, Savefile Replacer, Select a personal file to replace with
		return
	}
	LV_GetText(FileToReplaceWith, LV_GetNext())
	;Special Case for Batman: Arkahm Knight*******************************************************************************************
	if (InStr(FileToReplace, "BAK"))
		SpecialCaseAK(FileToReplace, FileToReplaceWith)
	;**************************************************************************************************************************************
	else ; Creates a copy of the personal file, renames it and overwrites the selected game file then updates the game files ListView
		FileCopy, % settings.pCurrentFilePaths[FileToReplaceWith], % settings.gCurrentFilePaths[FileToReplace], 1
	UpdateLVg(SelectedRow)
	return
;**************************************************************************************************************************************************************************************

change_dirs: ; Runs when the user changes the DropDownList choice
	GuiControlGet, newDir,, c_Dirs ; Get the new choice of the DropDownList and update everything accordingly 
	UpdateDirs(newDir)
	; AltSubmit used to get the current position of the choice then makes it the last chosen game
	GuiControl, +AltSubmit, c_Dirs
	GuiControlGet, chosennum,, c_Dirs
	settings.LastChosenGame := chosennum
	GuiControl, -AltSubmit, c_Dirs
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

^Esc::ExitApp
