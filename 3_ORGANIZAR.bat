@echo off
rem Vuelve a generar la carpeta catastro/ a partir de lo ya descargado en crudo/. No usa internet (salvo la lista de municipios).
chcp 65001 >nul
cd /d "%~dp0"
python catastro_colombia.py organizar
pause
