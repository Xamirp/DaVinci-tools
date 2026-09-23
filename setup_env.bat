@echo off
cd /d "%~dp0"

echo ============================================================
echo   BitMaker: Initializing environment and dependencies
echo ============================================================

if not exist "%~dp0.venv" (
    echo Creating .venv (Python 3.12)...
    py -3.12 -m venv "%~dp0.venv" 2>nul
    if errorlevel 1 (
        python -m venv "%~dp0.venv"
    )
)

if exist "%~dp0.venv\Scripts\python.exe" (
    echo Installing requirements.txt...
    "%~dp0.venv\Scripts\python.exe" -m pip install --upgrade pip
    "%~dp0.venv\Scripts\pip.exe" install -r "%~dp0requirements.txt"
    echo.
    echo [SUCCESS] Environment ready!
) else (
    echo [ERROR] Failed to create .venv.
)
pause
