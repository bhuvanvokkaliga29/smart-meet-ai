@echo off
title SmartMeet AI v2 Frontend Server
cls
echo =======================================================
echo   ⚡ SmartMeet AI v2 — Launching Frontend Dashboard
echo =======================================================
echo.

cd /d "%~dp0frontend"
echo [1/2] Installing dependencies if needed...
call npm install --no-audit --no-fund

echo.
echo [2/2] Starting Vite Dev Server on http://127.0.0.1:3000...
echo.

call npx vite --host 127.0.0.1 --port 3000 --open

pause
