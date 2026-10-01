@echo off
rem Abre la vista de administrador (estadisticas de visitas). Solo funciona en este computador.
rem Si el visor no esta abierto, lo enciende (ventana minimizada).
cd /d "%~dp0"
powershell -NoProfile -Command "try { Invoke-WebRequest http://127.0.0.1:8765/ -UseBasicParsing -TimeoutSec 2 | Out-Null } catch { Start-Process cmd -ArgumentList '/c','python servidor_visor.py --sin-navegador' -WindowStyle Minimized; Start-Sleep 4 }"
start "" "http://localhost:8765/admin/"
