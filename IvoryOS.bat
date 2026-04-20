@echo off
title IvoryOS
cd /d "%~dp0"

:: Buscar Python: prueba venvs locales primero, luego el Python del sistema
set "PYTHON="
if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not defined PYTHON if exist "%~dp0venv\Scripts\python.exe" set "PYTHON=%~dp0venv\Scripts\python.exe"
if not defined PYTHON if exist "%~dp0env\Scripts\python.exe"  set "PYTHON=%~dp0env\Scripts\python.exe"
if not defined PYTHON for /f "tokens=*" %%p in ('where python 2^>nul') do if not defined PYTHON set "PYTHON=%%p"

if not defined PYTHON (
    echo [ERROR] No se encontro Python ni ningun entorno virtual.
    echo Instala Python o crea un entorno virtual en la carpeta del proyecto.
    pause
    exit /b 1
)

echo Iniciando IvoryOS...
"%PYTHON%" -m ivoryos.main %*

if errorlevel 1 (
    echo.
    echo [ERROR] IvoryOS se ha cerrado con un error.
    pause
)
