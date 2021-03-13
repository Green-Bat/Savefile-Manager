; ==================================================================================================================================
; Function taken from https://www.autohotkey.com/boards/viewtopic.php?t=18939&p=302675
; Shows a dialog to select a folder.
; Depending on the OS version the function will use either the built-in FileSelectFolder command (XP and previous)
; or the Common Item Dialog (Vista and later).
; Parameter:
;     StartingFolder -  the full path of a folder which will be preselected.
;     Prompt         -  a text used as window title (Common Item Dialog) or as text displayed withing the dialog.
;     ----------------  Common Item Dialog only:
;     OwnerHwnd      -  HWND of the Gui which owns the dialog. If you pass a valid HWND the dialog will become modal.
;     BtnLabel       -  a text to be used as caption for the apply button.
;  Return values:
;     On success the function returns the full path of selected folder; otherwise it returns an empty string.
; MSDN:
;     Common Item Dialog -> msdn.microsoft.com/en-us/library/bb776913%28v=vs.85%29.aspx
;     IFileDialog        -> msdn.microsoft.com/en-us/library/bb775966%28v=vs.85%29.aspx
;     IShellItem         -> msdn.microsoft.com/en-us/library/bb761140%28v=vs.85%29.aspx
; ==================================================================================================================================
SelectFolderEx(StartingFolder := "", Prompt := "", OwnerHwnd := 0, OkBtnLabel := "") {
	Local ShellItem:= StrPtr:= FolderItem:= ""
	Static OsVersion := DllCall("GetVersion", "UChar")
		, IID_IShellItem := 0
		, InitIID := VarSetCapacity(IID_IShellItem, 16, 0)
				  & DllCall("Ole32.dll\IIDFromString", "WStr", "{43826d1e-e718-42ee-bc55-a1e261c37bfe}", "Ptr", &IID_IShellItem)
		, Show := A_PtrSize * 3
		, SetOptions := A_PtrSize * 9
		, SetFolder := A_PtrSize * 12
		, SetTitle := A_PtrSize * 17
		, SetOkButtonLabel := A_PtrSize * 18
		, GetResult := A_PtrSize * 20
	SelectedFolder := ""
	If (OsVersion < 6) { ; IFileDialog requires Win Vista+, so revert to FileSelectFolder
	  FileSelectFolder, SelectedFolder, *%StartingFolder%, 3, %Prompt%
	  Return SelectedFolder
	}
	OwnerHwnd := DllCall("IsWindow", "Ptr", OwnerHwnd, "UInt") ? OwnerHwnd : 0
	If !(FileDialog := ComObjCreate("{DC1C5A9C-E88A-4dde-A5A1-60F82A20AEF7}", "{42f85136-db7e-439c-85f1-e4075d135fc8}"))
	  Return ""
	VTBL := NumGet(FileDialog + 0, "UPtr")
	; FOS_CREATEPROMPT | FOS_NOCHANGEDIR | FOS_PICKFOLDERS
	DllCall(NumGet(VTBL + SetOptions, "UPtr"), "Ptr", FileDialog, "UInt", 0x00002028, "UInt")
	If (StartingFolder <> "")
	  If !DllCall("Shell32.dll\SHCreateItemFromParsingName", "WStr", StartingFolder, "Ptr", 0, "Ptr", &IID_IShellItem, "PtrP", FolderItem)
		 DllCall(NumGet(VTBL + SetFolder, "UPtr"), "Ptr", FileDialog, "Ptr", FolderItem, "UInt")
	If (Prompt <> "")
	  DllCall(NumGet(VTBL + SetTitle, "UPtr"), "Ptr", FileDialog, "WStr", Prompt, "UInt")
	If (OkBtnLabel <> "")
	  DllCall(NumGet(VTBL + SetOkButtonLabel, "UPtr"), "Ptr", FileDialog, "WStr", OkBtnLabel, "UInt")
	If !DllCall(NumGet(VTBL + Show, "UPtr"), "Ptr", FileDialog, "Ptr", OwnerHwnd, "UInt") {
	  If !DllCall(NumGet(VTBL + GetResult, "UPtr"), "Ptr", FileDialog, "PtrP", ShellItem, "UInt") {
		 GetDisplayName := NumGet(NumGet(ShellItem + 0, "UPtr"), A_PtrSize * 5, "UPtr")
		 If !DllCall(GetDisplayName, "Ptr", ShellItem, "UInt", 0x80028000, "PtrP", StrPtr) ; SIGDN_DESKTOPABSOLUTEPARSING
			SelectedFolder := StrGet(StrPtr, "UTF-16"), DllCall("Ole32.dll\CoTaskMemFree", "Ptr", StrPtr)
		 ObjRelease(ShellItem)
		}  
	}
	If (FolderItem)
	  ObjRelease(FolderItem)
	ObjRelease(FileDialog)
	Return SelectedFolder
}
; ==================================================================================================================================

UpdateTVg(FileToReplace:=""){ ; Updates the TreeView for the game directory
	IDToSelect := ""
	While (settings.gCurrentFilePaths.Count()) { ; delete all the current file paths
		for l in settings.gCurrentFilePaths
			settings.gCurrentFilePaths.Delete(l)
	}
	; Empty the TreeView
	Gui, TreeView, TVg
	if !(FileToReplace)
		TV_GetText(FileToReplace, TV_GetSelection())
	TV_Delete()
	; Refill the TreeView with the files of the current directory and store their full paths
	GuiControl, -Redraw, TVg ; for performance purposes
	Loop, Files, % settings.gSaveDir "\*.sgd"  ; Get all files in the directory, including subfolders
	{
		AddedID := TV_Add(A_LoopFileName,, "Icon1")
		, settings.gCurrentFilePaths[A_LoopFileName] := A_LoopFileLongPath ; Save the file paths and use their names as keys
		if (A_LoopFileName == FileToReplace) ; Get id of the game save to have to be selected after the TreeView is drawn
			IDToSelect := AddedID
	}
	GuiControl, +Redraw, TVg
	if (FileToReplace && IDToSelect){
		TV_Modify(IDToSelect, "+Select")
		Sleep, 1000
		SetTimer, % gCheckFilesObj, On
	} else {
		TV_Modify(TV_GetNext())
	}
}
; ==================================================================================================================================

UpdateTVp(BackupName:=""){ ; Updates the TreeView for the personal directory
	IDToSelect := ""
	While (settings.pCurrentFilePaths.Count()) {
		for l in settings.pCurrentFilePaths
			settings.pCurrentFilePaths.Delete(l)
	}
	Gui, TreeView, TVp
	TV_Delete()
	GuiControl, -Redraw, TVp
	AddSubfolders(settings.pSaveDir)
	Loop, Files, % settings.pSaveDir "\*.sgd"
	{
		AddedID := TV_Add(A_LoopFileName,, "Icon1")
		, settings.pCurrentFilePaths[AddedID] := A_LoopFileLongPath ; Save the file paths and use their IDs as keys
		if (A_LoopFileName == BackupName) ; Get id of the file to have it be selected after the TreeView is drawn
			IDToSelect := AddedID
	}
	GuiControl, +Redraw, TVp
	if (BackupName){
		TV_Modify(IDToSelect, "+Select +VisFirst" )
		GuiControl, Focus, TVp
		Sleep, 1000
		SetTimer, % pCheckFilesObj, On
	} else {
		TV_Modify(TV_GetNext())
	}
}

AddSubfolders(Folder, Parent:=0){
	Loop, Files, % Folder "\*.*", D
	{
		SubfolderID := TV_Add(A_LoopFileName, Parent, "Icon2")
		, settings.pCurrentFilePaths[SubfolderID] := A_LoopFileLongPath
		; Recursively add each subfolder and it's contents to the tree
		AddSubfolders(A_LoopFileLongPath, SubfolderID)
		Loop, Files, % A_LoopFileLongPath "\*.sgd"
		{
			AddedID := TV_Add(A_LoopFileName, SubfolderID, "Icon1")
			, settings.pCurrentFilePaths[AddedID] := A_LoopFileLongPath			
		}
	}
}
; ==================================================================================================================================

UpdateFolder(Folder, FolderID:="", FileName:=""){ ; Updates a specific folder
	Parent := 0
	if (FolderID){
		Parent := FolderID
	} else {
		; Get the ID of the folder
		for ID, path in settings.pCurrentFilePaths {
			if (Folder == path)
				Parent := ID
		}
	}
	if !(Parent)
		return
	StartingID := TV_GetChild(Parent)

	; Delete all of its children and delete it from the settings
	while(StartingID){
		settings.pCurrentFilePaths.Delete(StartingID)
		OldID := StartingID
		, StartingID := TV_GetNext(StartingID)
		TV_Delete(OldID)
	}
	; Readd everything
	Loop, Files, % Folder "\*.*", D
		settings.pCurrentFilePaths[TV_Add(A_LoopFileName, Parent, "Icon2")] := A_LoopFileLongPath
	Loop, Files, % Folder "\*.sgd"
	{
		AddedID := TV_Add(A_LoopFileName, Parent, "Icon1")
		settings.pCurrentFilePaths[AddedID] := A_LoopFileLongPath
		if (FileName == A_LoopFileName)
			IDToSelect := AddedID
	}

	if (FileName){
		TV_Modify(IDToSelect, "+Select +VisFirst" )
		GuiControl, Focus, TVp
	} else {
		; Expand the folder and select it after everything is done
		TV_Modify(Parent, "+Select +Expand")
	}
	Sleep, 700
}
; ==================================================================================================================================

UpdateDirs(key){ ; Function that is called when the user chooses an option in the saved games DropDownList
	global pCheckFilesObj, gCheckFilesObj
	; Takes the choice the user made as a parameter to use to retrieve the path to the saved directories
	settings.gSaveDir := settings.SavedDirs[key][1]
	, settings.pSaveDir := settings.SavedDirs[key][2]
	; Update relevant text then update TreeViews
	GuiControl, Text, ptext, % "Current personal directory: " settings.pSaveDir
	GuiControl, Text, gtext, % "Current game directory: " settings.gSaveDir
	UpdateTVg()
	UpdateTVp()
	SetTimer, % pCheckFilesObj, Off
	SetTimer, % gCheckFilesObj, Off
	pCheckFilesObj := Func("pCheckFiles").Bind(settings.pSaveDir)
	, gCheckFilesObj := Func("gCheckFiles").Bind(settings.gSaveDir)
	SetTimer, % pCheckFilesObj, 1000 
	SetTimer, % gCheckFilesObj, 1000
}
; ==================================================================================================================================

gCheckFiles(Folder){
	gOldTime := A_Now ; Get the current time to compare it to the last modified time of the folders
	Gui, Main:Default ; Ensures the corrct gui window will be acted on when the update functions are called

	FileGetTime, gNewTime, % Folder
	if ((gNewTime -= gOldTime, DHMS) > -2)
		UpdateTVg()
}

pCheckFiles(Folder){
	pOldTime := A_Now ; Get the current time to compare it to the last modified time of the folders
	Gui, Main:Default ; Ensures the corrct gui window will be acted on when the update functions are called

	Loop, Files, % Folder "\*.*", D
	{
		FileGetTime, pNewTIme, % A_LoopFileLongPath
		if ((pNewTime -= pOldTIme, DHMS) > -2){
			UpdateFolder(A_LoopFileLongPath)
		}
		pCheckFiles(A_LoopFileLongPath) ; Check the last modified time for all subfolders up to any depth
		pOldTime := A_Now
	}

	FileGetTime, pNewTime, % Folder
	if ((pNewTime -= pOldTime, DHMS) > -2)
		UpdateTVp()
}
; ==================================================================================================================================

SaveDir(gdir, pdir){ ; takes currently selected game and personal directories as parameters
	global MainHwnd
	Gui, Main:+OwnDialogs
	WinGetPos, x1, y1, w1, h1, ahk_id %MainHwnd%
	loop {
		InputBox, name, Savefile Replacer, Name the directory,, 200, 150, x1 + ((w1/2) - 100), y1 + ((h1/2) - 75)
		if (ErrorLevel)
			break
		; check if the name is already saved and warn the user (not case sensitive)
		if (settings.SavedDirs.HasKey(name)) {
			MsgBox, 48, Savefile Replacer, % "The name: """ name """ already exists please choose another one."
			name := ""
			continue
		}
	} until (name)
	if (ErrorLevel == 1)
		return ""
	; Update the directories in the settings
	settings.gSaveDir := gdir
	, settings.pSaveDir := pdir
	settings.SavedDirs[name] := [gdir, pdir] ; Use the name as a key with it's value being a small array that holds both directories
	return name
}
; ==================================================================================================================================

Save(){
	global MainHwnd, settingsfile
	settingsfile := FileOpen(A_ScriptDir "\settings.JSON" , "w")
	if !(IsObject(settingsfile)){
		MsgBox, 16, Savefile Replacer, 
		( LTrim
		ERROR: Failed to load settings file! Please make sure it's in the correct directory.
		You can use Ctrl+Esc to force close the program.
		)
		return
	}
	WinGetPos, GuiX, GuiY,,, ahk_id %MainHwnd%
	settings.XCoord := GuiX, settings.YCoord := GuiY
	settingsfile.Seek(0)
	settingsfile.Write((JSON.Dump(settings,, 4)))
	settingsfile.Close()
}
; ==================================================================================================================================

CenterMsgBox(P){
	global MainHwnd
	if (P == 1027){
		Process, Exist ; Get the PID of program, which is set to ErrorLevel
		DetectHiddenWindows, On
		WinGetPos, x1, y1, w1, h1, ahk_id %MainHwnd%
		if WinExist("ahk_class #32770 ahk_pid " ErrorLevel){
			WinGetPos,,, w2, h2 ; Get dimensions of the MsgBox
			WinMove, x1 + ((w1/2) - (w2/2)), y1 + ((h1/2) - (h2/2))
		}
	}
	DetectHiddenWindows, Off
}
; ====================================================| - ARKHAM KNIGHT SPECIAL CASE - |==============================================================================

SpecialCaseAK(FileName, FileToReplaceWith){
	if (InStr(FileName, "0x")){
		if (settings.gCurrentFilePaths.HasKey("BAK1Save0x0.sgd"))
			FileCopy, % FileToReplaceWith, % settings.gCurrentFilePaths["BAK1Save0x0.sgd"], 1
		if (settings.gCurrentFilePaths.HasKey("BAK1Save0x1.sgd"))
			FileCopy, % FileToReplaceWith, % settings.gCurrentFilePaths["BAK1Save0x1.sgd"], 1
		if (settings.gCurrentFilePaths.HasKey("BAK1Save0x2.sgd"))
			FileCopy, % FileToReplaceWith, % settings.gCurrentFilePaths["BAK1Save0x2.sgd"], 1
	} else if (InStr(FileName, "1x")){
		if (settings.gCurrentFilePaths.HasKey("BAK1Save1x0.sgd"))
			FileCopy, % FileToReplaceWith, % settings.gCurrentFilePaths["BAK1Save1x0.sgd"], 1
		if (settings.gCurrentFilePaths.HasKey("BAK1Save1x1.sgd"))
			FileCopy, % FileToReplaceWith, % settings.gCurrentFilePaths["BAK1Save1x1.sgd"], 1
		if (settings.gCurrentFilePaths.HasKey("BAK1Save1x2.sgd"))
			FileCopy, % FileToReplaceWith, % settings.gCurrentFilePaths["BAK1Save1x2.sgd"], 1
	} else if (InStr(FileName, "2x")){
		if (settings.gCurrentFilePaths.HasKey("BAK1Save2x0.sgd"))
			FileCopy, % FileToReplaceWith, % settings.gCurrentFilePaths["BAK1Save2x0.sgd"], 1
		if (settings.gCurrentFilePaths.HasKey("BAK1Save2x1.sgd"))
			FileCopy, % FileToReplaceWith, % settings.gCurrentFilePaths["BAK1Save2x1.sgd"], 1
		if (settings.gCurrentFilePaths.HasKey("BAK1Save2x2.sgd"))
			FileCopy, % FileToReplaceWith, % settings.gCurrentFilePaths["BAK1Save2x2.sgd"], 1
	}
}

GetUpToDateFile(File){
	UpToDateFile := ""
	, temp := ""
	, File1 := File . "0.sgd"
	, File2 := File . "1.sgd"
	, File3 := File . "2.sgd"
	if !(settings.gCurrentFilePaths.HasKey(File1))
		return UpToDateFile := File2
	FileGetTime, time1, % settings.gCurrentFilePaths[File1]
	FileGetTime, time2, % settings.gCurrentFilePaths[File2]
	FileGetTime, time3, % settings.gCurrentFilePaths[File3]
	temp := time2
	if ((time2 -= time1, SMHD) > 0){
		UpToDateFile := File2
	} else if (((temp -= time1, SMHD) == 0) && !settings.gCurrentFilePaths.HasKey(File3)){
		UpToDateFile := File1
	} else if ((time1 -= time3, SMHD) > 0) {
		UpToDateFile := File1
	} else {
		UpToDateFile := File3
	}
	return UpToDateFile
}
