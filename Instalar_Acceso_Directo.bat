@echo off
title Instalando acceso directo de IvoryOS...

:: Ruta del proyecto (donde esta este .bat)
set "PROJECT_DIR=%~dp0"
:: Quitar la barra final
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

set "PYTHON=%PROJECT_DIR%\.venv\Scripts\python.exe"
set "ICO_FILE=%PROJECT_DIR%\ivoryos\static\favicon.ico"
set "SHORTCUT=%USERPROFILE%\Desktop\IvoryOS.lnk"

if not exist "%PYTHON%" (
    echo [ERROR] No se encontro el entorno virtual en .venv\
    echo Ruta buscada: %PYTHON%
    pause
    exit /b 1
)

:: Crear el acceso directo apuntando directamente a python.exe
:: (evita el mensaje "finalizar trabajo por lotes" al cerrar)
powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$s = $ws.CreateShortcut('%SHORTCUT%'); " ^
  "$s.TargetPath = '%PYTHON%'; " ^
  "$s.Arguments = '-m ivoryos.main'; " ^
  "$s.WorkingDirectory = '%PROJECT_DIR%'; " ^
  "$s.IconLocation = '%ICO_FILE%'; " ^
  "$s.WindowStyle = 1; " ^
  "$s.Description = 'Lanzar IvoryOS'; " ^
  "$s.Save()"

if exist "%SHORTCUT%" (
    echo.
    echo  Acceso directo creado correctamente en el escritorio.
    echo  Ahora puedes abrir IvoryOS desde el icono del escritorio.
) else (
    echo.
    echo  [ERROR] No se pudo crear el acceso directo.
    echo  Intentalo ejecutando este archivo como Administrador.
)
echo.
pause
