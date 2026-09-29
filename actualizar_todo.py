"""
Automatizacion completa del proyecto Catastro Boyaca: ejecuta, en orden, todos los pasos que
actualizan los datos, las estadisticas, los Excel y el visor.

    python actualizar_todo.py                 actualizacion normal (fuentes economicas + estadisticas + Excel)
    python actualizar_todo.py --completo      ademas recalcula zonas urbanas y areas (lento, ~5 min)
    python actualizar_todo.py --offline       al final, actualiza la copia autoportante del escritorio
    python actualizar_todo.py --solo excel    ejecuta solo los pasos cuyo nombre contiene "excel"

Pasos (cada uno es un script independiente que tambien se puede correr solo):
    1. scraper_cct.py          descarga documentos nuevos de la Camara de Comercio de Tunja -> docs/camara_comercio/
    2. extraer_cct.py          texto y tablas de los documentos -> Excel por seccion
    3. importar_cct.py         indicadores municipales y provincias -> visor/datos/
    4. estadisticas_urbanas.py zonas urbanas, areas y jerarquia (solo con --completo)
    5. analisis_cct.py         calidad de datos, economia, uso del suelo y coincidencias -> informes/
    6. exportar_geo.py         capas GeoJSON/CSV para Geo Data Viewer -> geo/
    7. exportar_excel.py       datos del proyecto en Excel -> docs/datos/
    8. informe web             informes/analisis_boyaca_en_cifras.md -> visor/camara/analisis.html
    9. construir_versiones.py  copia offline autoportante (solo con --offline)

Registro de cada ejecucion: informes/actualizacion.log
"""
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

CARPETA = Path(__file__).parent
REGISTRO = CARPETA / "informes" / "actualizacion.log"

PASOS = [
    ("descarga de documentos (Camara de Comercio)", ["scraper_cct.py"], False),
    ("extraccion de texto y tablas a Excel", ["extraer_cct.py"], False),
    ("indicadores municipales y provincias", ["importar_cct.py"], False),
    ("zonas urbanas, areas y jerarquia", ["estadisticas_urbanas.py"], "--completo"),
    ("analisis de calidad, economia y coincidencias", ["analisis_cct.py"], False),
    ("capas para Geo Data Viewer", ["exportar_geo.py"], False),
    ("datos del proyecto en excel", ["exportar_excel.py"], False),
    ("informe web", None, False),
    ("copia offline autoportante", ["construir_versiones.py", "--offline"], "--offline"),
]


def informe_web():
    md = CARPETA / "informes" / "analisis_boyaca_en_cifras.md"
    import markdown
    (CARPETA / "visor" / "camara" / "analisis.html").write_text(
        markdown.markdown(md.read_text(encoding="utf-8"), extensions=["tables"]), encoding="utf-8")


def main():
    args = sys.argv[1:]
    solo = args[args.index("--solo") + 1].lower() if "--solo" in args else None
    REGISTRO.parent.mkdir(exist_ok=True)
    resultados = []
    with open(REGISTRO, "a", encoding="utf-8") as log:
        log.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M} · {' '.join(args) or 'normal'} =====\n")
        for i, (nombre, comando, bandera) in enumerate(PASOS, 1):
            if solo and solo not in nombre.lower():
                continue
            if bandera and bandera not in args and not solo:
                print(f"[{i}/{len(PASOS)}] {nombre}: omitido (use {bandera})")
                continue
            print(f"[{i}/{len(PASOS)}] {nombre}...", flush=True)
            t0 = time.time()
            try:
                if comando is None:
                    informe_web()
                    ok, salida = True, "ok"
                else:
                    r = subprocess.run([sys.executable, *comando], cwd=CARPETA, capture_output=True, text=True,
                                       encoding="utf-8", errors="replace", env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
                    ok, salida = r.returncode == 0, (r.stdout + r.stderr).strip()
            except Exception as e:
                ok, salida = False, str(e)
            seg = time.time() - t0
            ultima = salida.splitlines()[-1] if salida else ""
            print(f"      {'OK' if ok else 'ERROR'} ({seg:,.0f} s) {ultima[:150]}")
            log.write(f"[{'OK' if ok else 'ERROR'}] {nombre} ({seg:.0f} s)\n{salida[-4000:]}\n")
            resultados.append((nombre, ok))
            if not ok:
                print("      Se detiene la actualizacion: revise informes/actualizacion.log")
                break
    fallidos = [n for n, ok in resultados if not ok]
    print("\nActualizacion " + ("COMPLETA" if not fallidos else f"con errores en: {', '.join(fallidos)}"))
    sys.exit(1 if fallidos else 0)


if __name__ == "__main__":
    main()
