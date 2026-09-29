"""
Exporta las capas del proyecto en la carpeta geo/, listas para abrir con la extension de VS Code
"Geo Data Viewer" (randomfractalsinc.geo-data-viewer, basada en kepler.gl):
clic derecho sobre el archivo -> "Geo: View Map" (o Ctrl+Shift+P -> "Geo: View Map").

    geo/boyaca_municipios.geojson     123 municipios (limite oficial) con areas, jerarquia urbana,
                                      indicadores CCT 2024 y uso del suelo de sus predios
    geo/boyaca_municipios_puntos.csv  lo mismo como puntos (centro del municipio) para mapas de calor
    geo/boyaca_provincias.geojson     13 provincias con sus totales
    geo/boyaca_zonas_urbanas.geojson  zonas urbanas (cabeceras y centros poblados)
    geo/boyaca_contorno.geojson       contorno del departamento

Uso: python exportar_geo.py   (despues de exportar_web.py, estadisticas_urbanas.py e importar_cct.py)
"""
import csv
import json
from pathlib import Path

from shapely.geometry import shape

CARPETA = Path(__file__).parent
DATOS = CARPETA / "visor" / "datos"
GEO = CARPETA / "geo"


def leer(nombre):
    return json.loads((DATOS / nombre).read_text(encoding="utf-8"))


def uso_suelo(archivo):
    """Criterio del usuario: urbano = actividad economica; rural 10-300 m2 = vivienda; > 300 m2 = agropecuario."""
    r = {"pred_urbanos": 0, "pred_vivienda_rural": 0, "pred_agropecuarios": 0, "pred_atipicos": 0,
         "ha_urbana_predios": 0.0, "ha_vivienda_rural": 0.0, "ha_agropecuaria": 0.0}
    for f in json.loads((DATOS / archivo).read_text(encoding="utf-8"))["features"]:
        p = f["properties"]
        a = p.get("AREA_M2") or 0
        if p["ZONA"] == "URBANO":
            r["pred_urbanos"] += 1; r["ha_urbana_predios"] += a / 1e4
        elif a < 10:
            r["pred_atipicos"] += 1
        elif a <= 300:
            r["pred_vivienda_rural"] += 1; r["ha_vivienda_rural"] += a / 1e4
        else:
            r["pred_agropecuarios"] += 1; r["ha_agropecuaria"] += a / 1e4
    return {k: round(v, 2) if isinstance(v, float) else v for k, v in r.items()}


def guardar(nombre, feats):
    (GEO / nombre).write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False,
                                         separators=(",", ":")), encoding="utf-8")
    print(f"  geo/{nombre}: {len(feats)} elementos")


def main():
    GEO.mkdir(exist_ok=True)
    indice = leer("indice.json")
    est = leer("estadisticas.json")["municipios"]
    ind = leer("indicadores.json")["municipios"]
    muns = {m["codigo"]: m for d in indice["departamentos"] for m in d["municipios"]}
    feats, filas = [], []
    print("Calculando uso del suelo de los 123 municipios...")
    for f in leer("limites.json")["features"]:
        cod = str(f["properties"]["CODIGO"]).zfill(5)
        m, s, d = muns.get(cod, {}), est.get(cod, {}), ind.get(cod, {})
        props = {"codigo": cod, "municipio": (m.get("nombre") or "").title(), "provincia": d.get("provincia"),
                 "predios_urbanos_igac": m.get("urbanos"), "predios_rurales_igac": m.get("rurales"),
                 "area_km2": s.get("area_km2"), "area_urbana_ha": s.get("urbana_ha"), "pct_urbano": s.get("pct_urbana"),
                 "pct_rural": s.get("pct_rural"), "pct_de_boyaca": s.get("pct_departamento"),
                 "jerarquia_urbana": s.get("jerarquia"), "categoria_urbana": s.get("categoria")}
        props.update({k: v for k, v in d.items() if k != "provincia"})
        if d.get("poblacion") and s.get("area_km2"):
            props["densidad_hab_km2"] = round(d["poblacion"] / s["area_km2"], 2)
        if d.get("valor_agregado") and d.get("poblacion"):
            props["valor_agregado_por_hab_millones"] = round(d["valor_agregado"] * 1000 / d["poblacion"], 3)
        if m.get("archivo"):
            props.update(uso_suelo(m["archivo"]))
        feats.append({"type": "Feature", "properties": props, "geometry": f["geometry"]})
        c = shape(f["geometry"]).representative_point()
        filas.append({"latitud": round(c.y, 6), "longitud": round(c.x, 6), **props})
    feats.sort(key=lambda x: x["properties"]["codigo"])
    guardar("boyaca_municipios.geojson", feats)
    with open(GEO / "boyaca_municipios_puntos.csv", "w", newline="", encoding="utf-8") as fh:
        campos = list(dict.fromkeys(k for fila in filas for k in fila))
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(sorted(filas, key=lambda x: x["codigo"]))
    print(f"  geo/boyaca_municipios_puntos.csv: {len(filas)} filas")

    # provincias con totales
    prov = leer("provincias.json")["features"]
    for f in prov:
        miembros = [x["properties"] for x in feats if x["properties"].get("provincia") == f["properties"]["PROVINCIA"]]
        suma = lambda k: round(sum(p.get(k) or 0 for p in miembros), 2)
        f["properties"] = {"provincia": f["properties"]["PROVINCIA"], "municipios": len(miembros),
                           "poblacion": suma("poblacion"), "area_km2": suma("area_km2"),
                           "valor_agregado": suma("valor_agregado"), "area_urbana_ha": suma("area_urbana_ha"),
                           "pred_urbanos": suma("pred_urbanos"), "pred_agropecuarios": suma("pred_agropecuarios"),
                           "ha_agropecuaria": suma("ha_agropecuaria")}
        f["properties"]["densidad_hab_km2"] = round(f["properties"]["poblacion"] / f["properties"]["area_km2"], 2)
    guardar("boyaca_provincias.geojson", prov)

    zonas = leer("zonas_urbanas.json")["features"]
    for z in zonas:
        cod = z["properties"]["CODIGO"]
        z["properties"] = {"codigo": cod, "municipio": (muns.get(cod, {}).get("nombre") or "").title(),
                           "tipo": "Cabecera municipal" if z["properties"]["TIPO"] == "cabecera" else "Centros poblados",
                           "provincia": ind.get(cod, {}).get("provincia")}
    guardar("boyaca_zonas_urbanas.geojson", zonas)
    guardar("boyaca_contorno.geojson", leer("departamentos.json")["features"])


if __name__ == "__main__":
    main()
