"""
Scraper de "Boyaca en Cifras" (Camara de Comercio de Tunja).
https://cctunja.org.co/estudios-economicos/boyaca-en-cifras/

Crea el repositorio visor/camara/ con toda la informacion publicada en la pagina:

    visor/camara/archivos/          copia local de cada PDF y Excel publicado
    visor/camara/catalogo.json      documentos (titulo, anio, tipo, paginas, tamano, indice de contenido),
                                    tableros Power BI y textos de la pagina
    visor/camara/basemun.json       base municipal 2024 (123 municipios x 51 variables)
    visor/camara/baseboy.json       comparativo departamental 2020-2024 (PIB, desempleo, pobreza, Gini...)
    visor/camara/hojas/<hoja>.json  todas las hojas del Excel, fila por fila
    visor/camara/analisis.html      informe de analisis (generado por analisis_cct.py)

Se puede ejecutar varias veces: solo descarga lo que falta.
Uso: python scraper_cct.py
"""
import html as html_lib
import json
import re
import unicodedata
import warnings
from datetime import date
from pathlib import Path
from urllib.parse import unquote

import openpyxl
import requests

URL = "https://cctunja.org.co/estudios-economicos/boyaca-en-cifras/"
CARPETA = Path(__file__).parent
DESTINO = CARPETA / "visor" / "camara"
ARCHIVOS = DESTINO / "archivos"
UA = {"User-Agent": "Mozilla/5.0 (catastro-boyaca; investigacion)"}
warnings.filterwarnings("ignore")


def limpio(t):
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", t or ""))).strip()


def nombre_archivo(url):
    n = unquote(url.rsplit("/", 1)[-1])
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9._-]+", "_", n)


def titulo_de(url, texto_enlace):
    n = unquote(url.rsplit("/", 1)[-1]).rsplit(".", 1)[0]
    n = re.sub(r"[-_]+", " ", n).strip()
    if "auditoria" in n.lower():
        return "Informe de auditoría externa CCT"
    if "herramienta" in n.lower():
        return "Herramienta tecnológica (Excel) Boyacá en Cifras 2024"
    if "infograf" in n.lower():
        return "Infografía Boyacá en Cifras 2019-2020"
    anios = re.findall(r"20\d\d", n)
    if anios:
        return "Boyacá en Cifras " + "-".join(sorted(set(anios)))
    return texto_enlace or n


def indice_pdf(ruta):
    """Paginas y tabla de contenido (marcadores del PDF o, si no tiene, lineas '....... N' de las primeras paginas)."""
    import pypdf
    r = pypdf.PdfReader(str(ruta))
    paginas = len(r.pages)
    indice = []

    def recorrer(items, nivel=0):
        for it in items:
            if isinstance(it, list):
                recorrer(it, nivel + 1)
            else:
                try:
                    indice.append({"t": str(it.title).strip(), "p": r.get_destination_page_number(it) + 1, "n": nivel})
                except Exception:
                    pass
    try:
        recorrer(r.outline)
    except Exception:
        pass
    if not indice:
        patron = re.compile(r"^\s*((?:\d+(?:\.\d+)*\.?\s+)?[A-ZÁÉÍÓÚÑ][^\n]{3,110}?)\s*\.{4,}\s*(\d{1,3})\s*$")
        for i in range(min(12, paginas)):
            texto = r.pages[i].extract_text() or ""
            for linea in texto.splitlines():
                m = patron.match(linea)
                if m and 0 < int(m.group(2)) <= paginas:
                    t = m.group(1).strip()
                    nivel = t.split(" ")[0].count(".") if re.match(r"^\d", t) else 0
                    indice.append({"t": t, "p": int(m.group(2)), "n": min(nivel, 2)})
    vistos, unicos = set(), []
    for e in indice:
        if (e["t"], e["p"]) not in vistos:
            vistos.add((e["t"], e["p"]))
            unicos.append(e)
    return paginas, unicos[:250]


def excel_a_json(ruta):
    wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    (DESTINO / "hojas").mkdir(exist_ok=True)
    hojas = []
    for ws in wb.worksheets:
        filas = [[(round(v, 4) if isinstance(v, float) else v) for v in f] for f in ws.iter_rows(values_only=True)]
        filas = [f for f in filas if any(v is not None for v in f)]
        (DESTINO / "hojas" / f"{nombre_archivo(ws.title)}.json").write_text(
            json.dumps({"hoja": ws.title, "filas": filas}, ensure_ascii=False, default=str), encoding="utf-8")
        hojas.append({"hoja": ws.title, "archivo": f"hojas/{nombre_archivo(ws.title)}.json", "filas": len(filas)})
    # base municipal estructurada
    f = [list(x) for x in wb["BaseMun"].iter_rows(values_only=True)]
    grupos, grupo = [], ""
    for g in f[0]:
        grupo = str(g).strip() if g else grupo
        grupos.append(grupo)
    columnas = [{"k": str(c).strip(), "grupo": grupos[i]} for i, c in enumerate(f[1])]
    filas = [[(round(v, 3) if isinstance(v, float) else v) for v in r] for r in f[2:] if r[0]]
    (DESTINO / "basemun.json").write_text(json.dumps({"columnas": columnas, "filas": filas}, ensure_ascii=False), encoding="utf-8")
    # comparativo departamental
    f = [list(x) for x in wb["BaseBoy"].iter_rows(values_only=True)]
    cols = [str(c).strip() for c in f[0]]
    deps = {r[0]: {cols[i]: (round(v, 4) if isinstance(v, float) else v) for i, v in enumerate(r) if i} for r in f[1:] if r[0]}
    (DESTINO / "baseboy.json").write_text(json.dumps({"columnas": cols[1:], "departamentos": deps}, ensure_ascii=False), encoding="utf-8")
    return hojas


def main():
    ARCHIVOS.mkdir(parents=True, exist_ok=True)
    print("1/4 Leyendo la pagina...")
    pagina = requests.get(URL, timeout=60, headers=UA).text
    titulo_pag = limpio((re.search(r"<title>(.*?)</title>", pagina, re.S) or [None, ""])[1])
    parrafos = [limpio(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", pagina, re.S)]
    parrafos = [p for p in parrafos if len(p) > 60][:12]
    enlaces = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', pagina, re.S)
    docs, tableros, vistos = [], [], set()
    for url, texto in enlaces:
        url = html_lib.unescape(url).strip()
        if url in vistos:
            continue
        if "powerbi" in url.lower():
            vistos.add(url)
            tableros.append({"titulo": "Tablero Power BI" + (" " + limpio(texto) if limpio(texto) else ""), "url": url})
        elif re.search(r"\.(pdf|xlsx?)$", url, re.I):
            vistos.add(url)
            docs.append({"url": url, "texto": limpio(texto)})
    print(f"   {len(docs)} archivos y {len(tableros)} tableros Power BI")

    print("2/4 Descargando archivos (solo los que faltan)...")
    catalogo = []
    for d in docs:
        nombre = nombre_archivo(d["url"])
        ruta = ARCHIVOS / nombre
        if not ruta.exists():
            r = requests.get(d["url"], timeout=300, headers=UA)
            r.raise_for_status()
            ruta.write_bytes(r.content)
            print(f"   descargado {nombre} ({len(r.content) / 1e6:.1f} MB)")
        tipo = "Excel" if nombre.lower().endswith((".xlsx", ".xls")) else "PDF"
        anios = re.findall(r"20\d\d", nombre)
        catalogo.append({"titulo": titulo_de(d["url"], d["texto"]), "tipo": tipo, "anio": max(anios) if anios else "",
                         "archivo": f"archivos/{nombre}", "url": d["url"], "mb": round(ruta.stat().st_size / 1e6, 1)})

    print("3/4 Indices de los PDF y datos del Excel...")
    hojas = []
    for c in catalogo:
        ruta = DESTINO / c["archivo"]
        if c["tipo"] == "PDF":
            try:
                c["paginas"], c["indice"] = indice_pdf(ruta)
            except Exception as e:
                c["paginas"], c["indice"] = None, []
                print(f"   aviso: no se pudo leer {ruta.name}: {e}")
            print(f"   {c['titulo']}: {c['paginas']} paginas, {len(c['indice'])} entradas de indice")
        else:
            hojas = excel_a_json(ruta)
            c["hojas"] = hojas
            print(f"   {c['titulo']}: {len(hojas)} hojas convertidas")
    catalogo.sort(key=lambda c: (c["anio"], c["tipo"] == "Excel"), reverse=True)

    print("4/4 Guardando catalogo...")
    (DESTINO / "catalogo.json").write_text(json.dumps({
        "fuente": "Cámara de Comercio de Tunja", "pagina": URL, "titulo_pagina": titulo_pag,
        "descripcion": parrafos, "consultado": date.today().isoformat(),
        "documentos": catalogo, "tableros": tableros}, ensure_ascii=False, indent=1), encoding="utf-8")
    # informe de analisis como HTML (si existe)
    md = CARPETA / "informes" / "analisis_boyaca_en_cifras.md"
    if md.exists():
        try:
            import markdown
            cuerpo = markdown.markdown(md.read_text(encoding="utf-8"), extensions=["tables"])
            (DESTINO / "analisis.html").write_text(cuerpo, encoding="utf-8")
        except ImportError:
            print("   (instale 'markdown' para convertir el informe: pip install markdown)")
    total = sum(c["mb"] for c in catalogo)
    print(f"Listo: {len(catalogo)} documentos ({total:,.0f} MB), {len(tableros)} tableros -> visor/camara/")


if __name__ == "__main__":
    main()
