# Ficha de entrega técnica — E2

| Campo | Valor |
|---|---|
| Tag | `e2` |
| Equipo | Gael Alexandro Cortez Sarmienta · Luis Alejandro Mendoza Peñaloza |
| Fuente especializada | **Geoespacial**: DENUE (INEGI) + Marco Geoestadístico 2020 con GeoPandas |

## Checklist contra la rúbrica

| # | Requisito | Dónde se cumple | Evidencia |
|---|---|---|---|
| 1 | Fuente especializada geoespacial con GeoPandas y visualización cartográfica | `src/extraer_marcogeo.py`, `src/geoespacial.py` | `docs/E2/mapa_oferta_necesidad.png`, `docs/E2/mapa_centro_colima.png` |
| 2 | Declaración de ética y legalidad (términos, robots.txt, licencias, sesgos, privacidad) | `docs/etica-datos.md` | Copia fechada de robots.txt en `docs/E0/evidencia/` |
| 3 | Linaje: cada registro de Oro rastreable hasta Bronce y su fecha de ingesta | `data/oro/linaje_oro.csv`, columnas de linaje en cada tabla, `src/verificar_linaje.py` | `docs/E2/verificacion_linaje.md` (resultado OK) |
| 4 | Ficha de entrega y relatoría | este archivo, `docs/relatoria-E2.md` | — |
| 5 | **Análisis Estadístico:** experimento factorial 2³ con aleatorización, 3 réplicas y bloque; ANOVA de dos vías (2 × 3) con interacción; matrices 2⁴ y 2⁴⁻¹ con alias; supuestos y corrida de confirmación | `src/experimento_factorial.py` | [`docs/E2/experimento.md`](experimento.md), datos y gráficas en `docs/E2/experimento/` |
| 6 | **Calidad:** evaluación ISO/IEC 25010 (producto) e ISO/IEC 25012 (datos de la capa Oro) con métricas medidas; antecedentes normativos 9126 / SQuaRE / ISO 9001 | — | [`docs/E2/evaluacion-iso.md`](evaluacion-iso.md) |

## 1. Fuente geoespacial

**Datos:** 117 consultorios de psicología del DENUE (puntos con latitud y longitud) y los polígonos oficiales de los 10 municipios del Marco Geoestadístico 2020 (misma vintage que el Censo, así que las claves coinciden).

**Procesamiento con GeoPandas:**
- Reproyección a **EPSG:6372** (Mexico ITRF2008 / LCC, en metros) para medir distancias reales. Con grados de latitud y longitud no se pueden medir metros.
- **Validación espacial (punto en polígono):** el punto de cada consultorio cae dentro del municipio que declara DENUE en **117 de 117** casos.
- **Competencia cercana:** consultorios a 500 m, 1 km y 2 km del centro histórico de Colima (Jardín Libertad).
- Se recorta el archipiélago de Revillagigedo (que pertenece a Manzanillo) para que el mapa sea legible.

**Resultados:**

| Radio desde el centro | Consultorios de psicología | % del municipio de Colima |
|---|---|---|
| 500 m | 3 | 4.8 % |
| 1 km | 12 | 19.4 % |
| 2 km | 31 | 50.0 % |

La mitad de los consultorios del municipio de Colima está a menos de 2 km del centro, así que la cliente tiene **competencia directa alta**. Armería e Ixtlahuacán no tienen consultorios registrados y tienen las tasas de suicidio más altas del estado (ver mapa). Son candidatos para atención a distancia o una sede alterna, con la advertencia de que sus tasas son inestables por su población pequeña.

**Salidas en Oro:** `consultorios_psicologia_geo.csv`, `consultorios_psicologia_colima.geojson` y `competencia_centro_colima.csv`.

## 2. Linaje y trazabilidad

**Cómo se construye la cadena:**

```
origen (URL INEGI) ──SHA-256, fecha de ingesta──▶ data/bronce/manifiesto.csv
        │
Bronce: archivo + número de fila ──▶ Plata: id_registro, archivo_bronce, fila_bronce, fecha_ingesta_utc, sha256_origen
        │
Oro: cada tabla tiene n_registros_fuente y fecha_ingesta_max;
     data/oro/linaje_oro.csv lista, para cada fila de Oro, todos los id_registro que la forman
```

- `id_registro` tiene el formato `<FUENTE>:<archivo Bronce>:<fila>`, por ejemplo `EDR:defunciones_colima_registradas_2021:121`.
- Un conteo **cero** también es trazable: su linaje apunta a los archivos de Bronce que se revisaron (`id_registro = SIN_REGISTROS`).

**Verificación automática** (`src/verificar_linaje.py`, corre en cada ejecución del workflow):
1. Toda fila de Oro tiene linaje.
2. Todo `id_registro` del linaje existe en Plata con el mismo archivo y fila.
3. Todo archivo de Bronce existe y está en el manifiesto con la misma fecha de ingesta.
4. Se **re-lee la fila exacta** en Bronce y el valor coincide con Plata.
5. `n_registros_fuente` coincide con el linaje.

Resultado actual: **652 de 652** registros fuente verificados de punta a punta y las 6 tablas Oro cubiertas al 100 %. También se probó con un linaje corrompido a propósito: el verificador detecta la fila faltante y la fila alterada y detiene el pipeline.

## Cómo reproducir

```bash
pip install -r requirements.txt
python src/extraer_marcogeo.py
python src/plata.py && python src/oro.py
python src/geoespacial.py
python src/verificar_linaje.py
```
