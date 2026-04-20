@echo off
:: Truco para evitar el mensaje "finalizar trabajo por lotes" al cerrar con Ctrl+C:
:: el .bat se relanza a si mismo dentro de un cmd /c hijo, que absorbe el Ctrl+C.
if not defined _STARTED (
    set _STARTED=1
    cmd /d /c "%~f0" %*
    exit /b
)

title IvoryOS
cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [ERROR] No se encontro el entorno virtual en .venv\
    echo Ruta buscada: %PYTHON%
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
