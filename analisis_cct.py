"""
Analisis de la pagina "Boyaca en Cifras" (Camara de Comercio de Tunja) y de su base de datos.

1. Recorre la pagina y lista sus fuentes (ediciones, PDF, Excel, Power BI) con tamano y tipo.
2. Evalua la calidad de la base economica municipal (hoja BaseMun del Excel 2024):
   cobertura, completitud por variable, consistencia interna y contra los totales departamentales.
3. Estadisticas economicas: concentracion del valor agregado, provincias, per capita.
4. Coincidencias entre los municipios de la pagina y los del repositorio (codigo DANE y nombre),
   y cruce con los datos propios (predios, area, zona urbana).

Salidas:  informes/analisis_boyaca_en_cifras.md  y  informes/coincidencias_municipios.csv
Uso:      python analisis_cct.py
"""
import csv
import json
import re
import unicodedata
import warnings
from datetime import date
from pathlib import Path

import openpyxl
import pandas as pd
import requests

URL = "https://cctunja.org.co/estudios-economicos/boyaca-en-cifras/"
CARPETA = Path(__file__).parent
EXCEL = CARPETA / "fuentes" / "Boyaca-en-Cifras-2024_CCTunja.xlsx"
DATOS = CARPETA / "visor" / "datos"
SALIDA = CARPETA / "informes"
warnings.filterwarnings("ignore")


def norm(t):
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", " ", t).strip()


def fmt(x, d=0):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ 1. la pagina
def recorrer_pagina():
    html = requests.get(URL, timeout=60, headers={"User-Agent": "Mozilla/5.0"}).text
    enlaces = sorted(set(re.findall(r'href="([^"]+)"', html)))
    fuentes = []
    for u in enlaces:
        if not re.search(r"\.(pdf|xlsx?|csv)$|powerbi", u, re.I):
            continue
        tipo = "Power BI" if "powerbi" in u.lower() else u.rsplit(".", 1)[-1].upper()
        anio = re.findall(r"(20\d\d)", u.rsplit("/", 1)[-1]) or re.findall(r"/(20\d\d)/", u)
        tam = None
        if tipo != "Power BI":
            try:
                h = requests.head(u, timeout=30, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
                tam = int(h.headers.get("Content-Length", 0)) or None
            except requests.RequestException:
                pass
        fuentes.append({"tipo": tipo, "anio": max(anio) if anio else "", "url": u, "mb": round(tam / 1e6, 1) if tam else None})
    return fuentes


# ------------------------------------------------------------------ 2. la base municipal
def leer_base():
    wb = openpyxl.load_workbook(EXCEL, read_only=True, data_only=True)
    filas = list(wb["BaseMun"].iter_rows(values_only=True))
    df = pd.DataFrame(filas[2:], columns=[str(c).strip() for c in filas[1]])   # hay nombres con espacios al final
    df["codigo"] = df["Código"].astype(str).str[:5]
    dep = df[df["Provincia"] == "Departamento"].iloc[0]
    mun = df[df["codigo"].str.match(r"^15\d{3}$") & (df["Provincia"] != "Departamento")].copy()
    boy = [r for r in wb["BaseBoy"].iter_rows(values_only=True)]
    boy = dict(zip(boy[0], [r for r in boy if r[0] == "Boyacá"][0]))
    return mun, dep, boy


def calidad(mun, dep, boy):
    num = [c for c in mun.columns if c not in ("Código", "Municipio", "Provincia", "codigo", "Riesgo_2024")]
    for c in num:
        mun[c] = pd.to_numeric(mun[c], errors="coerce")
    completitud = {c: round(100 * mun[c].notna().mean(), 1) for c in num + ["Riesgo_2024"]}
    edades = ["0-6años", "7-14años", "15-17años", "18-26años", "27-59años", "60 o masaños"]
    pruebas = []

    def prueba(nombre, ok, total, detalle=""):
        pruebas.append({"prueba": nombre, "cumplen": int(ok), "total": int(total),
                        "pct": round(100 * ok / total, 1) if total else 0, "detalle": detalle})

    prueba("Hombres + Mujeres = Población total", (mun["N_Hombres"] + mun["N_Mujeres"] == mun["N_Total"]).sum(), len(mun))
    prueba("Suma de grupos de edad = Población total", (mun[edades].sum(axis=1) == mun["N_Total"]).sum(), len(mun))
    prueba("Canceladas ≤ matriculadas + renovadas", (mun["Can_2024"] <= mun["Mat_2024"] + mun["Ren_2024"]).sum(), len(mun))
    prueba("Empleos COMFABOY ≤ población de 18 a 59 años",
           (mun["Comf_Empleos"] <= mun["18-26años"] + mun["27-59años"]).sum(), mun["Comf_Empleos"].notna().sum())
    prueba("Códigos DANE únicos", mun["codigo"].nunique(), len(mun))
    # contra la fila "Departamento" y la hoja departamental
    tot = {
        "Población total": (mun["N_Total"].sum(), dep["N_Total"], boy.get("N_2024")),
        "Hombres": (mun["N_Hombres"].sum(), dep["N_Hombres"], None),
        "Mujeres": (mun["N_Mujeres"].sum(), dep["N_Mujeres"], None),
        "Valor agregado (miles de millones $)": (mun["VA_2024"].sum(), dep["VA_2024"], boy.get("PIB_2024")),
        "Empresas matriculadas": (mun["Mat_2024"].sum(), dep["Mat_2024"], None),
        "Empresas renovadas": (mun["Ren_2024"].sum(), dep["Ren_2024"], None),
        "Captaciones (millones $)": (mun["Fin_Captaciones"].sum(), dep["Fin_Captaciones"], None),
        "Colocaciones (millones $)": (mun["Fin_Colocaciones"].sum(), dep["Fin_Colocaciones"], None),
    }
    edades_dep = [dep[e] for e in edades]
    anomalias = []
    if len(set(edades_dep)) == 1:
        anomalias.append(f"Fila 'Departamento': los 6 grupos de edad tienen el mismo valor ({fmt(edades_dep[0])}); "
                         f"la suma municipal real es {', '.join(fmt(mun[e].sum()) for e in edades)}.")
    return completitud, pruebas, tot, anomalias


# ------------------------------------------------------------------ 3. economia
def economia(mun):
    m = mun.copy()
    m["va"] = pd.to_numeric(m["VA_2024"], errors="coerce")
    m["pob"] = pd.to_numeric(m["N_Total"], errors="coerce")
    m["va_pc_millones"] = m["va"] * 1000 / m["pob"]                       # miles de millones -> millones por habitante
    total = m["va"].sum()
    m["part"] = 100 * m["va"] / total
    orden = m.sort_values("va", ascending=False)
    hhi = ((m["part"]) ** 2).sum()
    prov = m.groupby("Provincia").agg(municipios=("codigo", "count"), va=("va", "sum"), pob=("pob", "sum"))
    prov["part_va"] = 100 * prov["va"] / total
    prov["va_pc"] = prov["va"] * 1000 / prov["pob"]
    return m, orden, hhi, prov.sort_values("va", ascending=False), total


# ------------------------------------------------------------------ 3b. uso del suelo segun los predios
# Criterio del usuario: la zona URBANA concentra la actividad economica; en la zona RURAL,
# los predios de 10 a 300 m2 son vivienda y los mayores a 300 m2 son de uso agropecuario.
VIVIENDA_MIN, VIVIENDA_MAX = 10, 300


def uso_suelo():
    indice = json.loads((DATOS / "indice.json").read_text(encoding="utf-8"))
    filas = []
    for d in indice["departamentos"]:
        for m in d["municipios"]:
            if not m.get("archivo"):
                continue
            fc = json.loads((DATOS / m["archivo"]).read_text(encoding="utf-8"))
            c = {"codigo": m["codigo"], "urb_n": 0, "urb_ha": 0.0, "viv_n": 0, "viv_ha": 0.0,
                 "agro_n": 0, "agro_ha": 0.0, "atip_n": 0}
            for f in fc["features"]:
                p = f["properties"]
                a = p.get("AREA_M2") or 0
                if p["ZONA"] == "URBANO":
                    c["urb_n"] += 1; c["urb_ha"] += a / 1e4
                elif a < VIVIENDA_MIN:
                    c["atip_n"] += 1
                elif a <= VIVIENDA_MAX:
                    c["viv_n"] += 1; c["viv_ha"] += a / 1e4
                else:
                    c["agro_n"] += 1; c["agro_ha"] += a / 1e4
            filas.append(c)
    return pd.DataFrame(filas)


# ------------------------------------------------------------------ 4. coincidencias con el repositorio
def coincidencias(mun):
    with open(CARPETA / "catastro" / "indice_municipios.csv", encoding="utf-8-sig") as fh:
        repo = {f["CODIGO_MUNICIPIO"]: f for f in csv.DictReader(fh) if f["CODIGO_DEPARTAMENTO"] == "15"}
    est = json.loads((DATOS / "estadisticas.json").read_text(encoding="utf-8"))["municipios"]
    filas = []
    for _, r in mun.iterrows():
        c = r["codigo"]
        rp = repo.get(c)
        nombre_repo = rp["MUNICIPIO"] if rp else ""
        if not rp:
            tipo = "Solo en la página"
        elif str(r["Municipio"]).strip().upper() == nombre_repo.upper():
            tipo = "Código y nombre idénticos"
        elif norm(r["Municipio"]) == norm(nombre_repo):
            tipo = "Código igual; nombre igual sin tildes/mayúsculas"
        else:
            tipo = "Código igual; nombre distinto"
        s = est.get(c, {})
        filas.append({
            "codigo": c, "municipio_pagina": str(r["Municipio"]).strip(), "municipio_repositorio": nombre_repo.title(),
            "provincia": r["Provincia"], "coincidencia": tipo,
            "predios_urbanos": int(rp["PREDIOS_URBANOS"]) if rp else None,
            "predios_rurales": int(rp["PREDIOS_RURALES"]) if rp else None,
            "poblacion_2024": r["N_Total"], "valor_agregado": r["VA_2024"],
            "empresas_renovadas": r["Ren_2024"], "produccion_agricola_ton": r["Prod(ton)_2023"], "bovinos": r["Bovino_2024"],
            "area_km2": s.get("area_km2"), "area_urbana_ha": s.get("urbana_ha"),
        })
    for c, rp in repo.items():
        if c not in set(mun["codigo"]):
            filas.append({"codigo": c, "municipio_pagina": "", "municipio_repositorio": rp["MUNICIPIO"].title(),
                          "provincia": "", "coincidencia": "Solo en el repositorio"})
    df = pd.DataFrame(filas)
    for c in ["predios_urbanos", "predios_rurales", "poblacion_2024", "valor_agregado", "area_km2", "area_urbana_ha",
              "empresas_renovadas", "produccion_agricola_ton", "bovinos"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["densidad_hab_km2"] = df["poblacion_2024"] / df["area_km2"]
    df["habitantes_por_predio_urbano"] = df["poblacion_2024"] / df["predios_urbanos"]
    return df


def main():
    SALIDA.mkdir(exist_ok=True)
    print("1/4 Recorriendo la página...")
    fuentes = recorrer_pagina()
    print("2/4 Calidad de la base municipal...")
    mun, dep, boy = leer_base()
    completitud, pruebas, tot, anomalias = calidad(mun, dep, boy)
    print("3/4 Estadísticas económicas...")
    m, orden, hhi, prov, total_va = economia(mun)
    print("4/4 Coincidencias con el repositorio...")
    co = coincidencias(mun)
    print("   clasificando predios por uso del suelo (123 municipios)...")
    uso = uso_suelo()
    co = co.merge(uso, on="codigo", how="left")
    co.to_csv(SALIDA / "coincidencias_municipios.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
    cuenta = co["coincidencia"].value_counts()
    corr = co[["valor_agregado", "poblacion_2024", "predios_urbanos", "area_urbana_ha"]].corr(method="pearson")

    L = [f"# Análisis de «Boyacá en Cifras» (Cámara de Comercio de Tunja)", "",
         f"Generado el {date.today():%d/%m/%Y} con `analisis_cct.py`. Página: <{URL}>", ""]
    L += ["## 1. Fuentes publicadas en la página", "", "| Tipo | Año | Tamaño | Enlace |", "|---|---|---|---|"]
    for f in sorted(fuentes, key=lambda x: (x["anio"], x["tipo"]), reverse=True):
        L.append(f"| {f['tipo']} | {f['anio']} | {fmt(f['mb'], 1) + ' MB' if f['mb'] else '—'} | [{f['url'].rsplit('/', 1)[-1][:60]}]({f['url']}) |")
    n_pdf = sum(f["tipo"] == "PDF" for f in fuentes)
    n_xls = sum(f["tipo"] in ("XLSX", "XLS") for f in fuentes)
    L += ["", f"Total: **{len(fuentes)} fuentes** ({n_pdf} PDF, {n_xls} Excel, "
              f"{sum(f['tipo'] == 'Power BI' for f in fuentes)} tablero Power BI).", ""]

    L += ["## 2. ¿Cuál es la base económica más precisa?", "",
          "**La herramienta Excel 2024 (hoja `BaseMun`)** es la fuente más completa y verificable de la página:",
          "", f"- Es la **única en formato de datos** (las ediciones 2015–2023 solo están en PDF; el Power BI no permite descarga ni verificación).",
          f"- Es la **más reciente** (cifras 2024; el ICM es 2023 y la producción agrícola 2023).",
          f"- Cubre **{len(mun)} de 123 municipios** con **{len(mun.columns) - 1} variables** y códigos DANE, lo que permite cruzarla con otras bases.",
          "", "### 2.1 Completitud por variable (% de municipios con dato)", "",
          "| Variable | % |", "|---|---|"]
    for c, p in sorted(completitud.items(), key=lambda x: x[1]):
        if p < 100:
            L.append(f"| {c} | {fmt(p, 1)} % |")
    completas = sum(1 for p in completitud.values() if p == 100)
    L += [f"| *las demás {completas} variables* | 100 % |", "", "### 2.2 Consistencia interna", "",
          "| Prueba | Cumplen | % |", "|---|---|---|"]
    for p in pruebas:
        L.append(f"| {p['prueba']} | {p['cumplen']} de {p['total']} | {fmt(p['pct'], 1)} % |")
    L += ["", "### 2.3 Suma de municipios frente a los totales del departamento", "",
          "| Variable | Suma de los 123 municipios | Fila «Departamento» (BaseMun) | Hoja departamental (BaseBoy) | Diferencia |",
          "|---|---|---|---|---|"]
    for k, (s, d, b) in tot.items():
        dif = f"{fmt(100 * (s - d) / d, 2)} %" if d else "—"
        L.append(f"| {k} | {fmt(s)} | {fmt(d)} | {fmt(b) if b else '—'} | {dif} |")
    va_s, va_d, va_b = tot["Valor agregado (miles de millones $)"]
    L += ["", "### 2.4 Anomalías detectadas", ""]
    for a in anomalias:
        L.append(f"- {a}")
    if va_b and abs(va_d - va_b) / va_b > 0.05:
        L.append(f"- **Valor agregado**: la base municipal suma {fmt(va_s)} y la hoja departamental reporta un PIB 2024 de "
                 f"{fmt(va_b)} (miles de millones), {fmt(100 * (va_d / va_b - 1), 1)} % más. Probablemente son precios "
                 "corrientes (municipal) frente a precios constantes (departamental); **no deben mezclarse** en un mismo cálculo.")
    L += ["- El ICM viene como **puesto** (1 = mejor), no como puntaje; y el riesgo del agua como categoría IRCA.", ""]

    L += ["## 3. Estadísticas económicas (valor agregado 2024)", "",
          f"- Valor agregado total (suma municipal): **{fmt(total_va)} miles de millones de pesos**.",
          f"- Los **3 mayores** ({', '.join(orden['Municipio'].head(3))}) concentran el "
          f"**{fmt(orden['part'].head(3).sum(), 1)} %**; los 10 mayores, el {fmt(orden['part'].head(10).sum(), 1)} %.",
          f"- Índice de concentración Herfindahl-Hirschman: **{fmt(hhi)}** "
          f"({'alta' if hhi > 2500 else 'moderada' if hhi > 1500 else 'baja'} concentración).",
          f"- Mediana municipal: {fmt(m['va'].median(), 1)} miles de millones; valor agregado por habitante: "
          f"mediana {fmt(m['va_pc_millones'].median(), 1)} millones $.", "",
          "| # | Municipio | Provincia | Valor agregado | % del depto. | Por habitante (millones $) |", "|---|---|---|---|---|---|"]
    for i, (_, r) in enumerate(orden.head(10).iterrows(), 1):
        L.append(f"| {i} | {r['Municipio']} | {r['Provincia']} | {fmt(r['va'], 1)} | {fmt(r['part'], 2)} % | {fmt(r['va_pc_millones'], 1)} |")
    L += ["", "**Por provincia**", "", "| Provincia | Municipios | Valor agregado | % | Por habitante (millones $) |",
          "|---|---|---|---|---|"]
    for p, r in prov.iterrows():
        L.append(f"| {p} | {int(r['municipios'])} | {fmt(r['va'], 1)} | {fmt(r['part_va'], 1)} % | {fmt(r['va_pc'], 1)} |")

    # ---- 3b. uso del suelo (criterio del usuario) y su relacion con la economia
    t = uso.sum(numeric_only=True)
    tot_pred = t["urb_n"] + t["viv_n"] + t["agro_n"] + t["atip_n"]
    L += ["", "## 3b. Uso del suelo según los predios (criterio del usuario)", "",
          f"- **Zona urbana** = actividad económica. **Zona rural**: predios de {VIVIENDA_MIN} a {VIVIENDA_MAX} m² = "
          f"**vivienda rural**; mayores a {VIVIENDA_MAX} m² = **uso agropecuario**; menores a {VIVIENDA_MIN} m² = atípicos (revisar).", "",
          "| Clase | Predios | % de predios | Área (ha) | % del área catastral |", "|---|---|---|---|---|"]
    area_tot = t["urb_ha"] + t["viv_ha"] + t["agro_ha"]
    for nombre, n, ha in [("Urbano (actividad económica)", t["urb_n"], t["urb_ha"]),
                          (f"Rural vivienda ({VIVIENDA_MIN}–{VIVIENDA_MAX} m²)", t["viv_n"], t["viv_ha"]),
                          (f"Rural agropecuario (> {VIVIENDA_MAX} m²)", t["agro_n"], t["agro_ha"]),
                          (f"Rural atípico (< {VIVIENDA_MIN} m²)", t["atip_n"], None)]:
        L.append(f"| {nombre} | {fmt(n)} | {fmt(100 * n / tot_pred, 1)} % | {fmt(ha, 0) if ha is not None else '—'} | "
                 f"{fmt(100 * ha / area_tot, 2) + ' %' if ha is not None else '—'} |")
    pruebas_uso = [
        ("Valor agregado ↔ predios urbanos", "valor_agregado", "urb_n"),
        ("Valor agregado ↔ área urbana de los predios", "valor_agregado", "urb_ha"),
        ("Empresas renovadas ↔ predios urbanos", "empresas_renovadas", "urb_n"),
        ("Producción agrícola (ton) ↔ área agropecuaria", "produccion_agricola_ton", "agro_ha"),
        ("Bovinos ↔ área agropecuaria", "bovinos", "agro_ha"),
        ("Población ↔ viviendas (predios urbanos + vivienda rural)", "poblacion_2024", "viviendas"),
    ]
    co["viviendas"] = co["urb_n"] + co["viv_n"]
    L += ["", "**¿Se cumple el criterio? Correlación con los indicadores económicos (Pearson y Spearman, 123 municipios)**", "",
          "| Relación | Pearson | Spearman (por rangos) | Lectura |", "|---|---|---|---|"]
    resumen_uso = []
    for nombre, a, b in pruebas_uso:
        rp, rs = co[a].corr(co[b]), co[a].rank().corr(co[b].rank())   # Spearman = Pearson sobre rangos
        lectura = "fuerte" if rs >= 0.7 else "moderada" if rs >= 0.4 else "débil"
        L.append(f"| {nombre} | {fmt(rp, 2)} | {fmt(rs, 2)} | {lectura} |")
        resumen_uso.append((nombre, rp, rs))
    part_va3 = orden["part"].head(3).sum()
    urb3 = co.set_index("municipio_pagina").loc[list(orden["Municipio"].head(3)), "urb_n"].sum() / t["urb_n"] * 100
    L += ["", f"- Los 3 municipios con más valor agregado tienen el **{fmt(urb3, 1)} %** de los predios urbanos del departamento "
              f"y generan el **{fmt(part_va3, 1)} %** del valor agregado: la actividad económica se concentra en lo urbano, "
              "como plantea el criterio.", ""]

    L += ["", "## 4. Coincidencias entre la página y el repositorio", "",
          "Se comparan los municipios de la página (Excel 2024) con los del repositorio (DIVIPOLA-DANE en "
          "`catastro/indice_municipios.csv`, que usa el visor).", "", "| Resultado | Municipios |", "|---|---|"]
    for k, v in cuenta.items():
        L.append(f"| {k} | {v} |")
    dist = co[co["coincidencia"].str.contains("distinto|Solo", regex=True)]
    if len(dist):
        L += ["", "**Diferencias de nombre o cobertura**", "", "| Código | Página | Repositorio | Resultado |", "|---|---|---|---|"]
        for _, r in dist.iterrows():
            L.append(f"| {r['codigo']} | {r['municipio_pagina']} | {r['municipio_repositorio']} | {r['coincidencia']} |")
    L += ["", "**Cruce con los datos propios (correlación de Pearson, 123 municipios)**", "",
          "| | Valor agregado | Población | Predios urbanos | Área urbana |", "|---|---|---|---|---|"]
    nombres = {"valor_agregado": "Valor agregado", "poblacion_2024": "Población", "predios_urbanos": "Predios urbanos",
               "area_urbana_ha": "Área urbana"}
    for a in corr.index:
        L.append(f"| {nombres[a]} | " + " | ".join(fmt(corr.loc[a, b], 2) for b in corr.columns) + " |")
    L += ["", f"- Habitantes por predio urbano: mediana {fmt(co['habitantes_por_predio_urbano'].median(), 1)}.",
          f"- Densidad: mediana {fmt(co['densidad_hab_km2'].median(), 1)} hab/km²; máxima "
          f"{fmt(co['densidad_hab_km2'].max(), 0)} ({co.loc[co['densidad_hab_km2'].idxmax(), 'municipio_pagina']}).",
          "", "El detalle municipio por municipio está en `informes/coincidencias_municipios.csv`.", ""]
    (SALIDA / "analisis_boyaca_en_cifras.md").write_text("\n".join(L), encoding="utf-8")

    print(f"\nFuentes en la página: {len(fuentes)} ({n_pdf} PDF, {n_xls} Excel)")
    for p in pruebas:
        print(f"  {p['prueba']}: {p['cumplen']}/{p['total']}")
    for k, (s, d, b) in tot.items():
        print(f"  {k}: municipios {fmt(s)} | fila depto {fmt(d)} | BaseBoy {fmt(b) if b else '-'}")
    print("Coincidencias:", dict(cuenta))
    print("Correlaciones:\n", corr.round(2))
    print(f"Top 3 VA: {list(orden['Municipio'].head(3))} = {orden['part'].head(3).sum():.1f} %  | HHI {hhi:.0f}")
    print(f"Uso del suelo: urbanos {fmt(t['urb_n'])} | vivienda rural {fmt(t['viv_n'])} | agropecuario {fmt(t['agro_n'])} "
          f"({fmt(t['agro_ha'])} ha) | atipicos {fmt(t['atip_n'])}")
    for nombre, rp, rs in resumen_uso:
        print(f"  {nombre}: Pearson {rp:.2f} | Spearman {rs:.2f}")
    print(f"  Top 3 VA tienen {urb3:.1f} % de predios urbanos y {part_va3:.1f} % del VA")
    print("Informe: informes/analisis_boyaca_en_cifras.md")


if __name__ == "__main__":
    main()
