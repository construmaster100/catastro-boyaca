# PROCESO — Catastro Boyacá

Arquitectura, automatización y protocolo de publicación del proyecto. La documentación técnica
completa (descarga del IGAC, visor, fuentes) está en `README.md`.

## 1. Tres versiones en este computador

| Versión | Carpeta | Para qué | Cómo se actualiza |
|---|---|---|---|
| **Trabajo** | `Escritorio\Database` | Donde se edita y se corren los scripts | `python actualizar_todo.py` |
| **Online** | `Escritorio\Catastro_Boyaca_ONLINE` | Clon del repositorio `github.com/construmaster100/catastro-boyaca` | `git push` desde Trabajo y `python construir_versiones.py --online` |
| **Offline** | `Escritorio\Catastro_Boyaca_OFFLINE` | **Autoportante**: visor + documentos + datos + servidor PowerShell. Sin internet ni Python | `python construir_versiones.py --offline` |

**Online (GitHub Pages):** se publica solo la carpeta `visor/` (el sitio), mediante el flujo
`.github/workflows/pages.yml` (manual: pestaña *Actions* → *Publicar visor* → *Run workflow*). Los documentos
de la Cámara se abren desde su página original y los Excel desde el repositorio (`visor/camara.html`
detecta si está en línea). Los mapas base (calles/satélite) requieren internet.

**Offline:** doble clic en `ABRIR_VISOR.html` (sin servidor: los datos van como `.json.js`, ver `visor/lib/datos_archivo.js`); alternativa `ABRIR_VISOR_OFFLINE.bat` → `http://localhost:8766/`. Las librerías del mapa
(Leaflet, proj4) están en `visor/lib/`, así que todo funciona sin conexión salvo el mapa base.

**Trabajo:** `4_ABRIR_VISOR.bat` (Python, `http://localhost:8765/`, sirve también `/docs/`).

## 2. Automatización

`python actualizar_todo.py` ejecuta en orden (registro en `informes/actualizacion.log`):

1. `scraper_cct.py` — descarga documentos nuevos de las 12 secciones de estudios económicos de la
   Cámara de Comercio de Tunja → `docs/camara_comercio/<sección>/` y `catalogo_camara_comercio.xlsx`.
2. `extraer_cct.py` — texto (página por página) y tablas de cada documento → `texto_<sección>.xlsx`,
   `tablas_<sección>.xlsx`.
3. `importar_cct.py` — indicadores municipales y provincias → `visor/datos/`.
4. `estadisticas_urbanas.py` — zonas urbanas, áreas y jerarquía (solo con `--completo`).
5. `analisis_cct.py` — calidad de datos, economía, uso del suelo, coincidencias → `informes/`.
6. `exportar_geo.py` — capas para Geo Data Viewer → `geo/`.
7. `exportar_excel.py` — datos del proyecto en Excel → `docs/datos/municipios_boyaca.xlsx`.
8. Informe web → `visor/camara/analisis.html`.
9. `construir_versiones.py --offline` — con `--offline`.

La descarga nacional del IGAC (predios) es aparte: `1_INICIAR_DESCARGA.bat` y luego
`preparar_visor.py` / `exportar_web.py` (ver README).

## 3. Datos en Excel (`docs/`)

| Archivo | Contenido |
|---|---|
| `docs/camara_comercio/catalogo_camara_comercio.xlsx` | Resumen por sección, documentos, índices de contenido, tableros |
| `docs/camara_comercio/<sección>/texto_<sección>.xlsx` | Texto de cada página de cada documento |
| `docs/camara_comercio/<sección>/tablas_<sección>.xlsx` | Tablas extraídas (una hoja por tabla + índice con vínculos) |
| `docs/camara_comercio/boyaca-en-cifras/Herramienta-...xlsx` | Base original de la Cámara (123 municipios × 51 variables) |
| `docs/datos/municipios_boyaca.xlsx` | Municipios, provincias, jerarquía urbana, coincidencias y fuentes |

## 4. Protocolo Git (mismo del proyecto «Investigación de mercado» / kraken)

- Configuración **local** del repositorio: `user.name=construmaster100`, `user.email=mesurare@gmail.com`,
  `core.autocrlf=false`, `core.quotepath=false`, `http.postbuffer=524288000`; rama `main`; remoto `origin`
  en `github.com/construmaster100/<repo>`.
- `.gitignore`: datos crudos regenerables, temporales de Office y del sistema, registros y `CLAUDE.md`
  (notas internas del asistente, no se publican).
- Commits por partes: primero código, datos livianos y páginas; luego cada carpeta pesada en su propio
  commit con conteo y tamaño, p. ej. `Documentos: docs/camara_comercio/tejido-empresarial (19 archivos, 139M)`.
  Así cada `push` es de tamaño manejable.
- **Publicar (hacer público el repositorio / activar Pages) solo cuando el usuario apruebe la versión final.**

## 5. Vista de administrador (estadísticas de uso)

- **Abrir:** `5_ABRIR_ADMINISTRADOR.bat` → `http://localhost:8765/admin/`. Carpeta independiente `admin/`
  (fuera de `visor/`, nunca se publica). Solo responde a este computador (127.0.0.1).
- **Barra lateral:** Resumen, Visitas a la página, Ingresos de personas (sesiones), Predios consultados,
  Quién consulta (IP, navegador, sistema, idioma, pantalla, primera/última actividad, predios vistos) y Registro
  de actividad (últimos 300 eventos). Exportar CSV. Se actualiza cada 30 s.
- **Cómo se registra:** `visor/lib/registro.js` envía cada visita, municipio, predio, ficha, descarga y documento
  a `servidor_visor.py` (`POST /api/evento`), que lo agrega a `registro/visitas.jsonl`.
- **Privacidad (Ley 1581 de 2012):** el visor muestra un aviso; `registro/` está en `.gitignore` y no va a la
  copia offline ni a la versión en línea. Solo se registra cuando el visor se usa a través de `servidor_visor.py`
  (no en la copia offline sin servidor ni en GitHub Pages, que no tienen servidor propio).
- **Términos y condiciones (bloqueante):** al entrar, `visor/lib/registro.js` muestra una ventana compacta con la casilla
  «Acepto los términos y condiciones» (el enlace abre la ventana con el texto completo: objeto, fuentes,
  uso permitido, tratamiento de datos — Ley 1581 de 2012 —, cookies y aceptación). El visor queda bloqueado hasta
  marcar la casilla; entonces aparece el botón verde «Ingresar». La aceptación se guarda un año (cookies
  `cb_terminos`, `cb_consent`, `cb_visitante`; en la copia offline, almacenamiento local) y se registra en el
  servidor (evento «aceptacion»). Para pedir de nuevo la aceptación a todos, cambiar `TERMINOS_VERSION`.
  Enlace «Términos y condiciones» en los créditos del mapa: muestra los términos y permite revocar la autorización.
  Quien abre la página y no acepta queda como visita anónima (sin IP ni navegador).
