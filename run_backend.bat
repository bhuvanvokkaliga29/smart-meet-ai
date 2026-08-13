@echo off
title SmartMeet AI v2 Backend Server
cls
echo =======================================================
echo   ⚡ SmartMeet AI v2 — Launching Backend API Server
echo =======================================================
echo.

cd /d "%~dp0backend"
if not exist "venv" (
    echo Creating virtual environment...
    py -m venv venv
)

echo Activating Python environment...
call .\venv\Scripts\activate.bat

echo Checking dependencies...
pip install -r requirements.txt

echo Starting FastAPI Backend Server on http://127.0.0.1:8000...
python main.py

pause
