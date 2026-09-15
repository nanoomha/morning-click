@echo off
cd /d "%~dp0\.."
if not exist logs mkdir logs
call venv\Scripts\activate.bat
python main_crawl.py >> logs\crawl.log 2>&1
