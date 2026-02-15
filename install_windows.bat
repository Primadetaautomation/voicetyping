@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  set "PYTHON_CMD=py -3"
) else (
  where python >nul 2>&1
  if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=python"
  ) else (
    echo Python niet gevonden. Installeer eerst Python 3.
    pause
    exit /b 1
  )
)

echo Gebruik Python via: %PYTHON_CMD%

if not exist ".venv\Scripts\python.exe" (
  echo Virtuele omgeving maken...
  %PYTHON_CMD% -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

set "CONFIG_PATH=%USERPROFILE%\.voice-typer.toml"
if exist "%CONFIG_PATH%" (
  echo Config bestaat al op %CONFIG_PATH%
  set /p RUN_SETUP=Setup opnieuw draaien? (y/N):
  if /I "%RUN_SETUP%"=="Y" (
    python voice_typer.py setup
  )
) else (
  python voice_typer.py setup
)

echo.
echo Installatie klaar.
echo Start nu met: start_windows.bat
pause
