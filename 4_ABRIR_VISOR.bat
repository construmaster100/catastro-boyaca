@echo off
rem Abre el buscador de predios en el navegador. Dejar esta ventana abierta mientras se usa.
chcp 65001 >nul
cd /d "%~dp0"
if not exist "visor\datos\indice.json" python exportar_web.py
python servidor_visor.py
pause
