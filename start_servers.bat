@echo off
echo Starting SmartMeet AI v2 Servers...

start "SmartMeet Backend API" cmd /k "cd /d %~dp0backend && .\venv\Scripts\activate && python main.py"
start "SmartMeet Frontend Dashboard" cmd /k "cd /d %~dp0frontend && npm run dev"

echo Done! Waiting for servers to initialize...
echo Backend API: http://127.0.0.1:8000
echo Frontend UI: http://localhost:3000
pause
