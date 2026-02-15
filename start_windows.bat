@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Geen virtuele omgeving gevonden.
  echo Run eerst install_windows.bat
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"

echo Voice Typer wordt gestart...
python voice_typer.py run

echo.
echo Voice Typer is gestopt.
pause
