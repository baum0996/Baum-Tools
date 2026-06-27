@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
title BAUM TOOLS V1

set "VENV_DIR=%~dp0.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "ACTIVATE_SCRIPT=%VENV_DIR%\Scripts\activate.bat"
set "PYTHON_EXE="

echo.
echo BAUM TOOLS V1
echo Preparing application...
echo.

if not exist "%VENV_PYTHON%" (
    call :find_python
    if not defined PYTHON_EXE goto python_missing

    echo Creating virtual environment...
    "%PYTHON_EXE%" -m venv "%VENV_DIR%" >nul 2>nul
    if errorlevel 1 goto venv_failed
)

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>nul
    if errorlevel 1 (
        call :find_python
        if not defined PYTHON_EXE goto python_missing

        echo Recreating virtual environment with Python 3.12+...
        rmdir /s /q "%VENV_DIR%" >nul 2>nul
        "%PYTHON_EXE%" -m venv "%VENV_DIR%" >nul 2>nul
        if errorlevel 1 goto venv_failed
    )
)

if not exist "%ACTIVATE_SCRIPT%" goto venv_failed
call "%ACTIVATE_SCRIPT%" >nul 2>nul
if errorlevel 1 goto venv_failed

echo Upgrading pip...
python -m pip install --upgrade pip --disable-pip-version-check --quiet
if errorlevel 1 goto pip_failed

if exist "tools\sync_requirements.py" (
    python tools\sync_requirements.py >nul 2>nul
)

echo Installing dependencies...
python -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 goto install_failed

echo.
echo Starting BAUM TOOLS V1...
echo.
python main.py
if errorlevel 1 goto app_failed

echo.
pause
exit /b 0

:find_python
for %%P in (
    "%~dp0runtime\python-3.13.0\tools\python.exe"
    "%~dp0runtime\python-3.13\tools\python.exe"
    "%~dp0runtime\python313\python.exe"
) do (
    if exist "%%~P" (
        "%%~P" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>nul
        if !errorlevel! equ 0 (
            set "PYTHON_EXE=%%~P"
            exit /b 0
        )
    )
)

for %%P in (
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles(x86)%\Python313\python.exe"
    "%LocalAppData%\Microsoft\WindowsApps\python.exe"
    "%LocalAppData%\Microsoft\WindowsApps\python3.exe"
) do (
    if exist "%%~P" (
        "%%~P" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>nul
        if !errorlevel! equ 0 (
            set "PYTHON_EXE=%%~P"
            exit /b 0
        )
    )
)

for /f "delims=" %%P in ('where python 2^>nul') do (
    "%%P" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>nul
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=%%P"
        exit /b 0
    )
)

for /f "delims=" %%P in ('where python3 2^>nul') do (
    "%%P" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>nul
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=%%P"
        exit /b 0
    )
)

where py >nul 2>nul
if not errorlevel 1 (
    for /f "delims=" %%P in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do (
        if exist "%%P" (
            set "PYTHON_EXE=%%P"
            exit /b 0
        )
    )
)

exit /b 0

:python_missing
echo Python 3.12 or newer was not found.
echo.
echo Install Python 3.12 or newer, then start this file again.
echo.
echo Recommended options:
echo Python 3.12 or newer
echo Microsoft Store or https://www.python.org/downloads/
echo.
echo If Python is already installed but this app cannot find it, turn these aliases ON:
echo Settings ^> Apps ^> Advanced app settings ^> App execution aliases
echo python.exe and python3.exe
echo.
pause
exit /b 1

:venv_failed
echo The virtual environment could not be created or activated.
echo Please reinstall Python 3.12+ and try again.
echo.
pause
exit /b 1

:pip_failed
echo pip could not be upgraded.
echo Check your Python installation and internet connection.
echo.
pause
exit /b 1

:install_failed
echo Dependencies could not be installed.
echo Check your internet connection, then start this file again.
echo.
pause
exit /b 1

:app_failed
echo BAUM TOOLS V1 stopped because an error occurred.
echo Check the logs folder for details.
echo.
pause
exit /b 1
