@echo off
setlocal EnableExtensions

cd /d "%~dp0"

echo.
echo BAUM TOOLS - VENV FIX
echo.

if exist ".venv" (
    echo Removing old .venv...
    rmdir /s /q ".venv"
)

echo Rewriting requirements.txt...
> requirements.txt echo colorama^>=0.4.6
>> requirements.txt echo psutil^>=6.1.0
>> requirements.txt echo rich^>=13.9.0

echo.
echo Creating new virtual environment...

where python >nul 2>nul
if not errorlevel 1 (
    python -m venv .venv
    goto venv_created
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -m venv .venv
    goto venv_created
)

echo.
echo ERROR: Python was not found.
echo Install Python 3.12+ and enable "Add python.exe to PATH".
pause
exit /b 1

:venv_created
if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo ERROR: .venv could not be created.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing requirements...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Requirements install failed.
    pause
    exit /b 1
)

echo.
echo Starting BAUM TOOLS...
python main.py

echo.
pause
