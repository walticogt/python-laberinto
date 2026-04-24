@echo off
REM ============================================================
REM  Lanzador del Generador de Laberintos (Windows)
REM  Alternativa al dist\laberinto.exe: activa el venv y llama
REM  a Python directamente, sin necesidad de compilar con PyInstaller.
REM
REM  Doble clic para abrir. Requiere que el venv ya exista en .venv\
REM  con el paquete instalado (pip install -e .).
REM ============================================================
setlocal

cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"

if not exist "%PY%" goto NOVENV

:MENU
cls
echo ==================================================
echo         Generador de Laberintos
echo ==================================================
echo.
echo   1) Basico    (preset "simple",  1 pagina)
echo   2) Medio     (preset "medium",  1 pagina)
echo   3) Complejo  (preset "complex", 1 pagina)
echo.
echo   4) Modo interactivo completo del CLI
echo      (menu en espanol, permite editar presets)
echo.
echo   5) Personalizado (multiples paginas)
echo   6) Personalizado con seed (reproducible)
echo.
echo   0) Salir
echo.
set "CHOICE="
set /p "CHOICE=Elige una opcion: "

if "%CHOICE%"=="1" goto SIMPLE
if "%CHOICE%"=="2" goto MEDIUM
if "%CHOICE%"=="3" goto COMPLEX
if "%CHOICE%"=="4" goto INTERACTIVE
if "%CHOICE%"=="5" goto CUSTOM
if "%CHOICE%"=="6" goto SEEDED
if "%CHOICE%"=="0" exit /b 0

echo.
echo Opcion invalida. Intenta de nuevo.
timeout /t 2 >nul
goto MENU

:SIMPLE
"%PY%" -m maze_pdf --difficulty simple
goto PAUSE_RETURN

:MEDIUM
"%PY%" -m maze_pdf --difficulty medium
goto PAUSE_RETURN

:COMPLEX
"%PY%" -m maze_pdf --difficulty complex
goto PAUSE_RETURN

:INTERACTIVE
"%PY%" -m maze_pdf
goto PAUSE_RETURN

:CUSTOM
set "DIFF="
set "PAGES="
set /p "DIFF=Dificultad (simple/medium/complex): "
set /p "PAGES=Numero de paginas (1-10): "
"%PY%" -m maze_pdf --difficulty %DIFF% --pages %PAGES%
goto PAUSE_RETURN

:SEEDED
set "DIFF="
set "PAGES="
set "SEED="
set /p "DIFF=Dificultad (simple/medium/complex): "
set /p "PAGES=Numero de paginas (1-10): "
set /p "SEED=Seed (numero entero): "
"%PY%" -m maze_pdf --difficulty %DIFF% --pages %PAGES% --seed %SEED%
goto PAUSE_RETURN

:PAUSE_RETURN
echo.
pause
goto MENU

:NOVENV
echo.
echo ERROR: No se encontro el entorno virtual en .venv\
echo.
echo Crealo con estos comandos desde esta carpeta:
echo.
echo     python -m venv .venv
echo     .venv\Scripts\python.exe -m pip install -e .
echo.
echo Luego vuelve a ejecutar este .bat
echo.
pause
exit /b 1
