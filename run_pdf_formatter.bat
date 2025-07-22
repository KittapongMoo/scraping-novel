@echo off
REM Activate virtual environment and run PDF formatter
echo Activating virtual environment...
call ".venv\Scripts\activate.bat"
echo Running PDF formatter...
python format_novel_to_pdf.py
pause
