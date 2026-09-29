@echo off
rem Descarga todo el pais y lo organiza en carpetas. Se puede cerrar y volver a abrir: continua donde iba.
chcp 65001 >nul
cd /d "%~dp0"
python --version >nul 2>&1 || (echo Python no esta instalado o no esta en el PATH. Ver README.md, seccion 4. & pause & exit /b 1)
echo Instalando/verificando librerias...
python -m pip install -q --disable-pip-version-check -r requirements.txt
python catastro_colombia.py todo
echo.
echo Proceso terminado. Revisa los mensajes de arriba.
pause
