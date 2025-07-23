@echo off
echo Installing Text-to-Speech packages for voice notifications...
echo.

echo Installing pywin32 (for Windows SAPI)...
pip install pywin32
echo.

echo Installing pyttsx3 (alternative TTS engine)...
pip install pyttsx3
echo.

echo Installation complete!
echo You can now use voice notifications in the novel scraper.
echo.
pause
