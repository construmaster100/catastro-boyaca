# Análisis de «Boyacá en Cifras» (Cámara de Comercio de Tunja)

Generado el 29/09/2026 con `analisis_cct.py`. Página: <https://cctunja.org.co/estudios-economicos/boyaca-en-cifras/>

## 1. Fuentes publicadas en la página

| Tipo | Año | Tamaño | Enlace |
|---|---|---|---|
| XLSX | 2024 | 0,7 MB | [Herramienta-tecnologica-XLS-Boyaca-en-Cifras-2024.xlsx](https://cctunja.org.co/wp-content/uploads/2025/09/Herramienta-tecnologica-XLS-Boyaca-en-Cifras-2024.xlsx) |
| PDF | 2024 | 17,8 MB | [Boyaca-en-Cifras-2024.pdf](https://cctunja.org.co/wp-content/uploads/2025/09/Boyaca-en-Cifras-2024.pdf) |
| PDF | 2023 | 1,2 MB | [Informe-Auditoria-Externa-CCT.pdf](https://cctunja.org.co/wp-content/uploads/2023/08/Informe-Auditoria-Externa-CCT.pdf) |
| PDF | 2023 | 9,8 MB | [Boyaca_Cifras_2023_V1.pdf](https://cctunja.org.co/wp-content/uploads/2024/08/Boyaca_Cifras_2023_V1.pdf) |
| PDF | 2022 | 11,7 MB | [Boyaca_en_Cifras_2022_.pdf](https://cctunja.org.co/wp-content/uploads/2023/08/Boyaca_en_Cifras_2022_.pdf) |
| PDF | 2021 | 15,0 MB | [BOYACA-EN-CIFRAS-2021.pdf](https://cctunja.org.co/wp-content/uploads/2022/08/BOYACA-EN-CIFRAS-2021.pdf) |
| PDF | 2020 | 11,7 MB | [Infograf%C3%ADa-Boyac%C3%A1-en-Cifras-2019-2020.pdf](https://cctunja.org.co/wp-content/uploads/2021/04/Infograf%C3%ADa-Boyac%C3%A1-en-Cifras-2019-2020.pdf) |
| PDF | 2020 | 5,0 MB | [Boyaca-en-Cifras-2019-2020.pdf](https://cctunja.org.co/wp-content/uploads/2021/07/Boyaca-en-Cifras-2019-2020.pdf) |
| PDF | 2019 | 4,4 MB | [Boyaca_Cifras_2019_.pdf](https://cctunja.org.co/wp-content/uploads/2019/09/Boyaca_Cifras_2019_.pdf) |
| PDF | 2019 | 17,8 MB | [Boyaca_Cifras_2018-2019-pdf.pdf](https://cctunja.org.co/wp-content/uploads/2020/06/Boyaca_Cifras_2018-2019-pdf.pdf) |
| PDF | 2018 | 5,8 MB | [BOYACA-EN-CIFRAS-2018.pdf](https://cctunja.org.co/wp-content/uploads/2021/03/BOYACA-EN-CIFRAS-2018.pdf) |
| PDF | 2016 | 7,4 MB | [Boyaca-en-Cifras-2015-2016.pdf](https://cctunja.org.co/wp-content/uploads/2021/03/Boyaca-en-Cifras-2015-2016.pdf) |
| Power BI |  | — | [view?r=eyJrIjoiMmUyZThjYzktMjVjNi00MWRmLWI2NzctZD%20Y1Yzc5Yj](https://app.powerbi.com/view?r=eyJrIjoiMmUyZThjYzktMjVjNi00MWRmLWI2NzctZD%20Y1Yzc5YjZlOTAwIiwidCI6IjUxMmIxNDc0LTUzMjctNDRlNS1hMmE2LTdjYjA2YWRiMTIzYiJ9) |
| Power BI |  | — | [view?r=eyJrIjoiY2RiYTdhOWEtNDU3Ni00OGQ0LWIyY2ItZjNjNjI0YjRiM](https://app.powerbi.com/view?r=eyJrIjoiY2RiYTdhOWEtNDU3Ni00OGQ0LWIyY2ItZjNjNjI0YjRiMjZiIiwidCI6IjkzYzk1NTZkLTc2NDAtNDBhNi05NTJhLWZlNTk5Yjk5MmE2MCIsImMiOjR9) |

Total: **14 fuentes** (11 PDF, 1 Excel, 2 tablero Power BI).

## 2. ¿Cuál es la base económica más precisa?

**La herramienta Excel 2024 (hoja `BaseMun`)** es la fuente más completa y verificable de la página:

- Es la **única en formato de datos** (las ediciones 2015–2023 solo están en PDF; el Power BI no permite descarga ni verificación).
- Es la **más reciente** (cifras 2024; el ICM es 2023 y la producción agrícola 2023).
- Cubre **123 de 123 municipios** con **51 variables** y códigos DANE, lo que permite cruzarla con otras bases.

### 2.1 Completitud por variable (% de municipios con dato)

| Variable | % |
|---|---|
| ICM | 18,7 % |
| Insti | 18,7 % |
| Infra | 18,7 % |
| Sosten | 18,7 % |
| Educa | 18,7 % |
| Salud | 18,7 % |
| SisFin | 18,7 % |
| Prod | 18,7 % |
| Bufalos_2021 | 48,0 % |
| Eventos_2024 | 90,2 % |
| Fin_BANCOLDEX | 96,7 % |
| Especial_2024 | 96,7 % |
| Ovino_2021 | 97,6 % |
| Aves_2022 | 97,6 % |
| Mat_2024 | 98,4 % |
| Ren_2024 | 98,4 % |
| Can_2024 | 98,4 % |
| Caprino_2021 | 99,2 % |
| *las demás 30 variables* | 100 % |

### 2.2 Consistencia interna

| Prueba | Cumplen | % |
|---|---|---|
| Hombres + Mujeres = Población total | 123 de 123 | 100,0 % |
| Suma de grupos de edad = Población total | 123 de 123 | 100,0 % |
| Canceladas ≤ matriculadas + renovadas | 121 de 123 | 98,4 % |
| Empleos COMFABOY ≤ población de 18 a 59 años | 123 de 123 | 100,0 % |
| Códigos DANE únicos | 123 de 123 | 100,0 % |

### 2.3 Suma de municipios frente a los totales del departamento

| Variable | Suma de los 123 municipios | Fila «Departamento» (BaseMun) | Hoja departamental (BaseBoy) | Diferencia |
|---|---|---|---|---|
| Población total | 1.311.983 | 1.311.983 | 1.311.983 | 0,00 % |
| Hombres | 647.741 | 647.741 | — | 0,00 % |
| Mujeres | 664.242 | 664.242 | — | 0,00 % |
| Valor agregado (miles de millones $) | 39.049 | 39.049 | 25.177 | 0,00 % |
| Empresas matriculadas | 10.572 | 10.572 | — | 0,00 % |
| Empresas renovadas | 50.660 | 50.660 | — | 0,00 % |
| Captaciones (millones $) | 7.702.722 | 7.702.722 | — | 0,00 % |
| Colocaciones (millones $) | 7.435.045 | 7.435.045 | — | -0,00 % |

### 2.4 Anomalías detectadas

- Fila 'Departamento': los 6 grupos de edad tienen el mismo valor (164.450); la suma municipal real es 121.663, 156.032, 60.782, 177.950, 560.291, 235.265.
- **Valor agregado**: la base municipal suma 39.049 y la hoja departamental reporta un PIB 2024 de 25.177 (miles de millones), 55,1 % más. Probablemente son precios corrientes (municipal) frente a precios constantes (departamental); **no deben mezclarse** en un mismo cálculo.
- El ICM viene como **puesto** (1 = mejor), no como puntaje; y el riesgo del agua como categoría IRCA.

## 3. Estadísticas económicas (valor agregado 2024)

- Valor agregado total (suma municipal): **39.049 miles de millones de pesos**.
- Los **3 mayores** (Tunja, Sogamoso, Duitama) concentran el **31,9 %**; los 10 mayores, el 60,7 %.
- Índice de concentración Herfindahl-Hirschman: **518** (baja concentración).
- Mediana municipal: 110,6 miles de millones; valor agregado por habitante: mediana 20,8 millones $.

| # | Municipio | Provincia | Valor agregado | % del depto. | Por habitante (millones $) |
|---|---|---|---|---|---|
| 1 | Tunja | Centro | 5.163,7 | 13,22 % | 27,6 |
| 2 | Sogamoso | Sugamuxi | 4.123,7 | 10,56 % | 29,9 |
| 3 | Duitama | Tundama | 3.178,2 | 8,14 % | 23,9 |
| 4 | Puerto Boyacá | Occidente | 3.084,6 | 7,90 % | 60,9 |
| 5 | Nobsa | Sugamuxi | 2.181,7 | 5,59 % | 125,9 |
| 6 | Chiquinquirá | Occidente | 1.329,0 | 3,40 % | 21,9 |
| 7 | Santa María | Neira | 1.301,1 | 3,33 % | 346,2 |
| 8 | Tibasosa | Sugamuxi | 1.141,8 | 2,92 % | 81,2 |
| 9 | Tuta | Centro | 1.134,5 | 2,91 % | 127,3 |
| 10 | Paipa | Tundama | 1.055,7 | 2,70 % | 29,0 |

**Por provincia**

| Provincia | Municipios | Valor agregado | % | Por habitante (millones $) |
|---|---|---|---|---|
| Sugamuxi | 13 | 8.808,6 | 22,6 % | 38,6 |
| Centro | 15 | 8.645,0 | 22,1 % | 28,5 |
| Occidente | 16 | 6.325,5 | 16,2 % | 33,3 |
| Tundama | 9 | 4.828,9 | 12,4 % | 23,6 |
| Ricaurte | 13 | 2.948,0 | 7,5 % | 28,5 |
| Neira | 6 | 1.912,1 | 4,9 % | 47,3 |
| Márquez | 10 | 1.904,6 | 4,9 % | 29,7 |
| Valderrama | 7 | 964,1 | 2,5 % | 23,2 |
| Oriente | 8 | 744,1 | 1,9 % | 21,7 |
| Norte | 9 | 713,4 | 1,8 % | 20,7 |
| Gutiérrez | 7 | 565,5 | 1,4 % | 18,0 |
| Lengupá | 6 | 521,0 | 1,3 % | 21,1 |
| La Libertad | 4 | 168,4 | 0,4 % | 15,4 |

## 3b. Uso del suelo según los predios (criterio del usuario)

- **Zona urbana** = actividad económica. **Zona rural**: predios de 10 a 300 m² = **vivienda rural**; mayores a 300 m² = **uso agropecuario**; menores a 10 m² = atípicos (revisar).

| Clase | Predios | % de predios | Área (ha) | % del área catastral |
|---|---|---|---|---|
| Urbano (actividad económica) | 209.059 | 27,6 % | 9.761 | 0,43 % |
| Rural vivienda (10–300 m²) | 15.314 | 2,0 % | 233 | 0,01 % |
| Rural agropecuario (> 300 m²) | 531.794 | 70,3 % | 2.260.948 | 99,56 % |
| Rural atípico (< 10 m²) | 30 | 0,0 % | — | — |

**¿Se cumple el criterio? Correlación con los indicadores económicos (Pearson y Spearman, 123 municipios)**

| Relación | Pearson | Spearman (por rangos) | Lectura |
|---|---|---|---|
| Valor agregado ↔ predios urbanos | 0,91 | 0,67 | moderada |
| Valor agregado ↔ área urbana de los predios | 0,92 | 0,66 | moderada |
| Empresas renovadas ↔ predios urbanos | 0,97 | 0,83 | fuerte |
| Producción agrícola (ton) ↔ área agropecuaria | -0,06 | 0,07 | débil |
| Bovinos ↔ área agropecuaria | 0,63 | 0,72 | fuerte |
| Población ↔ viviendas (predios urbanos + vivienda rural) | 0,97 | 0,77 | fuerte |

- Los 3 municipios con más valor agregado tienen el **42,4 %** de los predios urbanos del departamento y generan el **31,9 %** del valor agregado: la actividad económica se concentra en lo urbano, como plantea el criterio.


## 4. Coincidencias entre la página y el repositorio

Se comparan los municipios de la página (Excel 2024) con los del repositorio (DIVIPOLA-DANE en `catastro/indice_municipios.csv`, que usa el visor).

| Resultado | Municipios |
|---|---|
| Código y nombre idénticos | 122 |
| Código igual; nombre igual sin tildes/mayúsculas | 1 |

**Cruce con los datos propios (correlación de Pearson, 123 municipios)**

| | Valor agregado | Población | Predios urbanos | Área urbana |
|---|---|---|---|---|
| Valor agregado | 1,00 | 0,93 | 0,91 | 0,92 |
| Población | 0,93 | 1,00 | 0,97 | 0,94 |
| Predios urbanos | 0,91 | 0,97 | 1,00 | 0,98 |
| Área urbana | 0,92 | 0,94 | 0,98 | 1,00 |

- Habitantes por predio urbano: mediana 8,5.
- Densidad: mediana 43,3 hab/km²; máxima 1.564 (Tunja).

El detalle municipio por municipio está en `informes/coincidencias_municipios.csv`.
