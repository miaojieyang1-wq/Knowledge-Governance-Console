@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON_EXE=%ROOT%streamlit-ai-app-py-requirements-txt\.venv\Scripts\python.exe"
set "LAUNCHER=%ROOT%exe_launcher.py"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Cannot find project Python runtime:
    echo %PYTHON_EXE%
    echo.
    echo Please install dependencies first, or adjust this launcher path.
    pause
    exit /b 1
)

if not exist "%LAUNCHER%" (
    echo [ERROR] Cannot find launcher script:
    echo %LAUNCHER%
    pause
    exit /b 1
)

cd /d "%ROOT%"
"%PYTHON_EXE%" "%LAUNCHER%"

echo.
echo Console has stopped.
pause
