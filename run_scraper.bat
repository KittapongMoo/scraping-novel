@echo off
REM Activate virtual environment and run novel scraper
echo Activating virtual environment...
call ".venv\Scripts\activate.bat"
echo Running novel scraper...
python scrape_novel.py
pause
