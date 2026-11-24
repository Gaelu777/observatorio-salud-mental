# Ficha técnica del dataset (datasheet)

**Observatorio de Servicios Psicológicos · Colima: capa Oro**

Formato basado en *Datasheets for Datasets* (Gebru et al., 2021).
Versión: 2026-11-24 · Licencia: **CC BY 4.0** (ver la sección 8).

## 1. Motivación

- **Para qué se creó:** para responder, con datos públicos, dónde y cuándo hay necesidad de atención en salud mental en Colima y dónde falta oferta de psicólogos. La usuaria principal es una psicóloga con consultorio propio en la ciudad de Colima, que la usa para decidir horarios, difusión y una posible segunda sede.
- **Quién lo creó:** Gael Alexandro Cortez Sarmienta y Luis Alejandro Mendoza Peñaloza, como proyecto integrador escolar.
- **Financiamiento:** ninguno.

## 2. Composición

| Tabla | Unidad | Filas | Periodo |
|---|---|---|---|
| `serie_mensual_colima.csv` | mes | 72 | 2018-01 a 2023-12 |
| `serie_trimestral_colima.csv` | trimestre | 24 | 2018 a 2023 |
| `factores_suicidio.csv` | año × trimestre × sexo × grupo de edad × zona | 137 | 2018 a 2023 |
| `municipios_colima.csv` | municipio | 10 | Censo 2020; DENUE 2026 |
| `localidades_colima.csv` | localidad de 500 habitantes o más | 65 | Censo 2020; DENUE 2026 |
| `consultorios_psicologia_geo.csv` / `.geojson` | establecimiento | 117 | DENUE, captura 2026-11-23 |
| `competencia_centro_colima.csv` | radio | 3 | DENUE 2026 |
| `pronostico_suicidio_colima.csv` | mes pronosticado | 12 | 2024 |
| `linaje_oro.csv` | enlace entre Oro y Bronce | 2,191 | — |

- El significado de cada columna está en [`data/oro/DICCIONARIO.md`](../../data/oro/DICCIONARIO.md).
- **¿Contiene datos de personas?** No. Las defunciones se publican **agregadas** (conteos por mes, municipio, sexo o grupo de edad), y nunca se publica un registro individual. Los consultorios son *establecimientos* y se identifican por la CLEE del INEGI. No se incluye el nombre del negocio ni el teléfono, aunque el DENUE los publica.
- **Celdas pequeñas:** algunas combinaciones de `factores_suicidio.csv` tienen conteos de 1 o 2. Son agregados oficiales del INEGI, pero **no deben cruzarse con otras fuentes locales** para tratar de identificar casos (ver la sección 5).
- **Faltantes:** el 100 % de las celdas de Oro está lleno. Los faltantes de origen, como el mes de ocurrencia no especificado, se imputaron y quedaron marcados en `*_mes_imputado` (ver `docs/E1/reporte_limpieza.md`).

## 3. Proceso de captura

| Fuente | Método | Frecuencia |
|---|---|---|
| INEGI, Estadística de Defunciones Registradas (datos abiertos) | Descarga del ZIP oficial y filtro por entidad 06 | Mensual (el INEGI publica una vez al año) |
| INEGI, DENUE, descarga masiva de Colima (SCIAN 621) | Descarga del CSV oficial | **Diaria** |
| INEGI, Censo 2020, ITER Colima | Descarga del CSV oficial | Mensual (edición fija) |
| INEGI, Marco Geoestadístico 2020 | Descarga del shapefile oficial | Mensual (edición fija) |

- **Automatización:** todo se descarga con GitHub Actions (`.github/workflows/extraccion-bronce.yml`).
- **Ética de la descarga:** User-Agent identificable, 5 s de pausa entre descargas y solo rutas permitidas por robots.txt.
- **Registro:** cada archivo queda en `data/bronce/manifiesto.csv` con su URL, fecha UTC y SHA-256.

## 4. Preprocesamiento

**Bronce → Plata:**
- Limpieza de espacios y tabuladores.
- Puerta de calidad Pandera: tipos, rangos, reglas de fecha y unicidad. Los registros inválidos van a `data/cuarentena/` con su motivo.

**Plata → Oro:**
- Clasificación CIE-10: X60–X84 es suicidio y el capítulo F son los trastornos mentales.
- Imputación del mes faltante.
- Marcado de atípicos (IQR y Z robusto), sin borrarlos.
- Normalización min-max y z-score.
- Discretización en terciles y grupos de edad.
- Unión espacial con el Marco Geoestadístico (EPSG:6372).
- Distancias.
- PCA.

El detalle está en `docs/E1/reporte_limpieza.md`, `docs/E2/ENTREGA.md` y `docs/E3/multivariado.md`. Los datos crudos se conservan sin cambios en `data/bronce/`.

## 5. Usos

**Usos recomendados:**
- Planear dónde y cuándo ofrecer servicios de psicología en Colima.
- Detectar localidades con poca oferta (`localidades_colima.csv`: distancia al psicólogo, CP1).
- Fines de docencia en series de tiempo, diseño de experimentos y estadística multivariada.

**Usos NO recomendados:**
- **Identificar personas o casos individuales.** Cruzar los conteos pequeños con noticias o registros locales para "adivinar" quién falleció es un uso indebido.
- **Medir la demanda de terapia.** Las defunciones son un indicador de necesidad *extrema*, no de cuánta gente busca un psicólogo.
- **Evaluar a un psicólogo o consultorio en particular.** El DENUE solo dice que el consultorio existe, no cómo atiende.
- **Afirmar causalidad.** Que una localidad sea vulnerable y esté lejos de un psicólogo no prueba que una cosa cause la otra.
- **Usar el pronóstico de 2024 como alerta.** Su intervalo es amplio (0 a 9 por mes) y el modelo ganador equivale a la media histórica.

## 6. Sesgos y limitaciones conocidas

- **Subregistro de suicidios:** algunos se registran como accidentes. Esto es un sesgo conocido de las estadísticas vitales.
- **Oferta subestimada:** el DENUE no incluye a los psicólogos que atienden en consultorios médicos generales, en instituciones o solo en línea.
- **Fechas distintas:** el Censo es de 2020 y el DENUE de 2026.
- **Rezago de la fuente:** el INEGI publica las defunciones con alrededor de 10 meses de retraso.

## 7. Mantenimiento

- **Actualización:** el pipeline corre solo todos los días. Cada corrida queda en `data/bitacora/capturas.csv`.
- **Contacto:** por medio de los issues del repositorio en GitHub.
- **Versiones:** cada entrega tiene su tag de git (`e1`, `e2`, ...). Una versión vieja del dataset se recupera con `git checkout <tag>`.

## 8. Licencia y atribución

- **Datos derivados (capa Oro):** se publican bajo **Creative Commons Atribución 4.0 Internacional (CC BY 4.0)**, que es compatible con los *Términos de Libre Uso de la Información del INEGI*. Estos términos permiten copiar, distribuir y adaptar la información siempre que se cite la fuente.
- **Cita sugerida:** *Cortez Sarmienta, G. A. y Mendoza Peñaloza, L. A. (2026). Observatorio de Servicios Psicológicos · Colima [conjunto de datos]. Elaborado con datos de INEGI: Estadística de Defunciones Registradas 2018–2023, DENUE, Censo de Población y Vivienda 2020 y Marco Geoestadístico 2020.*
- **Aviso:** este proyecto no está respaldado por el INEGI.
