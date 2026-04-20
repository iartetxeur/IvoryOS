@echo off
title IvoryOS
cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [ERROR] No se encontro el entorno virtual en .venv\
    echo Ruta buscada: "%PYTHON%"
    pause
    exit /b 1
)

echo Iniciando IvoryOS...
"%PYTHON%" -m ivoryos.main %*
