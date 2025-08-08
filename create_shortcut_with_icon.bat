@echo off
echo Creating desktop shortcut with custom icon...
echo.

REM Run the VBScript with /createshortcut parameter to create desktop shortcut
wscript.exe "Novel Scraper GUI.vbs" /createshortcut

echo.
echo Done! Check your desktop for the "Novel Scraper" shortcut.
pause
