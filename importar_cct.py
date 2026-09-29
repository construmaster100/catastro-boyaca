"""
Importa los indicadores municipales de "Boyaca en Cifras 2024" (Camara de Comercio de Tunja)
y genera los datos del visor:

    visor/datos/indicadores.json   indicadores por municipio (codigo DANE) + metadatos de la fuente
    visor/datos/provincias.json    limite de las 13 provincias (union de los limites municipales oficiales)

Fuente: https://cctunja.org.co/estudios-economicos/boyaca-en-cifras/
Archivo: fuentes/Boyaca-en-Cifras-2024_CCTunja.xlsx (hoja "BaseMun")
Unidades (segun el informe): valor agregado en miles de millones de pesos; captaciones, colocaciones,
FINAGRO y BANCOLDEX en millones de pesos; ICM 2023 = puesto en el Indice de Competitividad Municipal;
riesgo del agua = categoria IRCA.

Uso: python importar_cct.py
"""
import json
import warnings
from pathlib import Path

import openpyxl
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

CARPETA = Path(__file__).parent
ORIGEN = CARPETA / "fuentes" / "Boyaca-en-Cifras-2024_CCTunja.xlsx"
DATOS = CARPETA / "visor" / "datos"

# columna del Excel (fila 2) -> clave en el visor
CAMPOS = {
    "Provincia": "provincia",
    "VA_2024": "valor_agregado", "Mat_2024": "empresas_matriculadas", "Ren_2024": "empresas_renovadas",
    "Can_2024": "empresas_canceladas", "Comf_Empresas": "comfaboy_empresas", "Comf_Empleos": "comfaboy_empleos",
    "0-6años": "pob_0_6", "7-14años": "pob_7_14", "15-17años": "pob_15_17", "18-26años": "pob_18_26",
    "27-59años": "pob_27_59", "60 o masaños": "pob_60_mas",
    "N_Hombres": "hombres", "N_Mujeres": "mujeres", "N_Total": "poblacion",
    "Fin_Captaciones": "captaciones", "Fin_Colocaciones": "colocaciones", "Fin_FINAGRO": "finagro", "Fin_BANCOLDEX": "bancoldex",
    "ICM": "icm_puesto", "Prod(ton)_2023": "produccion_agricola_ton", "Bovino_2024": "bovinos",
    "ICFES_2024": "icfes", "Matrículas_2024": "matricula_escolar", "Establecimientos": "establecimientos_educativos",
    "IPS_2024": "ips", "Camas_2024": "camas", "Contributivo_2024": "regimen_contributivo",
    "Especial_2024": "regimen_especial", "Subisidiado_2024": "regimen_subsidiado",
    "Acueductos_2024": "acueductos", "Riesgo_2024": "riesgo_agua", "Eventos_2024": "eventos_riesgo",
}


def numero(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return round(v, 2) if isinstance(v, float) else v
    try:
        return round(float(str(v).replace(",", ".")), 2)
    except ValueError:
        return str(v).strip()


def main():
    warnings.filterwarnings("ignore")
    ws = openpyxl.load_workbook(ORIGEN, read_only=True, data_only=True)["BaseMun"]
    filas = list(ws.iter_rows(values_only=True))
    cabecera = [str(c).strip() if c else "" for c in filas[1]]
    # "Contributivo_202..." puede venir recortado: se busca por prefijo
    col = {}
    for nombre_excel, clave in CAMPOS.items():
        idx = next((i for i, c in enumerate(cabecera) if c == nombre_excel or c.startswith(nombre_excel[:12])), None)
        if idx is None:
            print(f"  aviso: no se encontro la columna {nombre_excel}")
        else:
            col[clave] = idx
    municipios = {}
    for f in filas[2:]:
        codigo = str(f[0] or "")[:5]
        if not (codigo.isdigit() and codigo.startswith("15")):
            continue
        municipios[codigo] = {clave: (str(f[i]).strip() if clave in ("provincia", "riesgo_agua") and f[i] else numero(f[i]))
                              for clave, i in col.items()}
    salida = {
        "fuente": "Cámara de Comercio de Tunja, Boyacá en Cifras 2024",
        "url": "https://cctunja.org.co/estudios-economicos/boyaca-en-cifras/",
        "unidades": {"valor_agregado": "miles de millones de pesos", "captaciones": "millones de pesos",
                     "colocaciones": "millones de pesos", "icm_puesto": "puesto en el ICM 2023",
                     "riesgo_agua": "IRCA 2024", "produccion_agricola_ton": "toneladas 2023"},
        "municipios": municipios,
    }
    (DATOS / "indicadores.json").write_text(json.dumps(salida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Indicadores: {len(municipios)} municipios -> visor/datos/indicadores.json")

    # Provincias: union de los limites municipales oficiales
    limites = json.loads((DATOS / "limites.json").read_text(encoding="utf-8"))["features"]
    grupos = {}
    for f in limites:
        cod = str(f["properties"]["CODIGO"]).zfill(5)
        prov = municipios.get(cod, {}).get("provincia")
        if prov:
            grupos.setdefault(prov, []).append(shape(f["geometry"]).buffer(0.0005))
    feats = []
    for prov, geoms in sorted(grupos.items()):
        union = unary_union(geoms).buffer(-0.0005).simplify(0.0003)
        punto = union.representative_point()
        feats.append({"type": "Feature", "properties": {"PROVINCIA": prov, "MUNICIPIOS": len(geoms),
                                                        "ETIQUETA": [round(punto.x, 5), round(punto.y, 5)]},
                      "geometry": mapping(union)})
    (DATOS / "provincias.json").write_text(json.dumps({"type": "FeatureCollection", "features": feats},
                                                      ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Provincias: {len(feats)} -> visor/datos/provincias.json")
    for ft in feats:
        print(f"  {ft['properties']['PROVINCIA']:<12} {ft['properties']['MUNICIPIOS']:>3} municipios")


if __name__ == "__main__":
    main()
