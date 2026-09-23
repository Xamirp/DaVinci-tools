@echo off
cd /d "%~dp0"

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0beat_marker.py" --timeline intro --track-index 2 %*
) else (
    python "%~dp0beat_marker.py" --timeline intro --track-index 2 %*
)
pause
