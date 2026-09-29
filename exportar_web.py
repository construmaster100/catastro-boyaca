"""
Exporta los datos del visor web (visor/datos/) a partir de catastro/, en un formato
liviano: un archivo por municipio (urbano + rural juntos), coordenadas con 6
decimales (~10 cm) y sin puntos repetidos. Tambien descarga los limites
municipales oficiales del IGAC para dibujarlos en el mapa.

La carpeta visor/ queda autocontenida: se puede subir tal cual a un hosting
estatico (Netlify, Cloudflare Pages, GitHub Pages, un servidor web propio).

Uso:
    python exportar_web.py              # solo Boyaca (prueba inicial)
    python exportar_web.py 15 25 68     # departamentos a incluir
"""
import csv
import json
import sys
from datetime import date
from pathlib import Path

import requests

from catastro_colombia import esri_a_geojson

CARPETA = Path(__file__).parent
RAIZ = CARPETA / "catastro"
SALIDA = CARPETA / "visor" / "datos"
LIMITES = ("https://mapas.igac.gov.co/server/rest/services/ordenamientoterritorial/"
           "pendientepromediomunicipio/MapServer/0/query")
DECIMALES = 6


def redondear_anillo(anillo):
    salida = []
    for x, y in anillo:
        p = [round(x, DECIMALES), round(y, DECIMALES)]
        if not salida or p != salida[-1]:
            salida.append(p)
    return salida


def redondear(geom):
    if geom["type"] == "Polygon":
        return {"type": "Polygon", "coordinates": [redondear_anillo(a) for a in geom["coordinates"]]}
    return {"type": "MultiPolygon",
            "coordinates": [[redondear_anillo(a) for a in pol] for pol in geom["coordinates"]]}


def recuadro(feats):
    xs, ys = [], []
    for f in feats:
        g = f["geometry"]
        for pol in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
            for x, y in pol[0]:
                xs.append(x)
                ys.append(y)
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def exportar_municipio(fila):
    feats = []
    for zona in ("urbano", "rural"):
        ruta = RAIZ / fila["CARPETA"] / f"{zona}.geojson"
        if not ruta.exists():
            continue
        for f in json.loads(ruta.read_text(encoding="utf-8"))["features"]:
            if f["geometry"]:
                feats.append({"type": "Feature", "geometry": redondear(f["geometry"]),
                              "properties": f["properties"]})
    if not feats:
        return None
    destino = SALIDA / f"{fila['CODIGO_MUNICIPIO']}.json"
    destino.write_text(json.dumps({"type": "FeatureCollection", "features": feats},
                                  ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return recuadro(feats), destino.stat().st_size


def descargar_limites(deptos):
    """Poligonos oficiales de los municipios (IGAC), simplificados a ~30 m."""
    with open(RAIZ / "indice_municipios.csv", encoding="utf-8-sig") as fh:
        codigos = [f["CODIGO_MUNICIPIO"] for f in csv.DictReader(fh)]
    feats = []
    for d in deptos:
        print(f"  limites municipales del departamento {d} (servidor IGAC, puede tardar)...", flush=True)
        lista = ",".join(f"'{c}'" for c in codigos if c.startswith(d))
        try:
            # El servidor no filtra bien por rangos de texto: se pide la lista exacta de codigos.
            # f=json (Esri) es mucho mas rapido que f=geojson en este servidor; se convierte aqui
            r = requests.post(LIMITES, timeout=300, data={
                "where": f"CODIGO IN ({lista})",
                "outFields": "CODIGO,NOMBRE_ENT", "returnGeometry": "true",
                "outSR": "4326", "maxAllowableOffset": "0.0003", "geometryPrecision": "5",
                "f": "json"})
            r.raise_for_status()
            nuevos = [{"type": "Feature", "properties": f["attributes"],
                       "geometry": esri_a_geojson(f["geometry"]["rings"])}
                      for f in r.json().get("features", []) if f.get("geometry")]
            feats += nuevos
            print(f"    {len(nuevos)} municipios")
        except Exception as e:
            print(f"    no se pudieron descargar ({e}); el visor usara recuadros")
    return feats


def main(deptos):
    SALIDA.mkdir(parents=True, exist_ok=True)
    with open(RAIZ / "indice_municipios.csv", encoding="utf-8-sig") as fh:
        filas = [f for f in csv.DictReader(fh) if f["CODIGO_DEPARTAMENTO"] in deptos]
    indice = {}
    total = 0
    for i, f in enumerate(filas, 1):
        res = exportar_municipio(f)
        dep = indice.setdefault(f["CODIGO_DEPARTAMENTO"], {
            "codigo": f["CODIGO_DEPARTAMENTO"], "nombre": f["DEPARTAMENTO"], "municipios": []})
        dep["municipios"].append({
            "codigo": f["CODIGO_MUNICIPIO"], "nombre": f["MUNICIPIO"],
            "urbanos": int(f["PREDIOS_URBANOS"] or 0), "rurales": int(f["PREDIOS_RURALES"] or 0),
            "bbox": res[0] if res else None, "archivo": f"{f['CODIGO_MUNICIPIO']}.json" if res else None})
        total += res[1] if res else 0
        if i % 20 == 0 or i == len(filas):
            print(f"  exportados {i}/{len(filas)} municipios ({total / 1e6:,.0f} MB)", flush=True)
    (SALIDA / "indice.json").write_text(json.dumps(
        {"generado": date.today().isoformat(), "departamentos": sorted(indice.values(), key=lambda d: d["codigo"])},
        ensure_ascii=False), encoding="utf-8")
    limites = descargar_limites(deptos)
    if limites:
        (SALIDA / "limites.json").write_text(json.dumps(
            {"type": "FeatureCollection", "features": limites}, separators=(",", ":")), encoding="utf-8")
    contorno_departamentos()
    print(f"Listo: visor/datos/ ({total / 1e6:,.0f} MB de predios, {len(limites)} limites municipales)")


def contorno_departamentos():
    """Une los limites municipales de cada departamento en un solo contorno (departamentos.json)."""
    from shapely.geometry import mapping, shape
    from shapely.ops import unary_union
    ruta = SALIDA / "limites.json"
    if not ruta.exists():
        return
    por_dep = {}
    for f in json.loads(ruta.read_text(encoding="utf-8"))["features"]:
        cod = str(f["properties"]["CODIGO"]).zfill(5)
        por_dep.setdefault(cod[:2], []).append(shape(f["geometry"]).buffer(0))
    feats = []
    for dep, geoms in sorted(por_dep.items()):
        union = unary_union([g.buffer(0.0005) for g in geoms]).buffer(-0.0005)  # cierra rendijas entre municipios
        feats.append({"type": "Feature", "properties": {"CODIGO": dep},
                      "geometry": mapping(union.simplify(0.0002))})
    (SALIDA / "departamentos.json").write_text(json.dumps(
        {"type": "FeatureCollection", "features": feats}, separators=(",", ":")), encoding="utf-8")
    print(f"Contorno de {len(feats)} departamento(s) -> visor/datos/departamentos.json")


def solo_limites(deptos):
    limites = descargar_limites(deptos)
    if limites:
        (SALIDA / "limites.json").write_text(json.dumps(
            {"type": "FeatureCollection", "features": limites}, separators=(",", ":")), encoding="utf-8")
    print(f"Listo: {len(limites)} limites municipales")
    contorno_departamentos()


if __name__ == "__main__":
    deptos = [a.zfill(2) for a in sys.argv[1:] if not a.startswith("--")] or ["15"]
    if "--solo-contorno" in sys.argv:
        contorno_departamentos()
    elif "--solo-limites" in sys.argv:
        solo_limites(deptos)
    else:
        main(deptos)
