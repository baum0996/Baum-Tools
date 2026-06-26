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
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles(x86)%\Python313\python.exe"
) do (
    if exist "%%~P" (
        set "PYTHON_EXE=%%~P"
        exit /b 0
    )
)

for /f "delims=" %%P in ('where python 2^>nul') do (
    set "FOUND_PYTHON=%%P"
    echo !FOUND_PYTHON! | findstr /i "\\WindowsApps\\" >nul
    if errorlevel 1 (
        "%%P" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 13) else 1)" >nul 2>nul
        if !errorlevel! equ 0 (
            set "PYTHON_EXE=%%P"
            exit /b 0
        )
    )
)

for /f "delims=" %%P in ('where python3 2^>nul') do (
    set "FOUND_PYTHON=%%P"
    echo !FOUND_PYTHON! | findstr /i "\\WindowsApps\\" >nul
    if errorlevel 1 (
        "%%P" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 13) else 1)" >nul 2>nul
        if !errorlevel! equ 0 (
            set "PYTHON_EXE=%%P"
            exit /b 0
        )
    )
)

where py >nul 2>nul
if not errorlevel 1 (
    for /f "delims=" %%P in ('py -3.13 -c "import sys; print(sys.executable)" 2^>nul') do (
        if exist "%%P" (
            set "PYTHON_EXE=%%P"
            exit /b 0
        )
    )
)

exit /b 0

:python_missing
echo Python 3.13 or newer was not found.
echo.
echo Please install Python from:
echo https://www.python.org/downloads/
echo.
echo During installation, enable:
echo Add python.exe to PATH
echo.
echo If Windows opens the Microsoft Store, disable these aliases:
echo Settings ^> Apps ^> Advanced app settings ^> App execution aliases
echo python.exe and python3.exe
echo.
pause
exit /b 1

:venv_failed
echo The virtual environment could not be created or activated.
echo Please reinstall Python 3.13+ and try again.
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
