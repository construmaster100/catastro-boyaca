"""
Prepara los datos del visor (visor/index.html).

1. Organiza en catastro/ SOLO los departamentos pedidos, a partir de lo que ya
   este descargado en crudo/ (no espera a que termine la descarga nacional y no
   borra los demas departamentos).
2. Genera catastro/visor_indice.json (departamentos -> municipios, con conteos y
   el recuadro de cada municipio) que usa el visor.

Uso:
    python preparar_visor.py                 # Boyaca y departamentos vecinos
    python preparar_visor.py 15 25 68        # departamentos (codigo DANE) a organizar
    python preparar_visor.py --solo-indice   # solo regenerar el indice (p. ej. tras 'organizar')
"""
import csv
import gzip
import json
import sys
from datetime import date
from pathlib import Path

from catastro_colombia import (CAPAS, COLUMNAS, CRUDO, RAIZ, SERVICIO, area_y_centroide,
                               escribir_geojson, escribir_shapefile, esri_a_geojson, limpiar)

# Boyaca y sus vecinos: Antioquia, Norte de Santander, Cundinamarca, Santander, Arauca, Casanare
POR_DEFECTO = ["15", "05", "54", "25", "68", "81", "85"]


def leer_nombres():
    """Nombres DANE desde catastro/indice_municipios.csv (ya existe, no usa internet)."""
    with open(RAIZ / "indice_municipios.csv", encoding="utf-8-sig") as fh:
        return {f["CODIGO_MUNICIPIO"]: f for f in csv.DictReader(fh)}


def extraer(deptos):
    """Recorre crudo/ y devuelve {zona: {mpio: [feats]}} solo de los departamentos pedidos."""
    marcas = [f'"CODIGO":"{d}' for d in deptos]
    datos = {z: {} for z in CAPAS}
    for zona in CAPAS:
        bloques = sorted((CRUDO / zona).glob("*.json.gz"))
        vistos = set()
        for i, b in enumerate(bloques, 1):
            with gzip.open(b, "rt", encoding="utf-8") as fh:
                texto = fh.read()
            if any(m in texto for m in marcas):  # filtro rapido antes de leer el JSON
                for f in json.loads(texto):
                    codigo = f["a"].get("CODIGO") or ""
                    fid = f["a"].get("FID")
                    if codigo[:2] in deptos and fid not in vistos:
                        vistos.add(fid)
                        datos[zona].setdefault(codigo[:5], []).append(f)
            if i % 200 == 0 or i == len(bloques):
                print(f"  {zona}: {i}/{len(bloques)} bloques revisados", flush=True)
    return datos


def convertir(zona, crudos):
    feats = []
    for f in crudos:
        a, geom = f["a"], esri_a_geojson(f["g"])
        area, lon, lat = area_y_centroide(geom)
        feats.append((geom, {
            "ZONA": zona.upper(),
            "NUMERO_CATASTRAL": a.get("CODIGO"),
            "NUMERO_CATASTRAL_ANTERIOR": a.get("CODIGO_ANT"),
            "MANZANA_VEREDA": a.get("MANZANA_CO") or a.get("VEREDA_COD"),
            "NUMERO_SUB": a.get("NUMERO_SUB"),
            "AREA_M2": area,
            "LONGITUD": lon,
            "LATITUD": lat,
        }))
    feats.sort(key=lambda f: f[1]["NUMERO_CATASTRAL"] or "")
    return feats


def organizar_deptos(deptos):
    nombres = leer_nombres()
    print(f"Extrayendo departamentos {', '.join(deptos)} de crudo/ ...")
    datos = extraer(deptos)
    mpios = sorted(m for m, d in nombres.items() if d["CODIGO_DEPARTAMENTO"] in deptos)
    filas_indice = []
    for mpio in mpios:
        d = nombres[mpio]
        carpeta = RAIZ / d["CARPETA"]
        carpeta.mkdir(parents=True, exist_ok=True)
        for viejo in carpeta.iterdir():
            viejo.unlink()
        conteos, archivos, filas = {}, [], []
        for zona in CAPAS:
            feats = convertir(zona, datos[zona].get(mpio, []))
            conteos[zona] = len(feats)
            if feats:
                escribir_geojson(carpeta / f"{zona}.geojson", feats)
                escribir_shapefile(carpeta / zona, feats)
                archivos += [f"{zona}.geojson", f"{zona}.shp"]
                filas += [f[1] for f in feats]
        if filas:
            with open(carpeta / "predios.csv", "w", newline="", encoding="utf-8-sig") as fh:
                w = csv.DictWriter(fh, fieldnames=COLUMNAS)
                w.writeheader()
                w.writerows(filas)
            archivos.append("predios.csv")
        estado = "con_datos" if filas else "sin_datos_igac"
        meta = {
            "codigo_departamento": d["CODIGO_DEPARTAMENTO"], "departamento": d["DEPARTAMENTO"],
            "codigo_municipio": mpio, "municipio": d["MUNICIPIO"], "estado": estado,
            "predios_urbanos": conteos["urbano"], "predios_rurales": conteos["rural"],
            "archivos": archivos, "sistema_coordenadas": "EPSG:4686 (MAGNA-SIRGAS, grados)",
            "fuente": SERVICIO, "capas": {"urbano": "U_TERRENO (4)", "rural": "R_TERRENO (1)"},
            "fecha_organizacion": date.today().isoformat(),
            "nota": "Organizado con preparar_visor.py a partir de una descarga parcial.",
        }
        (carpeta / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        nombres[mpio].update(ESTADO=estado, PREDIOS_URBANOS=conteos["urbano"],
                             PREDIOS_RURALES=conteos["rural"])
        filas_indice.append(mpio)
    with open(RAIZ / "indice_municipios.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(next(iter(nombres.values()))))
        w.writeheader()
        w.writerows(nombres.values())
    print(f"Organizados {len(filas_indice)} municipios.")


def recuadro(ruta):
    """[oeste, sur, este, norte] de un GeoJSON."""
    xs, ys = [], []
    fc = json.loads(ruta.read_text(encoding="utf-8"))
    for f in fc["features"]:
        g = f["geometry"]
        if not g:
            continue
        pols = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for pol in pols:
            for x, y in pol[0]:
                xs.append(x)
                ys.append(y)
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def generar_indice():
    nombres = leer_nombres()
    deptos = {}
    for m in nombres.values():
        dep = deptos.setdefault(m["CODIGO_DEPARTAMENTO"], {
            "codigo": m["CODIGO_DEPARTAMENTO"], "nombre": m["DEPARTAMENTO"], "municipios": []})
        item = {"codigo": m["CODIGO_MUNICIPIO"], "nombre": m["MUNICIPIO"], "carpeta": m["CARPETA"],
                "urbanos": int(m["PREDIOS_URBANOS"] or 0), "rurales": int(m["PREDIOS_RURALES"] or 0),
                "bbox": None}
        cajas = [recuadro(RAIZ / m["CARPETA"] / f"{z}.geojson") for z in CAPAS
                 if (RAIZ / m["CARPETA"] / f"{z}.geojson").exists()]
        cajas = [c for c in cajas if c]
        if cajas:
            item["bbox"] = [min(c[0] for c in cajas), min(c[1] for c in cajas),
                            max(c[2] for c in cajas), max(c[3] for c in cajas)]
        dep["municipios"].append(item)
    salida = {"generado": date.today().isoformat(), "departamentos": sorted(deptos.values(), key=lambda d: d["codigo"])}
    (RAIZ / "visor_indice.json").write_text(json.dumps(salida, ensure_ascii=False), encoding="utf-8")
    con = sum(1 for d in deptos.values() for m in d["municipios"] if m["bbox"])
    print(f"Indice del visor listo: {con} municipios con datos -> {RAIZ / 'visor_indice.json'}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--solo-indice" not in args:
        organizar_deptos([a.zfill(2) for a in args] or POR_DEFECTO)
    generar_indice()
