#include JSON.ahk
#Include SFR_Functions.ahk

/**
*Savefile Replacer 
*By GreenBat
*Version:
*	1.4.17 (Last updated 28/12/2021)
*	https://github.com/Green-Bat/Savefile-Replacer
*/
#Warn
#NoEnv
#NoTrayIcon
#SingleInstance, Force
ListLines, Off
SetBatchLines, -1
SetWorkingDir, % A_ScriptDir

settingsfile := FileOpen(A_ScriptDir "\settings.JSON" , "r")
if !(IsObject(settingsfile)){
	MsgBox, 16, Savefile Replacer, ERROR: Failed to load settings file! Please make sure it's in the same directory as the program's exe file.
	ExitApp
}
global settings := JSON.Load(settingsfile.Read())
	, pCheckFilesObj := Func("pCheckFiles").Bind(settings.pSaveDir)
	, gCheckFilesObj := Func("gCheckFiles").Bind(settings.gSaveDir)
settingsfile.Close()
; Get the virtual left, top, width and height
SysGet, VirtualL, 76
SysGet, VirtualT, 77
SysGet, VirtualW, 78
SysGet, VirtualH, 79
; Do not allow the window to exceed the virtual dimensions of the screen
if ((settings.XCoord + 470) > (VirtualL + VirtualW))
	settings.XCoord := VirtualW - 470
else if (settings.XCoord < VirtualL)
	settings.XCoord := VirtualL
if ((settings.YCoord + 470) > (VirtualT + VirtualH))
	settings.YCoord := VirtualH - 470
else if (settings.YCoord < VirtualT)
	settings.YCoord := VirtualT

OnMessage(0x44, "CenterMsgBox") ; Center any MsgBox before it appears
SetTimer, % pCheckFilesObj, 1000 ; Timer to detect any changes the user might make to the folders manually.
SetTimer, % gCheckFilesObj, 1000

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
Gui, Main:Add, Text, xm yp+70 w450 r2 vptext gopenfolder, % "Current personal directory: " settings.pSaveDir
Gui, Main:Add, Text, xm yp+30 wp r2 vgtext gopenfolder, % "Current game directory: " settings.gSaveDir
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
Gui, Main:Add, Button, xp-30 yp+20 w30 h30 HwndreplaceHwnd greplace, =>
Gui, Main:Add, Button, xp yp+60 wp hp HwndbackupHwnd gcreate_backup, <=
Gui, Font
Gui, Main:Show, % "W470 H470 X" settings.XCoord " Y" settings.YCoord
return

;*************************************************************************| G-LABELS |**************************************************************************************************

add_game: ; Adds a game and saves it
	Gui +OwnDialogs ; Makes any dialogs like, MsgBox, InputBox...etc, modal
	; Let user choose the personal directory, if they cancel the dialog then return
	Loop {
		if !(newPersonalDir := SelectFolderEx(settings.pSaveDir ? settings.pSaveDir : A_Desktop, "Select a directory that contains your own personal save files", MainHwnd))
			return
		; Let user choose the game directory, if they cancel the dialog then return
		if !(newGameDir := SelectFolderEx(settings.gSaveDir ? settings.gSaveDir : A_Desktop, "Select the directory that contains the game's save files", MainHwnd))
			return
		if (newGameDir == newPersonalDir){
			MsgBox, 48, Savefile Replacer, % "The personal directory and the game directory cannot be the same."
		} else {
			break
		}
	}

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
	Save()
	return
;**************************************************************************************************************************************************************************************

remove_game: ; Deletes the currently selected game in the DropDown
	Gui +OwnDialogs
	Gui, Main:Submit, NoHide
	if !(c_Dirs){
		MsgBox, 48, No Games, You currently have no games to remove
		return
	}
	MsgBox, 308, DELETING GAME!!!, % "Are you sure you want to remove """ c_Dirs """ from your current games list?"
	IfMsgBox, No
		return
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
	GuiControl, Choose, c_Dirs, |1
	Save()
	return
;**************************************************************************************************************************************************************************************

create_backup: ; Create a backup from the currently highlighted file in the game files TreeView
	SetTimer, % pCheckFilesObj, Off
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
	WinGetPos, x, y, w, h, ahk_id %MainHwnd%
	Loop {
		InputBox, BackupName, Savefile Replacer, Choose backup name,, 200, 150, x + ((w/2) - 100), y + ((h/2) - 75)
		if (ErrorLevel)
			break
		childID := 0
		if !(SubFIsHighlighted := InStr(SubFolder, ".sgd")) { ; If a sub-folder is highlighted check if the chosen backup name already exists in the sub-folder and not in the main directory
			childID := TV_GetChild(parentID)
			Loop {
				(A_Index == 1) ? TV_GetText(ExistingName, childID) : TV_GetText(ExistingName, childID := TV_GetNext(childID))
				if (InStr(ExistingName, ".sgd") && BackupName = SubStr(ExistingName, 1, -4)){
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
				TV_GetText(ExistingName, childID := TV_GetNext(childID))
				if ( InStr(ExistingName, ".sgd") && BackupName = SubStr(ExistingName, 1, -4)){
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
	} until (BackupName)
	if (ErrorLevel == 1)
		return

	if (InStr(FileToBackup, "BAK"))
		FileToBackup := GetUpToDateFile(SubStr(FileToBackup,1,10))
	; If a subfolder is highlighted add the backup file to it instead of the root directory
	if (!SubFIsHighlighted && SubFolder){
		FileCopy, % settings.gCurrentFilePaths[FileToBackup], % settings.pCurrentFilePaths[parentID] "\" BackupName . ".sgd", 1
		UpdateFolder(settings.pCurrentFilePaths[parentID], parentID, BackupName . ".sgd")
		Sleep, 1000
		SetTimer, % pCheckFilesObj, On
	} else {	; Create a copy from the game file and put it in the current personal directory then update the personal file TreeView
		FileCopy, % settings.gCurrentFilePaths[FileToBackup], % settings.pSaveDir "\" BackupName ".sgd", 1
		UpdateTVp(BackupName . ".sgd")
	}
	return
;**************************************************************************************************************************************************************************************

replace: ; Replace the currently highlighted file in the game file TreeView with the currently highlighted file in the personal file TreeView
	SetTimer, % gCheckFilesObj, Off
	Gui +OwnDialogs
	Gui, TreeView, TVg
	if !(gID := TV_GetSelection()) {
		MsgBox, 48, Savefile Replacer, Select a game file to replace
		return
	}
	TV_GetText(FileToReplace, gID)
	Gui, TreeView, TVp
	TV_GetText(FileToReplaceWith, pID := TV_GetSelection())
	if !(pID && InStr(FileToReplaceWith, ".sgd") && !(InStr(FileExist(settings.pCurrentFilePaths[pID]), "D"))) {
		MsgBox, 48, Savefile Replacer, Select a personal file to replace with
		return
	}
	;Special Case for Batman: Arkahm Knight*******************************************************************************************
	if (InStr(FileToReplace, "BAK"))
		SpecialCaseAK(FileToReplace, settings.pCurrentFilePaths[pID])
	;**************************************************************************************************************************************
	else { ; Creates a copy of the personal file, renames it and overwrites the selected game file then updates the game files TreeView
		try
			FileCopy, % settings.pCurrentFilePaths[pID], % settings.gCurrentFilePaths[FileToReplace], 1
		catch e {
			MsgBox, 48, , % e.Message " " e.What
		}
	}
	UpdateTVg(FileToReplace)
	return
;**************************************************************************************************************************************************************************************

change_dirs: ; Runs when the user changes the DropDownList choice
	Critical
	Gui, Main:Submit, NoHide ; Get the new choice of the DropDownList and update everything accordingly
	; AltSubmit used to get the current position of the choice then makes it the last chosen game
	GuiControl, +AltSubmit, c_Dirs
	GuiControlGet, ChosenNum,, c_Dirs
	GuiControl, -AltSubmit, c_Dirs
	if (ChosenNum == settings.LastChosenGame) ; If the user clicks on a game that was already chosen, do nothing
		return
	UpdateDirs(c_Dirs)
	settings.LastChosenGame := ChosenNum
	Save()
	return
;**************************************************************************************************************************************************************************************

openfolder: ; Open the folder that the user double clicks on
	if (A_GuiEvent != "DoubleClick")
		return
	GuiControlGet, folder,, % A_GuiControl
	folder := SubStr(folder, InStr(folder, ":")+2)
	Run, % folder
	return
;**************************************************************************************************************************************************************************************

MainGuiClose:
	Save()
	ExitApp

#If WinActive("ahk_id " MainHwnd)
^Esc::ExitApp
#If
; Dev stuff
;!r::Reload
;!s::UpdateTVp("dd")
