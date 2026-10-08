@echo off
rem Despues de completar la descarga: organiza el pais y regenera visor, estadisticas, Excel y copia offline.
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
echo [1/7] organizar todo el pais & python catastro_colombia.py organizar || goto error
echo [2/7] datos web de Boyaca & python exportar_web.py 15 || goto error
echo [3/7] zonas urbanas y areas & python estadisticas_urbanas.py || goto error
echo [4/7] indicadores y provincias & python importar_cct.py || goto error
echo [5/7] analisis & python analisis_cct.py || goto error
echo [6/7] capas geo y Excel & python exportar_geo.py && python exportar_excel.py || goto error
echo [7/7] copia offline & python construir_versiones.py --offline || goto error
echo POST_TERMINADO
goto :eof
:error
echo POST_ERROR
