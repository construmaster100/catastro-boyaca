"""
Extrae a Excel el contenido de los documentos descargados por scraper_cct.py (docs/camara_comercio/).

Por cada seccion genera, dentro de su carpeta:

    texto_<seccion>.xlsx   hoja "Texto": documento, anio, pagina y texto completo de cada pagina (para buscar/filtrar)
                           hoja "Resumen": paginas y caracteres por documento
    tablas_<seccion>.xlsx  hoja "Indice": cada tabla detectada (documento, pagina, titulo, filas x columnas)
                           una hoja por tabla (T001, T002, ...) con sus celdas

Las tablas se buscan en las paginas que mencionan "Tabla" o "Cuadro" (asi se acelera el proceso).
Solo procesa las secciones cuyo Excel no existe o es mas antiguo que sus documentos.

Uso: python extraer_cct.py            (todas las secciones)
     python extraer_cct.py tejido-empresarial boletin-economico
"""
import json
import re
import sys
import warnings
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

CARPETA = Path(__file__).parent
DOCS = CARPETA / "docs" / "camara_comercio"
CATALOGO = CARPETA / "visor" / "camara" / "catalogo.json"
MAX_CELDA = 32000          # limite de caracteres por celda en Excel
ILEGALES = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
warnings.filterwarnings("ignore")


def celda(v):
    if v is None:
        return None
    v = ILEGALES.sub("", str(v)).strip()
    num = v.replace(".", "").replace(",", ".").replace("%", "").replace("$", "").strip()
    if re.fullmatch(r"-?\d+(\.\d+)?", num) and len(num) < 16:      # cifras en formato colombiano -> numero
        try:
            return float(num) if "." in num else int(num)
        except ValueError:
            pass
    return v[:MAX_CELDA]


def cabecera(ws, titulos, anchos):
    ws.append(titulos)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="0F4D2E")
        c.alignment = Alignment(vertical="center", wrap_text=True)
    for i, a in enumerate(anchos, 1):
        ws.column_dimensions[get_column_letter(i)].width = a
    ws.freeze_panes = "A2"


def procesar(slug, docs):
    import pdfplumber
    import pypdf
    carpeta = DOCS / slug
    pdfs = [d for d in docs if d["tipo"] == "PDF" and (carpeta / Path(d["archivo"]).name).exists()]
    if not pdfs:
        return
    wt = openpyxl.Workbook()
    ws_txt = wt.active
    ws_txt.title = "Texto"
    cabecera(ws_txt, ["Documento", "Año", "Página", "Texto"], [60, 8, 8, 120])
    ws_res = wt.create_sheet("Resumen")
    cabecera(ws_res, ["Documento", "Año", "Páginas", "Caracteres", "Páginas con tablas", "Tablas extraídas", "Archivo"], [60, 8, 9, 12, 14, 12, 60])
    wtab = openpyxl.Workbook()
    ws_ind = wtab.active
    ws_ind.title = "Indice"
    cabecera(ws_ind, ["Hoja", "Documento", "Año", "Página", "Título de la tabla", "Filas", "Columnas"], [8, 55, 8, 8, 80, 8, 9])
    n_tabla = 0
    for d in pdfs:
        ruta = carpeta / Path(d["archivo"]).name
        try:
            lector = pypdf.PdfReader(str(ruta))
            textos = [(p.extract_text() or "") for p in lector.pages]
        except Exception as e:
            print(f"   aviso: {ruta.name}: {e}")
            continue
        for i, t in enumerate(textos, 1):
            ws_txt.append([d["titulo"], d["anio"], i, ILEGALES.sub("", t)[:MAX_CELDA]])
        paginas_tabla = [i for i, t in enumerate(textos) if re.search(r"(?i)\b(tabla|cuadro)\s*\d", t)]
        extraidas = 0
        try:
            with pdfplumber.open(str(ruta)) as pdf:
                for i in paginas_tabla:
                    titulos = re.findall(r"(?im)^\s*((?:tabla|cuadro)\s*\d+[^\n]{0,150})", textos[i])
                    for k, tabla in enumerate(pdf.pages[i].extract_tables()):
                        filas = [[celda(c) for c in f] for f in tabla if f and any(c not in (None, "") for c in f)]
                        if len(filas) < 2 or max(len(f) for f in filas) < 2:
                            continue
                        n_tabla += 1
                        extraidas += 1
                        hoja = f"T{n_tabla:03d}"
                        titulo = titulos[k] if k < len(titulos) else (titulos[-1] if titulos else "")
                        ws = wtab.create_sheet(hoja)
                        ws.append([f"{d['titulo']} · página {i + 1}"])
                        ws.append([titulo.strip()])
                        ws["A1"].font = Font(bold=True)
                        ws["A2"].font = Font(italic=True)
                        for f in filas:
                            ws.append(f)
                        ws_ind.append([hoja, d["titulo"], d["anio"], i + 1, titulo.strip(), len(filas), max(len(f) for f in filas)])
                        ws_ind.cell(ws_ind.max_row, 1).hyperlink = f"#'{hoja}'!A1"
        except Exception as e:
            print(f"   aviso tablas {ruta.name}: {e}")
        ws_res.append([d["titulo"], d["anio"], len(textos), sum(len(t) for t in textos), len(paginas_tabla), extraidas,
                       f"docs/camara_comercio/{slug}/{ruta.name}"])
        print(f"   {ruta.name}: {len(textos)} págs, {extraidas} tablas", flush=True)
    ws_txt.auto_filter.ref = ws_txt.dimensions
    ws_ind.auto_filter.ref = ws_ind.dimensions
    wt.save(carpeta / f"texto_{slug}.xlsx")
    wtab.save(carpeta / f"tablas_{slug}.xlsx")
    print(f"== {slug}: texto_{slug}.xlsx y tablas_{slug}.xlsx ({n_tabla} tablas)", flush=True)
    return n_tabla


def main():
    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    pedidas = sys.argv[1:] or [s["slug"] for s in cat["secciones"]]
    total = 0
    for slug in pedidas:
        docs = [d for d in cat["documentos"] if d["slug"] == slug]
        salida = DOCS / slug / f"tablas_{slug}.xlsx"
        mas_nuevo = max(((DOCS / slug / Path(d["archivo"]).name).stat().st_mtime for d in docs
                         if (DOCS / slug / Path(d["archivo"]).name).exists()), default=0)
        if salida.exists() and salida.stat().st_mtime > mas_nuevo and not sys.argv[1:]:
            print(f"== {slug}: ya extraida (sin documentos nuevos)")
            continue
        print(f"== {slug}: {len(docs)} documentos", flush=True)
        total += procesar(slug, docs) or 0
    print(f"Listo: {total} tablas extraidas a Excel")


if __name__ == "__main__":
    main()
