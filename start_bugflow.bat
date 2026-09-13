@echo off
title BugFlow Application

echo ==========================================
echo       Starting BugFlow Application
echo ==========================================

cd /d "%~dp0"

echo.
echo Starting FastAPI backend...
start "" /b "%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --app-dir "%~dp0backend"

echo.
echo Starting BugFlow frontend...
start "" /b "%~dp0.venv\Scripts\python.exe" -m http.server 5500 --directory "%~dp0frontend"

echo.
echo Waiting for BugFlow servers...
timeout /t 3 /nobreak >nul

echo.
echo ==========================================
echo       BugFlow Application Started
echo ==========================================
echo.
echo Backend  : http://127.0.0.1:8000
echo Frontend : http://127.0.0.1:5500
echo Swagger  : http://127.0.0.1:8000/docs
echo.

start "" "http://127.0.0.1:5500/index.html"

echo BugFlow login page opened.
echo.