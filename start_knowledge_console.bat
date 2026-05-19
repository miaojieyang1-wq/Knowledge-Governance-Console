@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON_EXE=%ROOT%streamlit-ai-app-py-requirements-txt\.venv\Scripts\python.exe"
set "APP_FILE=%ROOT%app.py"
set "HOST=127.0.0.1"
set "PORT=8501"
set "CONFIG_FILE=%ROOT%config.yaml"

if not exist "%APP_FILE%" (
    echo [ERROR] Cannot find app.py in: %ROOT%
    pause
    exit /b 1
)

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Cannot find project Python runtime:
    echo %PYTHON_EXE%
    echo.
    echo Please install dependencies first, or adjust this launcher path.
    pause
    exit /b 1
)

echo Starting Knowledge Governance Console...
echo URL: http://%HOST%:%PORT%
echo Config: %CONFIG_FILE%
echo.
echo Keep this window open while using the console.
echo Press Ctrl+C in this window to stop the server.
echo.

cd /d "%ROOT%"
"%PYTHON_EXE%" -m streamlit run "%APP_FILE%" --server.address "%HOST%" --server.port "%PORT%" --server.headless false --browser.gatherUsageStats false

echo.
echo Console has stopped.
pause
