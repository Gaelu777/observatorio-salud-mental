# Reporte de limpieza y preprocesamiento — E1

> Archivo generado automáticamente por `src/oro.py`. No editar a mano: las cifras se recalculan en cada corrida.

Alcance: defunciones de **residentes del estado de Colima** (`ent_resid = 06`). Se excluyen 3,582 registros de no residentes o con residencia desconocida (861 desconocida); siguen en Plata, solo quedan fuera del análisis.

## 1. Valores faltantes

Residentes de Colima en Plata: **33,554** defunciones. Faltantes por variable (códigos *no especificado* de INEGI convertidos a nulo en Plata):

| variable | faltantes | pct |
|---|---|---|
| mes de ocurrencia | 96 | 0.286 |
| año de ocurrencia | 87 | 0.259 |
| sexo | 3 | 0.009 |
| edad | 61 | 0.182 |
| municipio de residencia | 21 | 0.063 |
| día de ocurrencia | 120 | 0.358 |

### Diagnóstico del mecanismo para *mes de ocurrencia*

| variable observada | chi2 | gl | p | % sin mes por nivel |
|---|---|---|---|---|
| tipo de defunción (violenta / no violenta) | 293.700 | 1 | 0.000 | no_violenta: 0.06%, violenta: 1.4% |
| sexo | 10.900 | 2 | 0.004 | H: 0.36%, M: 0.17%, NE: 0.0% |
| grupo de edad | 4516.800 | 4 | 0.000 | 0-14: 0.0%, 15-24: 0.67%, 25-59: 0.48%, 60+: 0.04%, NE: 45.9% |
| zona | 90.500 | 2 | 0.000 | NE: 9.52%, metropolitana: 0.13%, resto: 0.44% |
| año de registro | 61.300 | 5 | 0.000 | 2018: 0.09%, 2019: 0.22%, 2020: 0.05%, 2021: 0.24%, 2022: 0.74%, 2023: 0.36% |

**Conclusión:** se rechaza MCAR (α = 0.05). La falta del mes se asocia con variables observadas, principalmente con el tipo de defunción: las muertes violentas pierden la fecha con mucha más frecuencia, porque el cuerpo a veces se encuentra días después y el médico legista no puede fijar la fecha. Esto es **MAR** respecto al tipo de defunción. Además hay un componente **MNAR** que no se puede probar: cuanto más tiempo pasa sin encontrar el cuerpo, más probable es que se desconozca justo el mes. También se observa **faltante conjunto**: cuando falta la edad (NE), casi la mitad de esos registros tampoco tiene mes; son casos de cuerpos no identificados.

**Tratamiento:**
- *Año desconocido* → se imputa con el **año de registro**, que coincide con el de ocurrencia en 99.5 % de los casos con año conocido (imputación condicional determinista).
- *Mes desconocido* → **hot-deck condicional**: a cada registro se le asigna un mes sorteado de la distribución observada de su mismo grupo de causa (suicidio / trastorno mental / otra). Como el mecanismo es MAR por tipo de causa, imputar por grupo de causa es lo que corrige el sesgo; imputar con la moda inflaría artificialmente un solo mes. Semilla fija = 42 (reproducible). Cada registro queda marcado con `mes_imputado = True`.
- *Sexo / edad / municipio desconocidos* → **no se imputan**: son pocos casos y se reportan como categoría *No especificado* en las tablas de factores. Imputarlos inventaría información demográfica.
- *Meses sin defunciones* → son **ceros reales**, no faltantes: la malla mensual se completa con 0.

## 2. Atípicos y ruido

Se aplican **IQR** (Tukey, 1.5·IQR) y **Z robusto** (0.6745·(x − mediana)/MAD, umbral 3.5) a los conteos mensuales. No se usa el Z clásico porque la media y la desviación estándar se ven afectadas por el mismo valor atípico que se busca. Isolation Forest tampoco tiene sentido para una sola variable con 72 datos.

**Tratamiento:** los atípicos **no se borran**, porque son muertes reales. Se marcan y se crea una versión *winsorizada* (recortada al límite superior del IQR) para modelos sensibles a valores extremos. El pronóstico debe compararse con y sin winsorizar.

| serie | mediana | MAD | límite IQR | atípicos IQR | atípicos Z robusto | meses marcados |
|---|---|---|---|---|---|---|
| suicidio | 4.000 | 1.000 | [0.0, 8.6] | 4 | 2 | 2020-12 (10), 2021-08 (13), 2022-02 (9), 2022-09 (9) |
| trastorno_mental | 3.000 | 1.000 | [0.0, 8.5] | 0 | 0 | ninguno |

Ruido de captura: los archivos 2018–2021 traen tabuladores pegados a los valores (`"06\t"`). Se quitaron en Plata; el conteo exacto de celdas corregidas está en `data/plata/resumen_plata.json`.

## 3. Integración de fuentes heterogéneas

| Conflicto | Fuente(s) | Resolución |
|---|---|---|
| Mismo dato con nombre distinto: `presunto` (2018–2021) vs `tipo_defun` (2022+) | EDR | Se renombra a `tipo_defun` (mismo catálogo) en Plata |
| Número de columnas distinto por año (59 vs 73–74) | EDR | Selección de las 13 variables presentes en todos los años |
| Llave de municipio: `mun_resid` (EDR), `cve_mun` (DENUE), `MUN` (Censo) | las 3 | Llave única `cve_mun` texto de 3 dígitos con ceros a la izquierda |
| Codificación de texto: DENUE en Latin-1, Censo en UTF-8 con BOM, EDR solo códigos | DENUE, Censo | Todo se escribe en UTF-8; los nombres oficiales de municipio salen del Censo |
| Niveles mezclados en una tabla (estado, municipio, localidad) | Censo | Solo se toman los totales municipales (`LOC=0000`) |
| Valores reservados `*` por confidencialidad | Censo | Nulo (no cero); los totales municipales no los tienen |
| Personal ocupado como rango de texto (`0 a 5 personas`) | DENUE | Se separa en `per_ocu_min` / `per_ocu_max` numéricos |
| Granularidad temporal: EDR mensual 2018–2023, Censo fijo 2020, DENUE foto 2026 | las 3 | Tasas con población 2020 como denominador (punto medio del periodo); la oferta se trata como actual. Se declara como limitación |
| Dos campos para "suicidio": causa CIE-10 X60–X84 vs `tipo_defun = 3` | EDR | Coinciden en 327 casos; 0 solo por CIE-10 y 0 solo por tipo. Prevalece la **causa básica CIE-10**, que es la causa certificada y la definición estándar de la OMS |

Nombres de municipio que difieren entre DENUE y Censo: **0** (ninguno tras pasar todo a UTF-8).

## 4. Normalización y estandarización

Se calculan **Min-Max** (`x' = (x − min)/(max − min)`, rango [0, 1]) y **Z-Score** (`(x − media)/desv`) para las series mensual y trimestral y para las variables municipales. Min-Max se usará en el agrupamiento de municipios (E3), donde todas las variables deben pesar igual. Z-Score se usará en modelos que suponen variables centradas. Las columnas originales se conservan.

## 5. Discretización y jerarquías conceptuales

| Dimensión | Jerarquía |
|---|---|
| Causa | código CIE-10 (X700) → categoría (X70) → grupo analítico (suicidio X60–X84 / trastorno mental F / otra) → capítulo (X) |
| Tiempo | día → mes → trimestre → semestre → año |
| Lugar | municipio → zona (Zona Metropolitana Colima–Villa de Álvarez / resto) → estado |
| Edad | años → grupo 0-14, 15-24, 25-59, 60+. Cortes elegidos para coincidir con los grupos que publica el Censo y poder calcular tasas |
| Oferta y necesidad municipal | valor continuo → nivel baja/media/alta por **terciles** (igual frecuencia). Con intervalos de igual ancho, la concentración de consultorios en la capital dejaría casi todos los municipios en *baja* |

## 6. Reducción de datos

- **Selección de variables:** de 59–74 columnas de EDR se conservan 13 (más las de linaje).
- **Selección de filas:** solo residentes de Colima, años 2018–2023 y causas de salud mental.
- **Agregación:** registro individual → conteo mensual (72 periodos) → conteo trimestral (24 periodos).
- **Muestreo:** no se aplica. Los datos ya son el universo de registros y son pocos; muestrear solo perdería información.

## 7. Resultado

- Serie mensual: 72 periodos; suicidios por mes: mín 0, mediana 4, máx 13.
- Suicidios con mes imputado: 1; trastornos mentales con mes imputado: 0.

**Advertencia de áreas pequeñas:** en municipios con poca población (Ixtlahuacán, Minatitlán) un solo caso cambia mucho la tasa por 100 mil. Para E3 se recomienda suavizar las tasas (p. ej. Bayes empírico) o agrupar esos municipios antes de compararlos.

Tabla municipal integrada:

| cve_mun | nom_mun | pobtot | consultorios_psic | consultorios_por_100k | tasa_suicidio_anual_100k | oferta_nivel | necesidad_nivel | zona |
|---|---|---|---|---|---|---|---|---|
| 001 | Armería | 27626 | 0 | 0.000 | 10.260 | baja | alta | resto |
| 002 | Colima | 157048 | 62 | 39.480 | 8.910 | alta | alta | metropolitana |
| 003 | Comala | 21661 | 3 | 13.850 | 10.000 | alta | alta | metropolitana |
| 004 | Coquimatlán | 20837 | 1 | 4.800 | 4.800 | baja | baja | metropolitana |
| 005 | Cuauhtémoc | 31267 | 3 | 9.590 | 6.930 | media | media | metropolitana |
| 006 | Ixtlahuacán | 5623 | 0 | 0.000 | 11.860 | baja | alta | resto |
| 007 | Manzanillo | 191031 | 20 | 10.470 | 6.810 | alta | media | resto |
| 008 | Minatitlán | 10231 | 1 | 9.770 | 0.000 | media | baja | resto |
| 009 | Tecomán | 116305 | 7 | 6.020 | 7.740 | media | media | resto |
| 010 | Villa de Álvarez | 149762 | 20 | 13.350 | 6.340 | alta | baja | metropolitana |

