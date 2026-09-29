@echo off
rem Abre el visor Catastro Boyaca SIN internet y SIN Python (usa PowerShell de Windows).
rem Dejar esta ventana abierta mientras se usa el visor.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0servidor_offline.ps1"
pause
