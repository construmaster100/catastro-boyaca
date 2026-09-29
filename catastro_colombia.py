"""
Descarga la informacion catastral del IGAC (predios URBANOS y RURALES, con
numero catastral y geometria) de todo el pais y la organiza en carpetas por
departamento y municipio:

    catastro/
      indice_municipios.csv
      08_ATLANTICO/
        08421_LURUACO/
          urbano.geojson, urbano.shp (+ .shx .dbf .prj .cpg)
          rural.geojson,  rural.shp  (+ ...)
          predios.csv      (atributos + coordenadas del centroide, para Excel)
          metadata.json    (fuente, fecha, sistema de coordenadas, conteos)

Funciona en dos fases (ver README.md):

  1. descargar : baja las capas completas del IGAC por bloques de 2000 predios
                 a la carpeta crudo/. Tarda horas. Se puede interrumpir y
                 reanudar (incluso copiando la carpeta a otro equipo).
  2. organizar : reparte lo descargado en catastro/DEPARTAMENTO/MUNICIPIO/.
                 Es local (no usa internet) y se puede repetir cuando se quiera.

Uso:
    python catastro_colombia.py            # descargar + organizar
    python catastro_colombia.py descargar
    python catastro_colombia.py organizar
    python catastro_colombia.py estado     # muestra el avance
"""
import csv
import gzip
import json
import math
import shutil
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import requests
import shapefile  # pyshp

SERVICIO = "https://mapas.igac.gov.co/server/rest/services/Dato_Fundamental_Catastro/MapServer"
CAPAS = {"urbano": 4, "rural": 1}  # U_TERRENO, R_TERRENO
DIVIPOLA = "https://www.datos.gov.co/resource/gdxc-w37w.json?$limit=5000"

CARPETA = Path(__file__).parent
CRUDO = CARPETA / "crudo"          # fase 1: bloques descargados (.json.gz)
TEMPORAL = CARPETA / "_organizar"  # fase 2: archivos intermedios, se borra al final
RAIZ = CARPETA / "catastro"        # fase 2: resultado final

TAM_BLOQUE = 2000   # maximo de registros por consulta del servidor
HILOS = 3           # consultas simultaneas; no subir mucho para no saturar el servidor
VACIOS_FIN = 25     # bloques vacios seguidos para considerar que se llego al final

# MAGNA-SIRGAS geografico (EPSG:4686), para el .prj del shapefile
PRJ_4686 = ('GEOGCS["MAGNA-SIRGAS",DATUM["Marco_Geocentrico_Nacional_de_Referencia",'
            'SPHEROID["GRS 1980",6378137,298.257222101]],PRIMEM["Greenwich",0],'
            'UNIT["degree",0.0174532925199433]]')

COLUMNAS = ["ZONA", "NUMERO_CATASTRAL", "NUMERO_CATASTRAL_ANTERIOR", "MANZANA_VEREDA",
            "NUMERO_SUB", "AREA_M2", "LONGITUD", "LATITUD"]

sesion = requests.Session()


# ================================================================ utilidades

def limpiar(texto):
    """'NARIÑO' -> 'NARINO', 'San Andrés' -> 'SAN_ANDRES' (nombres de carpeta seguros)."""
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = "".join(c if c.isalnum() else "_" for c in t.upper())
    return "_".join(p for p in t.split("_") if p)


def _get(url, params, intentos=5):
    for i in range(intentos):
        try:
            r = sesion.get(url, params=params, timeout=200)
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                raise RuntimeError(data["error"])
            return data
        except Exception:
            if i == intentos - 1:
                raise
            time.sleep(10 * (i + 1))


def _area_signo(anillo):
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(anillo, anillo[1:])) / 2


def esri_a_geojson(rings):
    """Anillos Esri -> Polygon/MultiPolygon GeoJSON.
    En Esri los anillos exteriores van en sentido horario y los huecos antihorario;
    GeoJSON usa lo contrario, asi que se invierten."""
    if not rings:
        return None
    poligonos = []
    for anillo in rings:
        if _area_signo(anillo) < 0 or not poligonos:  # horario = exterior
            poligonos.append([anillo[::-1]])
        else:                                          # hueco del exterior anterior
            poligonos[-1].append(anillo[::-1])
    if len(poligonos) == 1:
        return {"type": "Polygon", "coordinates": poligonos[0]}
    return {"type": "MultiPolygon", "coordinates": poligonos}


def _anillo_area_centroide(anillo):
    """Area (m2, aproximada) y centroide (lon, lat) de un anillo en grados."""
    lat0 = math.radians(sum(p[1] for p in anillo) / len(anillo))
    # metros por grado a esa latitud (elipsoide GRS80, aproximacion estandar)
    my = 111132.92 - 559.82 * math.cos(2 * lat0) + 1.175 * math.cos(4 * lat0)
    mx = 111412.84 * math.cos(lat0) - 93.5 * math.cos(3 * lat0)
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(anillo, anillo[1:]):
        c = x1 * y2 - x2 * y1
        a += c
        cx += (x1 + x2) * c
        cy += (y1 + y2) * c
    if a == 0:
        return 0.0, anillo[0][0], anillo[0][1]
    return abs(a / 2) * mx * my, cx / (3 * a), cy / (3 * a)


def area_y_centroide(geom):
    """Area total en m2 y centroide del poligono mas grande."""
    if not geom:
        return None, None, None
    poligonos = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    total, mayor = 0.0, (-1.0, None, None)
    for pol in poligonos:
        area_ext, lon, lat = _anillo_area_centroide(pol[0])
        total += area_ext - sum(_anillo_area_centroide(h)[0] for h in pol[1:])
        if area_ext > mayor[0]:
            mayor = (area_ext, lon, lat)
    return round(total, 2), round(mayor[1], 7), round(mayor[2], 7)


# ================================================================ fase 1: descargar

def _bloque_existente(carpeta, inicio):
    return next(carpeta.glob(f"{inicio:09d}_*.json.gz"), None)


def bajar_bloque(zona, inicio):
    """Descarga los predios con FID en (inicio, inicio + TAM_BLOQUE] y los guarda
    en crudo/<zona>/<inicio>_<cantidad>.json.gz. Devuelve la cantidad (o None si fallo).

    Notas del servidor del IGAC que explican este metodo:
    - No soporta paginacion y no tiene indice sobre CODIGO: filtrar por municipio
      recorre todo el pais en cada consulta. Filtrar por FID (indexado) si es rapido.
    - f=geojson y outSR son extremadamente lentos: se pide Esri JSON en su
      sistema nativo (que ya es EPSG:4686)."""
    carpeta = CRUDO / zona
    existente = _bloque_existente(carpeta, inicio)
    if existente:
        return int(existente.name.split("_")[1].split(".")[0])
    campos = "FID,CODIGO,CODIGO_ANT,NUMERO_SUB," + ("MANZANA_CO" if zona == "urbano" else "VEREDA_COD")
    try:
        data = _get(f"{SERVICIO}/{CAPAS[zona]}/query", {
            "where": f"FID > {inicio} AND FID <= {inicio + TAM_BLOQUE}",
            "outFields": campos,
            "returnGeometry": "true",
            "f": "json",
        })
    except Exception as e:
        print(f"    ERROR bloque {zona} {inicio}: {e} (se reintentara en la proxima ejecucion)", flush=True)
        return None
    feats = [{"a": f.get("attributes", {}), "g": (f.get("geometry") or {}).get("rings")}
             for f in data.get("features", [])]
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / f"{inicio:09d}_{len(feats)}.json.gz"
    tmp = destino.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        json.dump(feats, fh, separators=(",", ":"))
    tmp.replace(destino)  # si se corta a mitad, no queda un bloque incompleto
    return len(feats)


def descargar():
    for zona in CAPAS:
        marca = CRUDO / zona / "_COMPLETO"
        if marca.exists():
            print(f"{zona}: descarga ya completa")
            continue
        print(f"{zona}: descargando (Ctrl+C para pausar; se reanuda donde iba)", flush=True)
        inicio_t, inicio, vacios, fallidos, total = time.time(), 0, 0, 0, 0
        with ThreadPoolExecutor(HILOS) as ex:
            while True:
                lote = [inicio + i * TAM_BLOQUE for i in range(HILOS * 4)]
                for n in ex.map(lambda a: bajar_bloque(zona, a), lote):
                    if n is None:
                        fallidos += 1
                        vacios = 0
                    else:
                        total += n
                        vacios = vacios + 1 if n == 0 else 0
                inicio = lote[-1] + TAM_BLOQUE
                print(f"  {zona}: FID {inicio:,} | {total:,} predios | "
                      f"{(time.time() - inicio_t) / 60:.0f} min", flush=True)
                if vacios >= VACIOS_FIN:
                    break
        if fallidos:
            print(f"{zona}: {fallidos} bloques fallaron. Vuelve a ejecutar 'descargar' para completarlos.")
        else:
            marca.write_text(f"{total} predios, {date.today().isoformat()}", encoding="utf-8")
            print(f"{zona}: descarga completa ({total:,} predios)")


def estado():
    for zona in CAPAS:
        bloques = list((CRUDO / zona).glob("*.json.gz"))
        predios = sum(int(b.name.split("_")[1].split(".")[0]) for b in bloques)
        ultimo = max((int(b.name.split("_")[0]) for b in bloques), default=0)
        completo = (CRUDO / zona / "_COMPLETO").exists()
        mb = sum(b.stat().st_size for b in bloques) / 1e6
        print(f"{zona}: {'COMPLETO' if completo else 'en progreso'} | {len(bloques)} bloques | "
              f"{predios:,} predios | hasta FID {ultimo + TAM_BLOQUE:,} | {mb:,.0f} MB")
    print("Referencia: la capa rural tiene 3.146.345 predios en total.")


# ================================================================ fase 2: organizar

def escribir_geojson(ruta, feats):
    fc = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4686"}},
        "features": [{"type": "Feature", "geometry": g, "properties": fila} for g, fila in feats],
    }
    ruta.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")


def escribir_shapefile(base, feats):
    with shapefile.Writer(str(base), shapeType=shapefile.POLYGON, encoding="utf-8") as w:
        w.field("ZONA", "C", 6)
        w.field("NUM_CATAST", "C", 30)
        w.field("NUM_ANTER", "C", 20)
        w.field("MANZ_VERED", "C", 17)
        w.field("NUM_SUB", "N", 10, 0)
        w.field("AREA_M2", "N", 18, 2)
        w.field("LONGITUD", "N", 14, 7)
        w.field("LATITUD", "N", 14, 7)
        for g, fila in feats:
            w.shape(g) if g else w.null()
            w.record(*(fila[c] for c in COLUMNAS))
    base.with_suffix(".prj").write_text(PRJ_4686, encoding="ascii")
    base.with_suffix(".cpg").write_text("UTF-8", encoding="ascii")


def _repartir():
    """Lee todos los bloques y los separa en un archivo temporal por municipio y zona."""
    if TEMPORAL.exists():
        shutil.rmtree(TEMPORAL)
    for zona in CAPAS:
        bloques = sorted((CRUDO / zona).glob("*.json.gz"))
        (TEMPORAL / zona).mkdir(parents=True)
        for i, b in enumerate(bloques, 1):
            with gzip.open(b, "rt", encoding="utf-8") as fh:
                feats = json.load(fh)
            grupos = {}
            for f in feats:
                mpio = (f["a"].get("CODIGO") or "")[:5] or "SIN_CODIGO"
                grupos.setdefault(mpio, []).append(f)
            for mpio, lista in grupos.items():
                with open(TEMPORAL / zona / f"{mpio}.ndjson", "a", encoding="utf-8") as out:
                    for f in lista:
                        out.write(json.dumps(f, separators=(",", ":")) + "\n")
            if i % 100 == 0 or i == len(bloques):
                print(f"  repartiendo {zona}: {i}/{len(bloques)} bloques", flush=True)


def _cargar(zona, mpio):
    ruta = TEMPORAL / zona / f"{mpio}.ndjson"
    if not ruta.exists():
        return []
    vistos, feats = set(), []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        f = json.loads(linea)
        fid = f["a"].get("FID")
        if fid in vistos:
            continue
        vistos.add(fid)
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


def organizar(forzar=False):
    if not forzar and not all((CRUDO / z / "_COMPLETO").exists() for z in CAPAS):
        sys.exit("La descarga no esta completa. Ejecuta primero 'descargar' "
                 "(o usa 'organizar --forzar' para organizar lo que haya).")
    print("Leyendo lista de municipios (DIVIPOLA, DANE)...")
    divipola = {d["cod_mpio"]: d for d in _get(DIVIPOLA, {})}
    print("Repartiendo predios por municipio...")
    _repartir()
    con_datos = {p.stem for z in CAPAS for p in (TEMPORAL / z).glob("*.ndjson")}
    todos = sorted(set(divipola) | con_datos)

    if RAIZ.exists():
        shutil.rmtree(RAIZ)
    indice = []
    for i, mpio in enumerate(todos, 1):
        d = divipola.get(mpio, {"cod_dpto": mpio[:2], "dpto": "DESCONOCIDO",
                                "cod_mpio": mpio, "nom_mpio": "SIN_NOMBRE_DIVIPOLA"})
        carpeta = RAIZ / f"{d['cod_dpto']}_{limpiar(d['dpto'])}" / f"{mpio}_{limpiar(d['nom_mpio'])}"
        carpeta.mkdir(parents=True, exist_ok=True)
        conteos, archivos, filas = {}, [], []
        for zona in CAPAS:
            feats = _cargar(zona, mpio)
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
        meta = {
            "codigo_departamento": d["cod_dpto"],
            "departamento": d["dpto"],
            "codigo_municipio": mpio,
            "municipio": d["nom_mpio"],
            "estado": "con_datos" if filas else "sin_datos_igac",
            "predios_urbanos": conteos["urbano"],
            "predios_rurales": conteos["rural"],
            "archivos": archivos,
            "sistema_coordenadas": "EPSG:4686 (MAGNA-SIRGAS, grados)",
            "fuente": SERVICIO,
            "capas": {"urbano": "U_TERRENO (4)", "rural": "R_TERRENO (1)"},
            "fecha_organizacion": date.today().isoformat(),
            "nota_area": "AREA_M2 calculada a partir de la geometria (aproximacion elipsoidal local).",
        }
        (carpeta / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        indice.append({
            "CODIGO_DEPARTAMENTO": d["cod_dpto"], "DEPARTAMENTO": d["dpto"],
            "CODIGO_MUNICIPIO": mpio, "MUNICIPIO": d["nom_mpio"], "ESTADO": meta["estado"],
            "PREDIOS_URBANOS": conteos["urbano"], "PREDIOS_RURALES": conteos["rural"],
            "CARPETA": carpeta.relative_to(RAIZ).as_posix(),
        })
        if i % 50 == 0 or i == len(todos):
            print(f"  organizados {i}/{len(todos)} municipios", flush=True)

    with open(RAIZ / "indice_municipios.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(indice[0]))
        w.writeheader()
        w.writerows(indice)
    shutil.rmtree(TEMPORAL)
    con = sum(1 for f in indice if f["ESTADO"] == "con_datos")
    print(f"Listo: {len(indice)} municipios ({con} con datos) en {RAIZ}")


# ================================================================ principal

if __name__ == "__main__":
    args = sys.argv[1:]
    orden = args[0] if args else "todo"
    if orden == "descargar":
        descargar()
    elif orden == "organizar":
        organizar(forzar="--forzar" in args)
    elif orden == "estado":
        estado()
    elif orden == "todo":
        descargar()
        organizar()
    else:
        sys.exit(__doc__)
