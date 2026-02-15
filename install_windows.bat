@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo =============================================
echo      Voice Typer - Installatie
echo            Windows
echo =============================================
echo.

:: ── 1. Python check ──────────────────────────────────
echo [1/4] Python controleren...

set "PYTHON_CMD="

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py -3"
    goto :check_version
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=python"
    goto :check_version
)

echo   X Python niet gevonden.
echo.
echo   Installeer Python 3.10+ van:
echo     https://www.python.org/downloads/
echo.
echo   LET OP: vink "Add Python to PATH" aan tijdens installatie!
echo.
pause
exit /b 1

:check_version
for /f "tokens=*" %%v in ('%PYTHON_CMD% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set "PY_VER=%%v"
for /f "tokens=*" %%v in ('%PYTHON_CMD% -c "import sys; print(sys.version_info.major)"') do set "PY_MAJOR=%%v"
for /f "tokens=*" %%v in ('%PYTHON_CMD% -c "import sys; print(sys.version_info.minor)"') do set "PY_MINOR=%%v"

if !PY_MAJOR! LSS 3 goto :version_fail
if !PY_MAJOR! EQU 3 if !PY_MINOR! LSS 10 goto :version_fail

echo   OK Python %PY_VER%
goto :setup_venv

:version_fail
echo   X Python %PY_VER% gevonden, maar 3.10+ is vereist.
echo.
echo   Download nieuwste versie van:
echo     https://www.python.org/downloads/
echo.
pause
exit /b 1

:: ── 2. Virtuele omgeving ─────────────────────────────
:setup_venv
echo.
echo [2/4] Virtuele omgeving...

if not exist ".venv\Scripts\python.exe" (
    echo   Virtuele omgeving maken...
    %PYTHON_CMD% -m venv .venv
    echo   OK Aangemaakt
) else (
    echo   OK Bestaat al
)

call ".venv\Scripts\activate.bat"

:: ── 3. Dependencies ──────────────────────────────────
echo.
echo [3/4] Dependencies installeren...

python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q
echo   OK Alle packages geinstalleerd

:: ── 4. Configuratie ──────────────────────────────────
echo.
echo [4/4] Configuratie...

set "CONFIG_PATH=%USERPROFILE%\.voice-typer.toml"
if exist "%CONFIG_PATH%" (
    echo   OK Config bestaat al op %CONFIG_PATH%
    echo.
    set /p OPEN_SETTINGS="  Settings openen om aan te passen? (y/N): "
    if /I "!OPEN_SETTINGS!"=="Y" (
        python voice_typer.py settings
    )
) else (
    echo   Geen config gevonden. Settings venster openen...
    echo.
    python voice_typer.py settings
    if exist "%CONFIG_PATH%" (
        echo   OK Configuratie opgeslagen
    ) else (
        echo   ! Geen configuratie opgeslagen.
        echo     Je kunt later alsnog draaien:
        echo       python voice_typer.py settings
    )
)

:: ── Klaar ────────────────────────────────────────────
echo.
echo =============================================
echo      Installatie voltooid!
echo =============================================
echo.
echo   Starten: dubbelklik start_windows.bat
echo   Settings: python voice_typer.py settings
echo.
echo   TIP: Als typen niet werkt in sommige apps,
echo        start de terminal als Administrator.
echo.
pause
