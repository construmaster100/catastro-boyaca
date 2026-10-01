"""
Arquitectura de versiones del proyecto Catastro Boyaca (3 copias en este computador):

    1. TRABAJO   Escritorio\\Database                   donde se edita y se ejecuta actualizar_todo.py
    2. ONLINE    Escritorio\\Catastro_Boyaca_ONLINE     clon del repositorio GitHub (construmaster100/catastro-boyaca)
    3. OFFLINE   Escritorio\\Catastro_Boyaca_OFFLINE    copia AUTOPORTANTE: visor + documentos + datos + servidor
                                                      PowerShell; funciona sin internet y sin instalar Python

Uso:
    python construir_versiones.py --offline    crea o actualiza la copia offline (solo copia lo que cambio)
    python construir_versiones.py --online     clona o actualiza (git pull) la copia online
"""
import filecmp
import json
import shutil
import subprocess
import sys
from pathlib import Path

CARPETA = Path(__file__).parent
ESCRITORIO = CARPETA.parent
OFFLINE = ESCRITORIO / "Catastro_Boyaca_OFFLINE"
ONLINE = ESCRITORIO / "Catastro_Boyaca_ONLINE"
REMOTO = "https://github.com/construmaster100/catastro-boyaca.git"

# lo que necesita la version offline (sin los datos crudos pesados ni el codigo de descarga)
CARPETAS_OFFLINE = ["visor", "docs", "geo", "informes"]
ARCHIVOS_OFFLINE = ["servidor_offline.ps1", "ABRIR_VISOR_OFFLINE.bat", "README.md"]
IGNORAR = shutil.ignore_patterns("*.log", "__pycache__", "~$*", "Thumbs.db", "desktop.ini", ".git")

LEEME = r"""CATASTRO BOYACA - VERSION OFFLINE (AUTOPORTANTE)
================================================

Para abrir: doble clic en ABRIR_VISOR.html  (o en visor\\index.html).
No necesita internet, ni Python, ni ventana negra: los datos de los predios vienen en archivos .json.js
que el navegador carga directamente desde el disco.

Alternativa: ABRIR_VISOR_OFFLINE.bat (servidor PowerShell en http://localhost:8766/).

- Sin internet no se ve el mapa de fondo (calles/satelite); todo lo demas funciona: predios, limites,
  zonas urbanas, provincias, cifras, fichas, graficos, documentos de la Camara de Comercio y Excel.
- Documentos y Excel: carpeta docs\   Capas para Geo Data Viewer: carpeta geo\
- Esta copia se genera desde la carpeta de trabajo con: python construir_versiones.py --offline
"""


def es_dato_web(rel):
    """Archivos de datos del visor que en la copia offline se publican como .js (ver visor/lib/datos_archivo.js)."""
    p = rel.as_posix()
    return (p.startswith("visor/datos/") and p.endswith(".json")) or \
           (p.startswith("visor/camara/") and p.count("/") == 2 and (p.endswith(".json") or p.endswith("analisis.html")))


def datos_como_js(raiz_origen, raiz_destino):
    """visor/datos/x.json -> visor/datos/x.json.js con window.__D["datos/x.json"] = {...};  (se abre sin servidor)."""
    hechos = 0
    for f in (raiz_origen / "visor").rglob("*"):
        rel = f.relative_to(raiz_origen)
        if not f.is_file() or not es_dato_web(rel):
            continue
        destino = raiz_destino / (rel.as_posix() + ".js")
        if destino.exists() and destino.stat().st_mtime >= f.stat().st_mtime:
            continue
        clave = rel.relative_to("visor").as_posix()           # la ruta que usa el visor en fetch(), p. ej. datos/15001.json
        contenido = f.read_text(encoding="utf-8")
        valor = contenido if f.suffix == ".json" else json.dumps(contenido, ensure_ascii=False)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(f"window.__D=window.__D||{{}};window.__D[{json.dumps(clave)}]={valor};", encoding="utf-8")
        hechos += 1
    (raiz_destino / "visor" / "lib" / "modo_offline.js").write_text(
        "// Copia OFFLINE: los datos se cargan desde los archivos .json.js (funciona con doble clic en index.html).\n"
        "window.__SOLO_JS = true;\n", encoding="utf-8")
    return hechos


def copiar_incremental(origen, destino, raiz=None):
    """Copia solo archivos nuevos o modificados; elimina del destino lo que ya no existe en el origen.
    Los datos del visor no se copian como .json: se generan como .json.js (datos_como_js)."""
    raiz = raiz or origen.parent
    nuevos = 0
    for f in origen.rglob("*"):
        rel = f.relative_to(origen)
        if any(p in (".git", "__pycache__") for p in rel.parts) or f.suffix == ".log":
            continue
        if f.is_file() and (es_dato_web(f.relative_to(raiz)) or f.relative_to(raiz).as_posix() == "visor/lib/modo_offline.js"):
            continue
        d = destino / rel
        if f.is_dir():
            d.mkdir(parents=True, exist_ok=True)
        elif not d.exists() or f.stat().st_size != d.stat().st_size or f.stat().st_mtime > d.stat().st_mtime + 1:
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, d)
            nuevos += 1
    borrados = 0
    for d in sorted(destino.rglob("*"), reverse=True):
        rel = d.relative_to(destino)
        if d.name.endswith(".json.js") and (origen / str(rel)[:-3]).exists():
            continue                                         # dato generado para el modo sin servidor
        if d.is_file() and es_dato_web((destino / rel).relative_to(destino.parent)):
            d.unlink()                                       # .json de copias anteriores: ya no se necesitan
            borrados += 1
            continue
        if rel.as_posix() == "lib/modo_offline.js":
            continue
        if not (origen / rel).exists():
            shutil.rmtree(d) if d.is_dir() else d.unlink()
            borrados += 1
    return nuevos, borrados


def offline():
    OFFLINE.mkdir(exist_ok=True)
    for c in CARPETAS_OFFLINE:
        if (CARPETA / c).exists():
            n, b = copiar_incremental(CARPETA / c, OFFLINE / c)
            print(f"  {c}/: {n} copiados, {b} eliminados")
    print(f"  datos convertidos para abrir sin servidor: {datos_como_js(CARPETA, OFFLINE)} archivos")
    for a in ARCHIVOS_OFFLINE:
        if not (OFFLINE / a).exists() or not filecmp.cmp(CARPETA / a, OFFLINE / a, shallow=False):
            shutil.copy2(CARPETA / a, OFFLINE / a)
    acceso = OFFLINE / "ABRIR_VISOR.html"                    # acceso directo: doble clic, sin ventana negra
    acceso.write_text('<!doctype html><meta charset="utf-8"><title>Catastro Boyacá</title>'
                      '<meta http-equiv="refresh" content="0; url=visor/index.html">'
                      '<a href="visor/index.html">Abrir el visor Catastro Boyacá</a>', encoding="utf-8")
    (OFFLINE / "LEEME.txt").write_text(LEEME, encoding="utf-8")
    total = sum(f.stat().st_size for f in OFFLINE.rglob("*") if f.is_file()) / 1e9
    print(f"Copia OFFLINE lista: {OFFLINE} ({total:.2f} GB). Abrir con doble clic en ABRIR_VISOR.html")


def online():
    if (ONLINE / ".git").exists():
        subprocess.run(["git", "-C", str(ONLINE), "pull", "--ff-only"], check=True)
    else:
        subprocess.run(["git", "clone", REMOTO, str(ONLINE)], check=True)
    print(f"Copia ONLINE sincronizada con {REMOTO}: {ONLINE}")


if __name__ == "__main__":
    if "--offline" in sys.argv:
        offline()
    if "--online" in sys.argv:
        online()
    if not {"--offline", "--online"} & set(sys.argv):
        print(__doc__)
