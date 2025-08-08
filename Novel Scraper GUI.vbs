' Novel Scraper GUI Launcher (VBScript - Silent with Icon Support)
' This script runs the GUI application without showing a command prompt window
' and can create a desktop shortcut with custom icon

Dim shell, fso, scriptDir, appFile, venvPath, pythonExe, command

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Change to script directory
shell.CurrentDirectory = scriptDir

' Check if this is being run to create a desktop shortcut with icon
If WScript.Arguments.Count > 0 Then
    If WScript.Arguments(0) = "/createshortcut" Then
        CreateDesktopShortcut
        WScript.Quit
    End If
End If

' Check if app file exists
appFile = scriptDir & "\app_version_scrape_novel.py"
If Not fso.FileExists(appFile) Then
    MsgBox "Error: app_version_scrape_novel.py not found in " & scriptDir, 16, "Novel Scraper"
    WScript.Quit
End If

' Check for virtual environment
venvPath = scriptDir & "\.venv\Scripts\python.exe"
If fso.FileExists(venvPath) Then
    pythonExe = venvPath
Else
    pythonExe = "python"
End If

' Build command
command = """" & pythonExe & """ """ & appFile & """"

' Run the application (0 = hidden window, False = don't wait)
shell.Run command, 0, False

' Function to create desktop shortcut with custom icon
Sub CreateDesktopShortcut()
    Dim desktop, shortcut, iconPath
    
    ' Get desktop path
    desktop = shell.SpecialFolders("Desktop")
    
    ' Create shortcut object
    Set shortcut = shell.CreateShortcut(desktop & "\Novel Scraper.lnk")
    
    ' Set shortcut properties
    shortcut.TargetPath = "wscript.exe"
    shortcut.Arguments = """" & WScript.ScriptFullName & """"
    shortcut.WorkingDirectory = scriptDir
    shortcut.Description = "Novel Scraper GUI - Silent Launch"
    
    ' Look for custom icon files in the script directory
    iconPath = ""
    If fso.FileExists(scriptDir & "\icon.ico") Then
        iconPath = scriptDir & "\icon.ico"
    ElseIf fso.FileExists(scriptDir & "\app_icon.ico") Then
        iconPath = scriptDir & "\app_icon.ico"
    ElseIf fso.FileExists(scriptDir & "\novel_scraper.ico") Then
        iconPath = scriptDir & "\novel_scraper.ico"
    ElseIf fso.FileExists(scriptDir & "\scraper.ico") Then
        iconPath = scriptDir & "\scraper.ico"
    End If
    
    ' Set custom icon if found, otherwise use default Python icon
    If iconPath <> "" Then
        shortcut.IconLocation = iconPath & ",0"
        MsgBox "Desktop shortcut created with custom icon: " & fso.GetFileName(iconPath), 64, "Novel Scraper"
    Else
        ' Try to use Python icon as fallback
        If pythonExe <> "python" And fso.FileExists(pythonExe) Then
            shortcut.IconLocation = pythonExe & ",0"
        End If
        MsgBox "Desktop shortcut created!" & vbCrLf & vbCrLf & "To use a custom icon, place an .ico file named:" & vbCrLf & "• icon.ico" & vbCrLf & "• app_icon.ico" & vbCrLf & "• novel_scraper.ico" & vbCrLf & "• scraper.ico" & vbCrLf & vbCrLf & "in the same folder as this script, then run this script again with /createshortcut", 64, "Novel Scraper"
    End If
    
    ' Save the shortcut
    shortcut.Save
End Sub
