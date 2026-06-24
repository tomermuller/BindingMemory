@echo off
cd /d "%~dp0"
.venv\Scripts\python.exe -m src.binding_task.record_baseline
pause
