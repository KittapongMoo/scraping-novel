# PowerShell script to create a desktop shortcut
# Run this once to create a shortcut on your desktop

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ShortcutPath = "$DesktopPath\Novel Scraper GUI.lnk"
$TargetPath = "$ScriptDir\run_gui_app.bat"

# Create shortcut
$WShell = New-Object -ComObject WScript.Shell
$Shortcut = $WShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.Description = "Novel Scraper GUI Application"
$Shortcut.Save()

Write-Host "✅ Desktop shortcut created: $ShortcutPath" -ForegroundColor Green
Write-Host "You can now double-click the shortcut on your desktop to run the app!" -ForegroundColor Cyan
