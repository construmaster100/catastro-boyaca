# Base catastral de Colombia (IGAC) por departamento y municipio

Descarga los predios **urbanos** y **rurales** que publica el IGAC (los mismos del visor
[Colombia en Mapas](https://www.colombiaenmapas.gov.co/)), con su **número catastral**,
**geometría (polígonos)**, **coordenadas** y **área en m²**, y los organiza en una carpeta
por departamento y municipio, en formatos que abren QGIS, ArcGIS, AutoCAD, Excel y Python.

- **Creado:** 28 de septiembre de 2026 · **Última actualización:** 29 de septiembre de 2026
- **Equipos:** original `C:\Users\CMconstrumaster\Desktop\Database`; actual `C:\Users\USUARIO\Desktop\Database`
- **Estado actual (29/09/2026):**
  - Descarga nacional: **urbano COMPLETO** (3.616.348 predios); **rural 63 %** (1.990.000 de 3.146.345).
    Se reanuda con `1_INICIAR_DESCARGA.bat`.
  - **Visor web "Catastro Boyacá"** funcionando en local (`4_ABRIR_VISOR.bat`) con los 123 municipios de
    Boyacá (756.197 predios). **No publicado**: se publica solo cuando se apruebe la versión final ([§ 15](#15-visor-web-buscador-de-predios)).
  - Todo el proyecto está versionado con Git en esta carpeta ([§ 16](#16-control-de-versiones)).

---

## Contenido

1. [Retomar en otro equipo (guía rápida)](#1-retomar-en-otro-equipo-guia-rapida)
2. [Qué hay en esta carpeta](#2-que-hay-en-esta-carpeta)
3. [Fuente de los datos](#3-fuente-de-los-datos)
4. [Instalar Python en un equipo nuevo](#4-instalar-python-en-un-equipo-nuevo)
5. [Descarga nacional: cómo funciona y cómo ejecutarla](#5-descarga-nacional-como-funciona-y-como-ejecutarla)
6. [Resultado: estructura de carpetas y formatos](#6-resultado-estructura-de-carpetas-y-formatos)
7. [Usar los datos en otros programas](#7-usar-los-datos-en-otros-programas)
8. [Script de un solo municipio (sin polígonos)](#8-script-de-un-solo-municipio-sin-poligonos)
9. [Hallazgos técnicos sobre el servidor del IGAC](#9-hallazgos-tecnicos-sobre-el-servidor-del-igac)
10. [Limitaciones](#10-limitaciones)
11. [Solución de problemas](#11-solucion-de-problemas)
12. [Bitácora](#12-bitacora)
13. [Pendientes](#13-pendientes)
14. [Referencias](#14-referencias)
15. [Visor web (buscador de predios)](#15-visor-web-buscador-de-predios)
16. [Control de versiones](#16-control-de-versiones)
17. [Fuente económica externa: Boyacá en Cifras (CCT)](#17-fuente-economica-externa-boyaca-en-cifras-cct)

---

## 1. Retomar en otro equipo (guía rápida)

> La descarga completa puede tardar **entre 1 y 24 horas** (depende de lo rápido que responda
> el servidor del IGAC). Se puede pausar y reanudar cuantas veces se quiera.

**En el equipo actual**
1. Copiar **toda la carpeta `Database`** (USB, Google Drive, OneDrive…). Incluir la subcarpeta
   `crudo/`: tiene lo que ya se descargó y así no se repite.

**En el equipo nuevo**
1. Pegar la carpeta en cualquier ubicación (por ejemplo, el Escritorio).
2. Instalar Python → [§ 4](#4-instalar-python-en-un-equipo-nuevo).
3. Configurar el equipo para que **no se suspenda** → [§ 5.4](#54-recomendaciones-para-dejarlo-corriendo).
4. Doble clic en **`1_INICIAR_DESCARGA.bat`**.
5. Dejarlo corriendo. Para ver el avance en cualquier momento: doble clic en **`2_VER_ESTADO.bat`**.
6. Al terminar aparece la carpeta **`catastro/`** con todos los departamentos y municipios
   y el archivo `catastro/indice_municipios.csv`.

**Si se interrumpe** (se apagó el equipo, se cortó internet, se cerró la ventana):
volver a abrir `1_INICIAR_DESCARGA.bat`. Continúa donde iba.

**Si al final dice que hubo bloques con error:** volver a abrir `1_INICIAR_DESCARGA.bat`;
solo descarga los que faltan.

---

## 2. Qué hay en esta carpeta

| Archivo / carpeta | Para qué sirve |
|---|---|
| `1_INICIAR_DESCARGA.bat` | **Doble clic para descargar todo el país** y organizarlo. Reanudable. |
| `2_VER_ESTADO.bat` | Muestra cuánto se ha descargado. No descarga nada. |
| `3_ORGANIZAR.bat` | Vuelve a generar `catastro/` a partir de lo descargado (sin volver a descargar). |
| `catastro_colombia.py` | Programa principal (descarga nacional + organización por carpetas). |
| `importar_catastro.py` | Programa pequeño: un municipio a pandas/Excel, sin polígonos ([§ 8](#8-script-de-un-solo-municipio-sin-poligonos)). |
| `requirements.txt` | Librerías de Python necesarias. |
| `crudo/` | Datos descargados en bruto (bloques comprimidos `.json.gz`). **No borrar** mientras no termine. |
| `catastro/` | **Resultado final** (se crea al terminar). |
| `catastro_08421.csv` / `.xlsx` | Prueba inicial: Luruaco (Atlántico), solo atributos. |
| `4_ABRIR_VISOR.bat` | **Doble clic para abrir el buscador de predios** en el navegador ([§ 15](#15-visor-web-buscador-de-predios)). |
| `preparar_visor.py` | Organiza en `catastro/` solo algunos departamentos, sin esperar la descarga completa. |
| `exportar_web.py` | Genera los datos livianos del visor en `visor/datos/`. |
| `servidor_visor.py` | Servidor local del visor (con compresión). |
| `estadisticas_urbanas.py` | Zonas urbanas, áreas por municipio y jerarquía urbana (`visor/datos/estadisticas.json`). |
| `georreferenciar_mapa.py` | Alinea la imagen ilustrada del departamento con el límite oficial. |
| `.gitignore` | Lo que **no** se versiona: `crudo/`, `catastro/` (datos pesados que se regeneran), registros y temporales. |
| `visor/` | Buscador de predios (HTML). Carpeta autocontenida: se puede subir a internet. |
| `README.md` | Este documento. |

---

## 3. Fuente de los datos

Colombia en Mapas no tiene un botón de descarga masiva; su información catastral viene de
este servicio público del IGAC (ArcGIS Server):

```
https://mapas.igac.gov.co/server/rest/services/Dato_Fundamental_Catastro/MapServer
```

| Capa | ID | Contenido | Se usa |
|---|---|---|---|
| R_CONSTRUCCION | 0 | Construcciones rurales | No |
| **R_TERRENO** | **1** | **Terrenos de predios rurales** (3.146.345 registros) | **Sí** |
| U_CONSTRUCCION | 2 | Construcciones urbanas | No |
| U_MANZANA | 3 | Manzanas urbanas | No |
| **U_TERRENO** | **4** | **Terrenos de predios urbanos** | **Sí** |

- **Sistema de coordenadas:** MAGNA-SIRGAS geográfico, **EPSG:4686** (longitud/latitud en grados).
- **Máximo por consulta:** 2.000 registros.

### Campos originales del servicio

| Campo | Descripción |
|---|---|
| `FID` | Identificador interno del registro |
| `CODIGO` | **Número predial nacional** (30 dígitos) |
| `CODIGO_ANT` | Número predial anterior (20 dígitos) |
| `MANZANA_CO` | Código de manzana (solo urbano) |
| `VEREDA_COD` | Código de vereda (solo rural) |
| `NUMERO_SUB` | Número de subdivisión |
| `SHAPE_Area` | Área en **grados cuadrados** (no sirve como m²) |
| `SHAPE_Leng` | Perímetro en grados |

### Estructura del número predial nacional (30 dígitos)

Ejemplo: `08 421 01 00 00 00 0001 0001 0 00 00 0000`

| Posición | Dígitos | Significado |
|---|---|---|
| 1–2 | 2 | Departamento (DANE) |
| 3–5 | 3 | Municipio (DANE) |
| 6–7 | 2 | Zona: `00` rural, `01` urbano, `02`–`99` corregimientos |
| 8–9 | 2 | Sector |
| 10–11 | 2 | Comuna |
| 12–13 | 2 | Barrio |
| 14–17 | 4 | Manzana (urbano) o vereda (rural) |
| 18–21 | 4 | Terreno |
| 22 | 1 | Condición de propiedad |
| 23–24 | 2 | Edificio o torre |
| 25–26 | 2 | Piso |
| 27–30 | 4 | Unidad predial |

Los primeros 5 dígitos son el **código DANE del municipio**; así se reparte cada predio en su carpeta.

---

## 4. Instalar Python en un equipo nuevo

1. Ir a [python.org/downloads](https://www.python.org/downloads/) y descargar el instalador
   (botón amarillo **Download Python**).
2. Ejecutarlo. Según la versión, aparece uno de estos dos instaladores:

   **a) Instalador clásico (ventana con botones)**
   - Marcar **☑ Add python.exe to PATH** (abajo, en la primera pantalla). **Es obligatorio.**
   - Clic en **Install Now** y esperar a "Setup was successful".

   **b) Python install manager (ventana negra con preguntas)** — el que se usó en el equipo original:

   | Pregunta | Respuesta |
   |---|---|
   | *Windows is not configured to allow paths longer than 260 characters… Update setting now?* | `y` (si sale un aviso amarillo de que no se pudo, no importa) |
   | *Add commands directory to your PATH now?* | **`y`** (obligatorio) |
   | *Install CPython now?* | **`y`** |
   | *View online help?* | `N` |

3. **Cerrar todas las ventanas de terminal / VS Code y abrirlas de nuevo.**
4. Comprobar: abrir una terminal (tecla Windows → escribir `cmd` → Enter) y escribir:
   ```
   python --version
   ```
   Debe responder algo como `Python 3.14.7`.
5. Las librerías (`requests`, `pyshp`, `pandas`, `openpyxl`) las instala solo
   `1_INICIAR_DESCARGA.bat`. A mano sería:
   ```
   python -m pip install -r requirements.txt
   ```

> En el equipo original quedó instalado Python 3.14.7 en
> `C:\Users\CMconstrumaster\AppData\Local\Python\`.

---

## 5. Descarga nacional: cómo funciona y cómo ejecutarla

### 5.1 Las dos fases

```
Servidor IGAC ──(1. descargar)──► crudo/urbano/*.json.gz ──(2. organizar)──► catastro/DEPTO/MUNICIPIO/...
                                   crudo/rural/*.json.gz
```

**Fase 1 — `descargar`** (lenta, usa internet)
- Recorre cada capa completa en bloques de 2.000 predios según su `FID`
  (`FID 1–2000`, `2001–4000`, …) y guarda cada bloque como
  `crudo/<zona>/<inicio>_<cantidad>.json.gz`.
- Hace 3 consultas simultáneas y reintenta hasta 5 veces cada bloque que falle.
- Si un bloque ya existe, lo salta, **por eso se puede reanudar**.
- Cuando encuentra 25 bloques vacíos seguidos, da la capa por terminada y crea el archivo
  `crudo/<zona>/_COMPLETO`.
- Si algún bloque falló después de 5 intentos, **no** marca la capa como completa y avisa:
  basta con volver a ejecutar.

**Fase 2 — `organizar`** (rápida, local)
- Solo se ejecuta si las dos capas tienen `_COMPLETO` (o con `--forzar`).
- Descarga la lista oficial de los 1.122 municipios del DANE (DIVIPOLA) para los nombres.
- Reparte los predios por municipio, convierte la geometría, calcula área y centroide y
  escribe GeoJSON, shapefile, CSV y metadata de cada municipio.
- Borra y vuelve a crear `catastro/` completo cada vez; se puede repetir sin riesgo.

### 5.2 Comandos

Con doble clic (recomendado) o desde una terminal abierta en la carpeta:

| Acción | Doble clic | Comando |
|---|---|---|
| Descargar + organizar | `1_INICIAR_DESCARGA.bat` | `python catastro_colombia.py` |
| Solo descargar | — | `python catastro_colombia.py descargar` |
| Ver avance | `2_VER_ESTADO.bat` | `python catastro_colombia.py estado` |
| Solo organizar | `3_ORGANIZAR.bat` | `python catastro_colombia.py organizar` |
| Organizar lo que haya (prueba) | — | `python catastro_colombia.py organizar --forzar` |

**Pausar:** `Ctrl + C` en la ventana, o cerrarla. **Reanudar:** ejecutar de nuevo.

Ejemplo de lo que muestra `estado`:
```
urbano: en progreso | 2 bloques | 4,000 predios | hasta FID 4,000 | 0 MB
rural: en progreso | 2 bloques | 4,000 predios | hasta FID 4,000 | 1 MB
Referencia: la capa rural tiene 3.146.345 predios en total.
```

### 5.3 Tiempo y espacio estimados

| Concepto | Estimado |
|---|---|
| Predios en total | ~6 millones (rural 3.146.345 confirmado; urbano ~3 millones estimado) |
| Consultas necesarias | ~3.100 bloques de 2.000 |
| Tiempo si el servidor está rápido (1–2 s por bloque) | **~1 hora** |
| Tiempo si el servidor está lento (se midieron hasta 180 s por consulta) | **12–24 horas** |
| Espacio de `crudo/` | ~1–3 GB |
| Espacio de `catastro/` (resultado) | ~8–15 GB |
| Espacio total recomendado libre | **20 GB** |

El servidor del IGAC es muy irregular: la misma consulta tardó entre 1 y 180 segundos en
distintos momentos del día. De noche suele estar menos cargado.

### 5.4 Recomendaciones para dejarlo corriendo

- **Evitar que el equipo se suspenda:** Configuración → Sistema → Energía →
  "Suspender cuando esté enchufado" → **Nunca**. (O en una terminal:
  `powercfg /change standby-timeout-ac 0`.) Volver a dejarlo como estaba al terminar.
- Mantener el equipo **enchufado** y con **internet estable** (mejor por cable).
- No es necesario tener VS Code abierto; basta la ventana negra del `.bat`.
- No mover ni renombrar la carpeta mientras está descargando.

---

## 6. Resultado: estructura de carpetas y formatos

```
catastro/
├── indice_municipios.csv                 ← los 1.122 municipios, con estado y conteos
├── 05_ANTIOQUIA/
│   ├── 05002_ABEJORRAL/
│   └── ...
├── 08_ATLANTICO/
│   ├── 08421_LURUACO/
│   │   ├── urbano.geojson                ← polígonos urbanos (GeoJSON)
│   │   ├── urbano.shp .shx .dbf .prj .cpg ← polígonos urbanos (Shapefile)
│   │   ├── rural.geojson
│   │   ├── rural.shp .shx .dbf .prj .cpg
│   │   ├── predios.csv                   ← todos los predios, sin polígono (para Excel)
│   │   └── metadata.json                 ← información del municipio
│   └── ...
└── ...
```

- Nombres de carpeta: `CODIGO_NOMBRE`, en mayúsculas, sin tildes ni espacios
  (compatibles con cualquier programa).
- Se crea carpeta para **todos** los municipios del DANE. Los que no tienen datos en el IGAC
  quedan solo con `metadata.json` y estado `sin_datos_igac` (lista para agregar datos de su
  gestor catastral más adelante).
- Un municipio puede tener solo urbano, solo rural o ambos.

### 6.1 Columnas (iguales en CSV, GeoJSON y shapefile)

| CSV / GeoJSON | Shapefile (máx. 10 letras) | Descripción |
|---|---|---|
| `ZONA` | `ZONA` | `URBANO` o `RURAL` |
| `NUMERO_CATASTRAL` | `NUM_CATAST` | Número predial nacional (30 dígitos) |
| `NUMERO_CATASTRAL_ANTERIOR` | `NUM_ANTER` | Número predial anterior (20 dígitos) |
| `MANZANA_VEREDA` | `MANZ_VERED` | Código de manzana (urbano) o vereda (rural) |
| `NUMERO_SUB` | `NUM_SUB` | Número de subdivisión |
| `AREA_M2` | `AREA_M2` | Área del terreno en m² (calculada de la geometría) |
| `LONGITUD` | `LONGITUD` | Longitud del centroide (grados, EPSG:4686) |
| `LATITUD` | `LATITUD` | Latitud del centroide (grados, EPSG:4686) |

> **Importante:** el número catastral debe tratarse como **texto**, no como número; si Excel lo
> convierte a número, pierde los ceros iniciales y los últimos dígitos (ver [§ 7.1](#71-excel)).

**Sobre el área:** se calcula con una aproximación elipsoidal local (GRS80), con error muy
pequeño para predios. En la prueba de Luruaco, el lote urbano mediano dio **299 m²**
(mínimo 43 m², máximo 38.944 m²), valores coherentes.

**Sobre el centroide:** es el centro geométrico del polígono más grande del predio; puede
quedar fuera del predio si este tiene forma de "L" o "U".

### 6.2 `metadata.json` (ejemplo)

```json
{
  "codigo_departamento": "08",
  "departamento": "ATLÁNTICO",
  "codigo_municipio": "08421",
  "municipio": "LURUACO",
  "estado": "con_datos",
  "predios_urbanos": 4126,
  "predios_rurales": 778,
  "archivos": ["urbano.geojson", "urbano.shp", "rural.geojson", "rural.shp", "predios.csv"],
  "sistema_coordenadas": "EPSG:4686 (MAGNA-SIRGAS, grados)",
  "fuente": "https://mapas.igac.gov.co/server/rest/services/Dato_Fundamental_Catastro/MapServer",
  "capas": {"urbano": "U_TERRENO (4)", "rural": "R_TERRENO (1)"},
  "fecha_organizacion": "2026-09-28",
  "nota_area": "AREA_M2 calculada a partir de la geometria (aproximacion elipsoidal local)."
}
```

### 6.3 `indice_municipios.csv`

| Columna | Descripción |
|---|---|
| `CODIGO_DEPARTAMENTO`, `DEPARTAMENTO` | Departamento |
| `CODIGO_MUNICIPIO`, `MUNICIPIO` | Municipio (DIVIPOLA) |
| `ESTADO` | `con_datos` o `sin_datos_igac` |
| `PREDIOS_URBANOS`, `PREDIOS_RURALES` | Cantidad de predios |
| `CARPETA` | Ruta relativa, p. ej. `08_ATLANTICO/08421_LURUACO` |

Sirve para que otro programa encuentre la carpeta de cualquier municipio sin recorrerlas todas.

---

## 7. Usar los datos en otros programas

| Programa | Archivo recomendado |
|---|---|
| QGIS / ArcGIS Pro / ArcMap | `.shp` o `.geojson` |
| AutoCAD Map 3D / Civil 3D | `.shp` |
| Excel | `predios.csv` |
| Python | `.geojson` o `predios.csv` |
| Google Earth | convertir a KML con QGIS |
| Páginas web (Leaflet, Mapbox, OpenLayers) | `.geojson` |
| Bases de datos (PostGIS, SQL Server) | `.shp` o `.geojson` con `ogr2ogr` |

### 7.1 Excel
Para no dañar el número catastral: **Datos → Desde texto/CSV** → elegir `predios.csv` →
**Transformar datos** → seleccionar las columnas `NUMERO_CATASTRAL`,
`NUMERO_CATASTRAL_ANTERIOR` y `MANZANA_VEREDA` → tipo **Texto** → Cerrar y cargar.
(Abrir el CSV con doble clic hace que Excel los convierta a número.)

### 7.2 QGIS
Arrastrar `urbano.shp` / `rural.shp` (o los `.geojson`) al mapa. El sistema de coordenadas
(EPSG:4686) se reconoce solo. Para medir en metros, reproyectar a **EPSG:9377
(MAGNA-SIRGAS / Origen-Nacional)**: clic derecho → Exportar → Guardar objetos como → SRC 9377.

Para cargar muchos municipios juntos: Vectorial → Herramientas de gestión de datos →
**Unir capas vectoriales**.

### 7.3 ArcGIS Pro
Mapa → **Agregar datos** → elegir el `.shp`. Para GeoJSON: herramienta
**JSON To Features**.

### 7.4 AutoCAD Map 3D / Civil 3D
Comando **`MAPIMPORT`** → tipo *ESRI Shapefile* → elegir el `.shp`. En "Data", marcar
"Create Object Data" para conservar el número catastral. Asignar el sistema de coordenadas
del dibujo (p. ej. MAGNA-SIRGAS Origen Nacional) para que se transforme a metros.

### 7.5 Google Earth
En QGIS: clic derecho en la capa → Exportar → Guardar objetos como → formato **KML**.

### 7.6 Python
```python
import json
import pandas as pd

# Atributos (sin geometria)
df = pd.read_csv("catastro/08_ATLANTICO/08421_LURUACO/predios.csv",
                 dtype={"NUMERO_CATASTRAL": str, "NUMERO_CATASTRAL_ANTERIOR": str,
                        "MANZANA_VEREDA": str})

# Buscar la carpeta de un municipio con el indice
indice = pd.read_csv("catastro/indice_municipios.csv", dtype=str)
carpeta = indice.loc[indice.CODIGO_MUNICIPIO == "08421", "CARPETA"].item()

# Todos los predios del pais en un solo DataFrame (sin geometria)
from pathlib import Path
todo = pd.concat((pd.read_csv(p, dtype=str) for p in Path("catastro").glob("*/*/predios.csv")),
                 ignore_index=True)
```

Con geometría (requiere `pip install geopandas`):
```python
import geopandas as gpd
gdf = gpd.read_file("catastro/08_ATLANTICO/08421_LURUACO/urbano.geojson")
gdf_m = gdf.to_crs(9377)          # a metros (MAGNA-SIRGAS Origen Nacional)
```

### 7.7 PostGIS / otras bases de datos (GDAL)
```
ogr2ogr -f PostgreSQL PG:"dbname=catastro" catastro/08_ATLANTICO/08421_LURUACO/urbano.shp -nln predios_urbanos -append
```

---

## 8. Script de un solo municipio (sin polígonos)

`importar_catastro.py` fue la primera solución: trae **solo los atributos** de un municipio
a pandas y opcionalmente a Excel. No trae polígonos ni área en m².

```
python importar_catastro.py 08421            # genera catastro_08421.csv
python importar_catastro.py 08421 --excel    # además catastro_08421.xlsx (hojas URBANO y RURAL)
```
```python
from importar_catastro import importar
urbano, rural, todo = importar("08421")
```

- Usa la consulta por municipio, que en este servidor es **lenta** (recorre todo el país,
  15–120 s por consulta) y a veces falla por tiempo de espera. Para muchos municipios, usar
  `catastro_colombia.py`.
- La columna `AREA_GRADOS2` es el `SHAPE_Area` original, en grados cuadrados (**no** m²).

---

## 9. Hallazgos técnicos sobre el servidor del IGAC

Pruebas hechas el 28/09/2026. Explican por qué el programa está hecho así:

| Prueba | Resultado | Decisión |
|---|---|---|
| Filtro `CODIGO LIKE '08421%'` | Devuelve 0 aunque haya datos | Filtrar por rango de texto: `CODIGO >= '08421' AND CODIGO < '08422'` |
| Paginación `resultOffset` | "Pagination is not supported" | No usar paginación |
| Filtro por rango de `CODIGO` | Recorre toda la tabla del país (sin índice): 15–120 s | Evitar filtrar por municipio para la descarga masiva |
| Filtro por rango de `FID` | 1–2 s por 2.000 predios (con el servidor tranquilo) | **Método elegido** |
| `f=geojson` | 170 s para 50 predios | Pedir `f=json` (Esri) y convertir a GeoJSON localmente |
| Parámetro `outSR=4686` | 60 s vs 1,8 s sin él (aunque ya está en 4686) | No enviar `outSR` |
| Consulta por lista de IDs (`objectIds`) | Lenta y con errores 503 | No usar |
| `outStatistics` (máximo FID) | "Unable to complete operation" | Detectar el final con 25 bloques vacíos seguidos |
| `SHAPE_Area` | Viene en grados² | Calcular el área en m² a partir de la geometría |
| Conteo total de la capa rural | 3.146.345 | Referencia de avance |
| Conteo total de la capa urbana | Error 504 (tiempo agotado) | Desconocido; estimado ~3 millones |
| Tiempos en general | Muy variables: 1 a 180 s la misma consulta | Reintentos automáticos y descarga reanudable |

**Conversión de geometría:** en formato Esri los anillos exteriores van en sentido horario y
los huecos en antihorario; en GeoJSON es al revés. El programa invierte el orden y agrupa cada
hueco con su anillo exterior (Polygon o MultiPolygon).

---

## 10. Limitaciones

- **Cobertura:** solo municipios donde el IGAC es el **gestor catastral**. Las ciudades con
  catastro propio (Bogotá, Medellín, Cali, Barranquilla y otras) no aparecen o aparecen
  incompletas; hay que pedir sus datos a su gestor.
- **Actualidad:** los datos son los que el IGAC tenga publicados al momento de la descarga.
  La fecha queda en `metadata.json` y en `crudo/<zona>/_COMPLETO`.
- **Solo terrenos:** no se descargan construcciones (capas 0 y 2) ni manzanas (capa 3).
  Se podrían agregar en `CAPAS` dentro de `catastro_colombia.py`.
- **Sin propietarios ni avalúos:** el servicio público no los publica (datos protegidos).
- **Área:** aproximación con error muy pequeño; para trabajos legales usar la cifra oficial
  del certificado catastral.
- Si el IGAC cambia la dirección del servicio o sus capas, habrá que ajustar `SERVICIO` y
  `CAPAS` al inicio de `catastro_colombia.py`.

---

## 11. Solución de problemas

| Síntoma | Causa / solución |
|---|---|
| `Python was not found…` o "Python no está instalado" | Python no está instalado o falta en el PATH. Repetir [§ 4](#4-instalar-python-en-un-equipo-nuevo) y **cerrar y abrir** la terminal. |
| `No module named 'shapefile'` / `'requests'` | `python -m pip install -r requirements.txt` |
| Muchos `ERROR bloque … (se reintentara…)` | El servidor está saturado o caído. Cerrar, esperar un rato (o probar de noche) y volver a ejecutar. |
| Se queda mucho tiempo sin avanzar | Normal cuando el servidor está lento (hasta 3 min por consulta). Si pasa de 30 min, cerrar y volver a ejecutar. |
| "La descarga no está completa" al organizar | Falta terminar la fase 1: ejecutar `1_INICIAR_DESCARGA.bat`. |
| Aparecen archivos `.tmp` en `crudo/` | Bloques interrumpidos a mitad; se pueden borrar. Se vuelven a descargar solos. |
| Un municipio sale `sin_datos_igac` | Su gestor catastral no es el IGAC ([§ 10](#10-limitaciones)). |
| Excel muestra `8,4210E+28` en el número catastral | Importar el CSV como texto ([§ 7.1](#71-excel)). |
| Se quiere empezar desde cero | Borrar las carpetas `crudo/` y `catastro/` y ejecutar de nuevo. |
| El servidor cambió / da error 404 | Revisar la dirección en [§ 14](#14-referencias) y actualizar `SERVICIO` en el programa. |

**Ajustes en `catastro_colombia.py`** (al inicio del archivo):

| Variable | Valor | Para qué |
|---|---|---|
| `HILOS` | 3 | Consultas simultáneas. Subirlo acelera, pero puede saturar el servidor y generar más errores. |
| `TAM_BLOQUE` | 2000 | Predios por consulta (máximo que permite el servidor). |
| `VACIOS_FIN` | 25 | Bloques vacíos seguidos para dar por terminada una capa. |
| `CAPAS` | urbano 4, rural 1 | Capas a descargar. |

---

## 12. Bitácora

**28/09/2026**
- Solicitud inicial: importar a pandas los predios urbanos y rurales con número catastral de
  Colombia en Mapas.
- Se identificó el servicio `Dato_Fundamental_Catastro` del IGAC y se creó
  `importar_catastro.py` (un municipio, atributos). Probado con Luruaco (08421):
  4.126 urbanos + 778 rurales.
- Se instaló Python 3.14.7 (Python install manager) y pandas 3.0.6.
- Se detectó que `SHAPE_Area` está en grados²: la columna se renombró a `AREA_GRADOS2`.
- Nueva solicitud: todos los departamentos y municipios, con estructura de carpetas,
  coordenadas y shape, para usar en otros programas.
- Se probaron varios métodos de descarga (ver [§ 9](#9-hallazgos-tecnicos-sobre-el-servidor-del-igac));
  se eligió la descarga por bloques de FID + organización local.
- Prueba del sistema completo con 2 bloques por capa: 7 municipios de Atlántico organizados
  correctamente (GeoJSON, shapefile, CSV y metadata validados; áreas coherentes).
  Esa salida de prueba se borró; los 4 bloques descargados quedaron en `crudo/` y se
  aprovechan al reanudar.
- La descarga completa **queda pendiente** para ejecutarse en otro equipo
  (no se disponía de las horas necesarias).

**29/09/2026** (equipo `USUARIO`)
- Descarga reanudada: urbano completo; rural al 63 % (se detuvo al cerrarse la ventana; se reanuda con el `.bat`).
- Prioridad Boyacá: `preparar_visor.py` organiza departamentos sueltos sin esperar la descarga nacional.
  Boyacá quedó completo (123/123 municipios, 209.059 urbanos + 547.138 rurales).
- Visor web construido y ajustado con el usuario (ver [§ 15](#15-visor-web-buscador-de-predios)): buscador por número
  predial con jerarquía del código, navegación por niveles de zoom (municipio → sector → manzana/vereda → predio),
  área y cotas del lote, ficha imprimible con plano y linderos, grilla MAGNA-SIRGAS Origen Nacional, logos,
  banner, mapa departamental ilustrado georreferenciado (coincidencia 88 %), zonas urbanas, áreas por municipio,
  jerarquía urbana y gráfico circular del área de los 123 municipios.
- Se publicó por error en GitHub Pages y se retiró el mismo día (repositorio privado, Pages desactivado).
  Regla: **no publicar hasta aprobar la versión final**.
- Todo el proyecto quedó versionado con Git en la carpeta `Database` ([§ 16](#16-control-de-versiones)).

---

## 13. Pendientes

- [x] Identificar la fuente de datos (IGAC).
- [x] Script de un municipio (`importar_catastro.py`).
- [x] Instalar Python y librerías en el equipo original.
- [x] Sistema nacional por carpetas con GeoJSON, shapefile, CSV y metadata (`catastro_colombia.py`).
- [x] Prueba corta del sistema completo.
- [ ] **Terminar la descarga rural** (`1_INICIAR_DESCARGA.bat`) — falta ~37 %, unas 3–4 horas.
- [x] Visor web de Boyacá (local).
- [ ] Aprobar la versión final del visor y **publicarlo** (GitHub Pages, ver § 15 y § 16).
- [ ] Agregar Cundinamarca y Casanare al visor (hoy "proyectados"): `python preparar_visor.py 25 85` y
      `python exportar_web.py 15 25 85`, luego `python estadisticas_urbanas.py`.
- [ ] Validar con el usuario los cortes de la jerarquía urbana (1.000 / 300 / 100 / 30 ha).
- [ ] Revisar `catastro/indice_municipios.csv` al terminar (cuántos municipios con datos).
- [ ] (Opcional) Agregar construcciones y manzanas (capas 0, 2 y 3).
- [ ] (Opcional) Conseguir datos de los municipios con gestor catastral propio.
- [ ] (Opcional) Versionar cada carpeta de departamento en Git si se necesita historial de cambios.

---

## 14. Referencias

- Servicio del IGAC: <https://mapas.igac.gov.co/server/rest/services/Dato_Fundamental_Catastro/MapServer>
- Visor Colombia en Mapas: <https://www.colombiaenmapas.gov.co/>
- Guía de consulta catastral de Colombia en Mapas:
  <https://colombia-en-mapas.gitbook.io/colombia-en-mapas/funcionalidades/consultas-avanzadas/como-hacer-una-consulta-catastral>
- Lista de municipios DIVIPOLA (DANE), usada para los nombres:
  <https://www.datos.gov.co/resource/gdxc-w37w.json>
- Datos abiertos ICDE — Terreno de predio rural:
  <https://datos.icde.gov.co/datasets/1ab5d2d687534c8d85d7586985cac2cd>
- Sistema de coordenadas EPSG:4686: <https://epsg.io/4686> · EPSG:9377: <https://epsg.io/9377>
- Límites municipales (IGAC): <https://mapas.igac.gov.co/server/rest/services/ordenamientoterritorial/pendientepromediomunicipio/MapServer/0>

---

## 15. Visor web (buscador de predios)

Página que identifica un predio a partir de su número predial y marca la jerarquía
**País → Departamento → Municipio → Zona → Sector → Comuna → Barrio → Manzana/Vereda → Terreno → Predio**.

**Abrir:** doble clic en `4_ABRIR_VISOR.bat` (abre `http://localhost:8765/`). Dejar la ventana
negra abierta mientras se usa. Abrir el `index.html` con doble clic **no** funciona: el navegador
bloquea la lectura de los datos sin un servidor.

**Flujo de datos:**
```
crudo/ ──preparar_visor.py──► catastro/ ──exportar_web.py──► visor/datos/ ──servidor_visor.py──► navegador
```
- `python preparar_visor.py 15 25` organiza esos departamentos desde lo ya descargado.
- `python exportar_web.py 15 25` genera `visor/datos/` (un `.json` por municipio, coordenadas
  a 6 decimales, `indice.json` y `limites.json` con los límites municipales oficiales).
- Prueba inicial: solo Boyacá (15), 123 municipios.
- `python estadisticas_urbanas.py` calcula las zonas urbanas (unión de predios urbanos, cerrando
  calles con ±12 m; cabecera = zona 01, centros poblados = zonas 02–99), el área de cada municipio
  (límite oficial), % urbano, % rural, % del área del departamento y la jerarquía urbana
  (≥1.000 ha ciudad principal, ≥300 intermedia, ≥100 centro menor, ≥30 centro local, resto núcleo básico).
  Salidas: `visor/datos/zonas_urbanas.json` y `visor/datos/estadisticas.json`.
- `python georreferenciar_mapa.py` alinea la imagen ilustrada del departamento con el límite oficial.

**Uso:** escribir el número predial por partes (2 dígitos = departamento, 5 = municipio,
7 = zona, 17 = manzana/vereda, 30 = predio) o el número anterior (20 dígitos); o elegir
departamento/municipio en el recuadro superior derecho; o hacer clic en un predio. Al acercarse
(zoom 13+) se cargan solos los predios de los municipios visibles.

**Publicar en internet:** `visor/` es un sitio estático (HTML + JSON), no necesita base de datos
ni Python en el servidor. Subir la carpeta `visor/` completa a:
- **Cloudflare Pages** o **Netlify** (gratis; arrastrar la carpeta). Límite de 25 MB por archivo
  en Cloudflare: revisar que ningún municipio lo supere.
- **GitHub Pages** (repositorio de máx. ~1 GB, archivos < 100 MB).
- Un servidor propio (nginx/Apache/IIS) con compresión gzip activada para `.json`.

Para mostrarlo en la red local sin publicarlo: `python servidor_visor.py 8765 --red` y abrir
`http://IP-del-equipo:8765/` desde otro equipo. Los datos son públicos del IGAC; citar la fuente.

### 15.1 Manual de uso (para usuarios sin conocimientos técnicos)

**Pantalla**
```
┌──────────┬──────────── banner ────────────┬──────────────┐
│  Logo    │ Catastro Boyacá                │ Logo perito  │
│ (inicio) ├────────────────────────────────┤              │
│          │ Ruta · Departamento · Municipio│              │
├──────────┼────────────────────────────────┼──────────────┤
│ Buscador │                                │ Buscador de  │
│ por      │            MAPA                │ municipios   │
│ número   │                                │ Áreas        │
│ predial  │                                │ Gráfico      │
│ Mapa de  │                                │ circular     │
│ ubicación│                                │              │
└──────────┴────────────────────────────────┴──────────────┘
```

| Quiero… | Cómo |
|---|---|
| Buscar un predio | Escribir el número predial (30 dígitos) en el panel izquierdo. También sirve el número anterior (20). |
| Ver una zona por su código | Escribir solo el inicio: 5 dígitos = municipio, 9 = sector, 17 = manzana/vereda. |
| Ir a un municipio | Buscador del panel derecho (escribir nombre o código, ↑ ↓ y Enter), selector de la barra o clic en el mapa. |
| Volver a todo Boyacá | Clic en el logo, en el mapa de ubicación, o botón ✕ del buscador de municipios, o tecla **Esc**. |
| Ver área y medidas de un lote | Clic en el predio: aparecen el área (m²) y 4 cotas de sus lados principales. |
| Imprimir o guardar la ficha del lote | Botón **🖨 Ficha / Imprimir** → Imprimir / Guardar PDF, o Descargar plano (imagen). |
| Quitar el predio seleccionado | Botón ✕ Quitar selección, tecla Esc o clic en un espacio vacío del mapa. |
| Ver coordenadas | Grilla MAGNA-SIRGAS Origen Nacional (10 / 100 / 1.000 m según el zoom); el recuadro muestra E/N del mouse. |
| Ver áreas urbana/rural del municipio | Tarjeta "Áreas" del panel derecho (área total, % urbano, % rural, % de Boyacá, jerarquía). |
| Ver la jerarquía urbana | Botón **📊 Jerarquía urbana y áreas** (tabla ordenable, clic en fila = ir, Descargar CSV). |
| Cambiar fondo o capas | Botón de capas (arriba a la derecha): Calles / Satélite, Mapa departamental (ilustrado), Zonas urbanas. |

**Qué se ve según el zoom**

| Nivel | Se muestra |
|---|---|
| Departamento | Contorno grueso de Boyacá, mapa ilustrado, límites y códigos de municipio, zonas urbanas |
| Municipio | Regiones por zona-sector con su cantidad de predios |
| Barrio | Números de manzana / vereda |
| Calle | Polígonos de los predios |
| Muy cerca | Número de terreno de cada predio |

**Enlaces directos:** `…/#<número predial>` abre ese predio; `…/?ficha#<número de 30 dígitos>` abre su ficha;
`…/?jerarquia` abre la tabla de jerarquía urbana.

### 15.2 Archivos del visor

| Archivo | Contenido |
|---|---|
| `visor/index.html` | Toda la aplicación (HTML + CSS + JavaScript; Leaflet y proj4 desde cdnjs) |
| `visor/datos/<código>.json` | Predios de cada municipio (urbano + rural) |
| `visor/datos/indice.json` | Departamentos y municipios con conteos y recuadros |
| `visor/datos/limites.json` / `departamentos.json` | Límites municipales oficiales (IGAC) y contorno de Boyacá |
| `visor/datos/zonas_urbanas.json` / `estadisticas.json` | Zonas urbanas, áreas y jerarquía |
| `visor/datos/mapa_departamental.json` | Georreferenciación de la imagen ilustrada |
| `visor/img/` | Originales del usuario (`logo.png`, `logoperito.png`, `banner.png`, `Mapa departamental..png`) y versiones web (`*_web.*`, `*_raster.png`, `*_mini.png`) |

---

## 16. Control de versiones

Toda la carpeta `Database` es un repositorio **Git** (rama `main`), con la historia del visor incluida
en `visor/`.

- **No se versionan** (ver `.gitignore`): `crudo/` y `catastro/` (varios GB; se regeneran con
  `1_INICIAR_DESCARGA.bat` / `3_ORGANIZAR.bat` / `preparar_visor.py`), `_organizar/`, registros `*.log`,
  `__pycache__/` y la configuración local `.claude/`.
- **Guardar cambios:** `git add -A` y `git commit -m "descripción"`.
- **Publicar el visor (solo cuando se apruebe):** el repositorio de GitHub
  `construmaster100/visor-catastro-boyaca` (hoy **privado**, Pages desactivado) está configurado como
  remoto `pages`. Se publica únicamente la carpeta `visor/`:
  ```
  git subtree push --prefix visor pages main
  ```
  y luego en GitHub: Settings → General → hacerlo público; Settings → Pages → Branch `main` / root.

---

## 17. Fuente económica externa: Boyacá en Cifras (CCT)

Página: <https://cctunja.org.co/estudios-economicos/boyaca-en-cifras/> (Cámara de Comercio de Tunja).

| Archivo | Para qué sirve |
|---|---|
| `fuentes/Boyaca-en-Cifras-2024_CCTunja.xlsx` | Copia de la herramienta Excel 2024 (hoja `BaseMun`: 123 municipios × 51 variables). |
| `importar_cct.py` | Genera `visor/datos/indicadores.json` (indicadores por municipio) y `visor/datos/provincias.json` (13 provincias, unión de límites oficiales). |
| `analisis_cct.py` | Recorre la página y genera `informes/analisis_boyaca_en_cifras.md` y `informes/coincidencias_municipios.csv`. |

**Resultados principales (29/09/2026)**
- La página publica 14 fuentes (11 PDF, 1 Excel, 2 Power BI). La **base más precisa y verificable es el Excel 2024**:
  única en formato de datos, la más reciente, 123/123 municipios, población y totales coinciden al 100 % con el departamento.
- Anomalías: en la fila «Departamento» los 6 grupos de edad tienen el mismo valor (164.450); el valor agregado
  municipal (39.049 miles de millones) es 55 % mayor que el PIB 2024 de la hoja departamental (25.177), probablemente
  precios corrientes frente a constantes; el ICM solo existe para 23 municipios (18,7 %) y viene como puesto.
- Coincidencia de municipios con el repositorio: **123/123 por código DANE**; 122 con nombre idéntico y 1 que solo
  difiere en la tilde (Zetaquirá; DIVIPOLA lo trae sin tilde).
- **Uso del suelo (criterio del usuario):** urbano = actividad económica; rural 10–300 m² = vivienda; rural > 300 m² =
  agropecuario. Resultado: 209.059 urbanos, 15.314 vivienda rural, 531.794 agropecuarios (2,26 millones de ha).
  El valor agregado y las empresas siguen a los predios urbanos (Pearson 0,91 y 0,97); la producción agrícola en
  toneladas **no** sigue al área agropecuaria (≈ 0), porque se concentra en cultivos intensivos de municipios pequeños.

---

## 18. Capas para Geo Data Viewer (VS Code)

La extensión **Geo Data Viewer** (`randomfractalsinc.geo-data-viewer`, basada en kepler.gl) está instalada y
recomendada en `.vscode/extensions.json`. `python exportar_geo.py` genera en `geo/`:

| Archivo | Contenido |
|---|---|
| `boyaca_municipios.geojson` | 123 municipios (límite oficial) con áreas, % urbano/rural, % de Boyacá, jerarquía urbana, indicadores CCT 2024 (población, densidad, valor agregado, empresas, ICFES, salud, IRCA…) y uso del suelo de sus predios |
| `boyaca_municipios_puntos.csv` | Lo mismo como puntos (centro de cada municipio), para mapas de calor o burbujas |
| `boyaca_provincias.geojson` | 13 provincias con totales (población, área, valor agregado, predios) |
| `boyaca_zonas_urbanas.geojson` | Cabeceras y centros poblados |
| `boyaca_contorno.geojson` | Contorno del departamento |

**Abrir:** en el explorador de VS Code, clic derecho sobre el archivo → **Geo: View Map** (o `Ctrl+Shift+P` →
"Geo: View Map"). En kepler.gl se puede colorear por cualquier columna (p. ej. `densidad_hab_km2`,
`valor_agregado`, `riesgo_agua`, `categoria_urbana`) y filtrar por provincia.

**Imagen ilustrada del departamento:** `georreferenciar_mapa.py` hace un ajuste afín completo (6 parámetros) que
maximiza la coincidencia pixel a pixel con el límite oficial (89,4 %; el resto son diferencias propias del dibujo),
remuestrea la imagen a la grilla del mapa y la recorta con el límite oficial para que su borde coincida exactamente.

---

## 19. Repositorio «Cámara de Comercio» (scraping de Boyacá en Cifras)

`python scraper_cct.py` descarga **todo** lo publicado en <https://cctunja.org.co/estudios-economicos/boyaca-en-cifras/>
a `visor/camara/` (solo lo que falta):

| Contenido | Detalle |
|---|---|
| `camara/archivos/` | 12 documentos (108 MB): ediciones 2015–2024 (PDF), infografía 2019-2020, informe de auditoría y la herramienta Excel 2024 |
| `camara/catalogo.json` | Título, año, tipo, páginas, tamaño e **índice de contenido** de cada PDF (cuando el PDF lo permite), tableros Power BI y textos de la página |
| `camara/basemun.json` | Base municipal 2024 (123 municipios × 51 variables) |
| `camara/baseboy.json` | Comparativo de los 33 departamentos y Colombia 2020–2024 (PIB, PIB per cápita, desempleo, pobreza monetaria y multidimensional, Gini, competitividad, población) |
| `camara/hojas/` | Las 9 hojas del Excel, fila por fila |
| `camara/analisis.html` | Informe de `analisis_cct.py` |

**Interfaz:** botón **🏛 Cámara de Comercio** en la barra del visor (antes de «Colombia») → `camara.html`, con el mismo
diseño: pestañas **Documentos** (visor de PDF con índice y salto a página), **Datos municipales** (tabla ordenable y
filtrable, CSV, enlace de cada municipio al visor catastral), **Comparativo departamental** (Boyacá resaltado frente a
los demás departamentos y evolución frente a Colombia) y **Análisis**. Panel derecho: cifras clave de Boyacá y enlaces a
los tableros Power BI. Botón **🗺 Catastro** para volver.

**Inconsistencias de la fuente detectadas:** la fila «Colombia» trae pobreza multidimensional ≈ 40 % (mayor que Chocó,
33,9 %; mediana departamental 13,4 %) y un «puesto» de competitividad 57; en esos dos indicadores la interfaz no muestra
la referencia nacional y lo explica.
