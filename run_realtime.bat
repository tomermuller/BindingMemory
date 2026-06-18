@echo off
cd /d "%~dp0"
.venv\Scripts\python.exe -m src.real_time_task.real_time_task
pause
