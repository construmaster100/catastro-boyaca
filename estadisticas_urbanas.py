"""
Zonas urbanas y estadisticas de area por municipio (para el visor).

- Zona urbana: union de los predios urbanos (capa U_TERRENO) de cada municipio. Se "cierran"
  las calles entre manzanas con un buffer de +CIERRE m y luego -CIERRE m.
  Se separa la cabecera municipal (zona 01) de los centros poblados (zonas 02-99).
- Area del municipio: poligono del limite municipal oficial (visor/datos/limites.json).
- Salidas:
    visor/datos/zonas_urbanas.json   contornos urbanos (lon/lat) para dibujar
    visor/datos/estadisticas.json    areas, porcentajes y jerarquia urbana por municipio

Uso: python estadisticas_urbanas.py
"""
import json
import math
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import transform, unary_union

DATOS = Path(__file__).parent / "visor" / "datos"
CIERRE = 12          # metros para unir manzanas separadas por calles
MIN_ISLA = 2000      # m2: se descartan fragmentos urbanos menores

# Categorias de la jerarquia urbana segun el area urbana (hectareas)
CATEGORIAS = [(1000, "Ciudad principal"), (300, "Ciudad intermedia"), (100, "Centro urbano menor"),
              (30, "Centro urbano local"), (0, "Núcleo urbano básico")]


def proyeccion_local(lat0):
    """Metros locales (aproximacion elipsoidal GRS80, la misma del calculo de areas de predios)."""
    r = math.radians(lat0)
    my = 111132.92 - 559.82 * math.cos(2 * r) + 1.175 * math.cos(4 * r)
    mx = 111412.84 * math.cos(r) - 93.5 * math.cos(3 * r)
    ida = lambda x, y, z=None: (x * mx, y * my)
    vuelta = lambda x, y, z=None: (x / mx, y / my)
    return ida, vuelta


def categoria(ha):
    return next(nombre for minimo, nombre in CATEGORIAS if ha >= minimo)


def main():
    indice = json.loads((DATOS / "indice.json").read_text(encoding="utf-8"))
    limites = {str(f["properties"]["CODIGO"]).zfill(5): shape(f["geometry"]).buffer(0)
               for f in json.loads((DATOS / "limites.json").read_text(encoding="utf-8"))["features"]}
    stats, contornos, omitidos = {}, [], 0
    muns = [m for d in indice["departamentos"] for m in d["municipios"]]
    for i, m in enumerate(muns, 1):
        cod = m["codigo"]
        lim = limites.get(cod)
        lat0 = (lim.bounds[1] + lim.bounds[3]) / 2 if lim else (m["bbox"][1] + m["bbox"][3]) / 2
        ida, vuelta = proyeccion_local(lat0)
        area_mun = transform(ida, lim).area if lim else None
        cabecera = otros = None
        if m.get("archivo"):
            fc = json.loads((DATOS / m["archivo"]).read_text(encoding="utf-8"))
            grupos = {"cabecera": [], "centros": []}
            for f in fc["features"]:
                p = f["properties"]
                if p["ZONA"] != "URBANO" or not f["geometry"]:
                    continue
                try:
                    g = transform(ida, shape(f["geometry"]))
                except ValueError:                        # geometria defectuosa (anillo degenerado): se omite
                    omitidos += 1
                    continue
                grupos["cabecera" if p["NUMERO_CATASTRAL"][5:7] == "01" else "centros"].append(g.buffer(CIERRE, 4))
            for tipo, geoms in grupos.items():
                if not geoms:
                    continue
                zona = unary_union(geoms).buffer(-CIERRE, 4)
                partes = [p for p in getattr(zona, "geoms", [zona]) if p.area >= MIN_ISLA]
                if not partes:
                    continue
                zona = unary_union(partes)
                if lim:                                   # la zona urbana no puede salirse del municipio
                    zona = zona.intersection(transform(ida, lim))
                if tipo == "cabecera":
                    cabecera = zona
                else:
                    otros = zona
                contornos.append({"type": "Feature", "properties": {"CODIGO": cod, "TIPO": tipo},
                                  "geometry": mapping(transform(vuelta, zona.simplify(1.5)))})
        a_cab = cabecera.area if cabecera else 0
        a_otr = otros.area if otros else 0
        a_urb = a_cab + a_otr
        stats[cod] = {
            "area_km2": round(area_mun / 1e6, 2) if area_mun else None,
            "urbana_ha": round(a_urb / 1e4, 2),
            "cabecera_ha": round(a_cab / 1e4, 2),
            "centros_poblados_ha": round(a_otr / 1e4, 2),
            "pct_urbana": round(100 * a_urb / area_mun, 3) if area_mun else None,
            "pct_rural": round(100 - 100 * a_urb / area_mun, 3) if area_mun else None,
        }
        if i % 10 == 0 or i == len(muns):
            print(f"  {i}/{len(muns)} municipios", flush=True)

    total = sum(s["area_km2"] or 0 for s in stats.values())
    orden = sorted(stats, key=lambda c: stats[c]["urbana_ha"], reverse=True)
    for puesto, cod in enumerate(orden, 1):
        s = stats[cod]
        s["pct_departamento"] = round(100 * (s["area_km2"] or 0) / total, 3) if total else None
        s["jerarquia"] = puesto
        s["categoria"] = categoria(s["urbana_ha"])
    (DATOS / "estadisticas.json").write_text(json.dumps(
        {"area_departamento_km2": round(total, 2), "categorias": [[a, n] for a, n in CATEGORIAS], "municipios": stats},
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (DATOS / "zonas_urbanas.json").write_text(json.dumps(
        {"type": "FeatureCollection", "features": contornos}, separators=(",", ":")), encoding="utf-8")
    print(f"Area de Boyaca (suma de municipios): {total:,.0f} km2 | predios con geometria defectuosa omitidos: {omitidos}")
    for cod in orden[:10]:
        s = stats[cod]
        print(f"  {s['jerarquia']:>3}. {cod} {s['urbana_ha']:>9,.1f} ha urbanas  {s['pct_urbana']:.2f}% del municipio  {s['categoria']}")


if __name__ == "__main__":
    main()
