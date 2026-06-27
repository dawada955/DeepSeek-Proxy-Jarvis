@echo off
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"

if not exist "env\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

call env\Scripts\activate
pip install -r requirements.txt >nul 2>&1
python main.py
pause
