@echo off
rem Muestra cuanto se ha descargado. No descarga nada.
chcp 65001 >nul
cd /d "%~dp0"
python catastro_colombia.py estado
pause
