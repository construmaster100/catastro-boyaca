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

LEEME = """CATASTRO BOYACA - VERSION OFFLINE (AUTOPORTANTE)
================================================

Para abrir: doble clic en ABRIR_VISOR_OFFLINE.bat
Se abre el navegador en http://localhost:8766/ . Deje abierta la ventana negra mientras lo usa.

- No necesita internet ni instalar programas (usa PowerShell, incluido en Windows).
- Sin internet no se ve el mapa de fondo (calles/satelite); todo lo demas funciona: predios, limites,
  zonas urbanas, provincias, cifras, fichas, graficos, documentos de la Camara de Comercio y Excel.
- Documentos y Excel: carpeta docs\\   Capas para Geo Data Viewer: carpeta geo\\
- Esta copia se genera desde la carpeta de trabajo con: python construir_versiones.py --offline
"""


def copiar_incremental(origen, destino):
    """Copia solo archivos nuevos o modificados; elimina del destino lo que ya no existe en el origen."""
    nuevos = 0
    for f in origen.rglob("*"):
        rel = f.relative_to(origen)
        if any(p in (".git", "__pycache__") for p in rel.parts) or f.suffix == ".log":
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
        if not (origen / d.relative_to(destino)).exists():
            shutil.rmtree(d) if d.is_dir() else d.unlink()
            borrados += 1
    return nuevos, borrados


def offline():
    OFFLINE.mkdir(exist_ok=True)
    for c in CARPETAS_OFFLINE:
        if (CARPETA / c).exists():
            n, b = copiar_incremental(CARPETA / c, OFFLINE / c)
            print(f"  {c}/: {n} copiados, {b} eliminados")
    for a in ARCHIVOS_OFFLINE:
        if not (OFFLINE / a).exists() or not filecmp.cmp(CARPETA / a, OFFLINE / a, shallow=False):
            shutil.copy2(CARPETA / a, OFFLINE / a)
    (OFFLINE / "LEEME.txt").write_text(LEEME, encoding="utf-8")
    total = sum(f.stat().st_size for f in OFFLINE.rglob("*") if f.is_file()) / 1e9
    print(f"Copia OFFLINE lista: {OFFLINE} ({total:.2f} GB). Abrir con ABRIR_VISOR_OFFLINE.bat")


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
