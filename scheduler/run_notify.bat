@echo off
cd /d "%~dp0\.."
if not exist logs mkdir logs
call venv\Scripts\activate.bat
python main_notify_schedule.py >> logs\notify.log 2>&1
