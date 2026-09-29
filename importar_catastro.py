"""
Importa a pandas la informacion catastral publica del IGAC (la misma que
muestra https://www.colombiaenmapas.gov.co/ en el modulo catastral):

    - URBANO : capa U_TERRENO  (terrenos de predios urbanos)
    - RURAL  : capa R_TERRENO  (terrenos de predios rurales)
    - NUMERO CATASTRAL: CODIGO (numero predial nacional, 30 digitos)
                        CODIGO_ANT (numero predial anterior, 20 digitos)

Fuente: https://mapas.igac.gov.co/server/rest/services/Dato_Fundamental_Catastro/MapServer
Nota: solo cubre municipios donde el IGAC es gestor catastral (no incluye
Bogota, Medellin, Cali, Barranquilla, etc., que tienen gestor propio).

Uso:
    pip install pandas requests openpyxl
    python importar_catastro.py 08421          # codigo DANE del municipio (5 digitos)
    python importar_catastro.py 08421 --excel  # ademas exporta a Excel
"""
import sys
import time

import pandas as pd
import requests

SERVICIO = "https://mapas.igac.gov.co/server/rest/services/Dato_Fundamental_Catastro/MapServer"
CAPAS = {"URBANO": 4, "RURAL": 1}  # U_TERRENO, R_TERRENO
CAMPOS = "CODIGO,CODIGO_ANT,MANZANA_CO,VEREDA_COD,NUMERO_SUB,SHAPE_Area"
PAGINA = 2000  # maxRecordCount del servicio


def _get(url, params, intentos=3):
    for i in range(intentos):
        try:
            r = requests.get(url, params=params, timeout=120)
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                raise RuntimeError(data["error"])
            return data
        except Exception:
            if i == intentos - 1:
                raise
            time.sleep(3 * (i + 1))


def descargar_capa(capa_id, municipio):
    """Descarga todos los registros (sin geometria) de una capa para un municipio."""
    url = f"{SERVICIO}/{capa_id}/query"
    campos_capa = {f["name"] for f in _get(f"{SERVICIO}/{capa_id}", {"f": "json"})["fields"]}
    out_fields = ",".join(c for c in CAMPOS.split(",") if c in campos_capa)

    # El servicio no soporta paginacion (resultOffset): se piden primero los IDs
    # y luego los registros en bloques. Tampoco resuelve bien LIKE, asi que se
    # filtra por rango de texto.
    ids = _get(url, {
        "where": f"CODIGO >= '{municipio}' AND CODIGO < '{int(municipio) + 1:05d}'",
        "returnIdsOnly": "true",
        "f": "json",
    }).get("objectIds") or []
    ids.sort()

    filas = []
    for i in range(0, len(ids), PAGINA // 4):
        bloque = ids[i:i + PAGINA // 4]
        data = _get(url, {
            "objectIds": ",".join(map(str, bloque)),
            "outFields": out_fields,
            "returnGeometry": "false",
            "f": "json",
        })
        filas.extend(f["attributes"] for f in data.get("features", []))
        print(f"  capa {capa_id}: {len(filas)}/{len(ids)} registros...", end="\r")
    print()
    return pd.DataFrame(filas)


def importar(municipio):
    """Devuelve (df_urbano, df_rural, df_todo) para un codigo DANE de municipio."""
    dfs = {}
    for zona, capa_id in CAPAS.items():
        print(f"Descargando {zona} ({municipio})...")
        df = descargar_capa(capa_id, municipio)
        df.insert(0, "ZONA", zona)
        dfs[zona] = df

    todo = pd.concat(dfs.values(), ignore_index=True)
    todo = todo.rename(columns={
        "CODIGO": "NUMERO_CATASTRAL",
        "CODIGO_ANT": "NUMERO_CATASTRAL_ANTERIOR",
        # SHAPE_Area viene en grados cuadrados (EPSG:4686), NO en m2.
        # Para area en m2 usar catastro_colombia.py, que la calcula de la geometria.
        "SHAPE_Area": "AREA_GRADOS2",
    })
    # Desglose del numero predial nacional de 30 digitos
    nc = todo["NUMERO_CATASTRAL"].astype(str)
    todo["DEPARTAMENTO"] = nc.str[0:2]
    todo["MUNICIPIO"] = nc.str[2:5]
    todo["ZONA_COD"] = nc.str[5:7]  # 00 = rural, 01+ = urbano/corregimientos
    return dfs["URBANO"], dfs["RURAL"], todo


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv[1]) != 5 or not sys.argv[1].isdigit():
        sys.exit("Indica el codigo DANE del municipio (5 digitos). Ej: python importar_catastro.py 08421")

    municipio = sys.argv[1]
    urbano, rural, todo = importar(municipio)

    print(f"\nURBANO: {len(urbano)} predios | RURAL: {len(rural)} predios")
    print(todo.head())

    todo.to_csv(f"catastro_{municipio}.csv", index=False, encoding="utf-8-sig")
    print(f"Guardado: catastro_{municipio}.csv")
    if "--excel" in sys.argv:
        with pd.ExcelWriter(f"catastro_{municipio}.xlsx") as xl:
            urbano.to_excel(xl, sheet_name="URBANO", index=False)
            rural.to_excel(xl, sheet_name="RURAL", index=False)
        print(f"Guardado: catastro_{municipio}.xlsx")
