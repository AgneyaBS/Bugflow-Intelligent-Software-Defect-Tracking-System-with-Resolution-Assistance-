@echo off

echo ==========================================
echo        Starting BugFlow Application
echo ==========================================
echo.

cd /d "%~dp0backend"

echo Starting FastAPI server...
echo.

start /b "" ..\.venv\Scripts\python.exe -m uvicorn app.main:app

echo Waiting for BugFlow server...

:WAIT

powershell -Command "try { if ((Test-NetConnection 127.0.0.1 -Port 8000 -InformationLevel Quiet) -eq $true) { exit 0 } else { exit 1 } } catch { exit 1 }"

if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto WAIT
)

echo.
echo ==========================================
echo       BugFlow server is READY!
echo ==========================================
echo.

start "" "%~dp0frontend\index.html"

echo BugFlow login page opened.
echo.