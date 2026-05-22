@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON_EXE=%ROOT%streamlit-ai-app-py-requirements-txt\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Cannot find project Python runtime:
    echo %PYTHON_EXE%
    pause
    exit /b 1
)

cd /d "%ROOT%"
"%PYTHON_EXE%" "%ROOT%selfcheck.py"
if errorlevel 1 (
    echo.
    echo Selfcheck failed.
    pause
    exit /b 1
)

echo.
echo Selfcheck passed.
pause
