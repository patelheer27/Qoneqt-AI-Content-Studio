@echo off
title Qoneqt AI Content Studio Launcher
echo ========================================================
echo   Starting Qoneqt AI Content Studio (Backend + Frontend)
echo ========================================================

cd /d "%~dp0"

echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "Qoneqt AI Backend (Port 8000)" cmd /k "backend\venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Launching Vite Frontend on http://localhost:5173 ...
start "Qoneqt AI Frontend (Port 5173)" cmd /k "npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5173"

echo.
echo ========================================================
echo   Servers launched! You can access:
echo   - Dashboard: http://localhost:5173
echo   - Direct:    http://127.0.0.1:5173
echo ========================================================

