# Diccionario de datos · capa Oro

Generado por `src/diccionario_oro.py`; **no editar a mano** (se regenera en cada corrida del pipeline). Tipo, nulos, mínimo y máximo se miden sobre los datos actuales.

El archivo `consultorios_psicologia_colima.geojson` tiene las mismas columnas que `consultorios_psicologia_geo.csv` más la geometría (punto, EPSG:4326).

**Completitud global (ISO/IEC 25012):** 100.0 % de celdas no nulas en promedio por columna; columnas con algún nulo: 0 de 128.

## `serie_mensual_colima.csv` (72 filas)

Serie mensual estatal (ene-2018 a dic-2023) de suicidios y defunciones por trastornos mentales de residentes de Colima. Base del pronóstico (E1).

| Columna | Descripción | Unidad / dominio | Origen | Tipo | Nulos % | Mín | Máx |
|---|---|---|---|---|---|---|---|
| `periodo` | Mes (AAAA-MM) o trimestre (AAAA-Tn) de ocurrencia | texto | EDR: anio_ocur + mes_ocurr | texto | 0.0 |  |  |
| `anio` | Año de ocurrencia de la defunción | 2018-2023 | EDR: anio_ocur | numérico | 0.0 | 2018.0 | 2023.0 |
| `mes` | Mes de ocurrencia | 1-12 | EDR: mes_ocurr | numérico | 0.0 | 1.0 | 12.0 |
| `trimestre` | Trimestre de ocurrencia | 1-4 | Derivado del mes | numérico | 0.0 | 1.0 | 4.0 |
| `semestre` | Semestre de ocurrencia | 1-2 | Derivado del mes | numérico | 0.0 | 1.0 | 2.0 |
| `suicidio` | Defunciones de residentes de Colima con causa CIE-10 X60-X84 (lesiones autoinfligidas) | conteo | EDR: causa_def, ent_resid=06 | numérico | 0.0 | 0.0 | 13.0 |
| `suicidio_mes_imputado` | 1 si el mes de ocurrencia faltaba y se imputó (ver reporte de limpieza) de `suicidio` | 0/1 | Derivado en Oro (src/oro.py) | numérico | 0.0 | 0.0 | 1.0 |
| `suicidio_atipico_iqr` | True si queda fuera de [Q1 − 1.5·IQR, Q3 + 1.5·IQR] (marcado, no borrado) de `suicidio` | booleano | Derivado en Oro (src/oro.py) | booleano | 0.0 |  |  |
| `suicidio_z_robusto` | 0.6745·(x − mediana)/MAD de `suicidio` | adimensional | Derivado en Oro (src/oro.py) | numérico | 0.0 | -2.698 | 6.07 |
| `suicidio_atipico_z_robusto` | True si |z robusto| > 3.5 de `suicidio` | booleano | Derivado en Oro (src/oro.py) | booleano | 0.0 |  |  |
| `suicidio_winsor` | Valor recortado a los límites IQR (para modelos sensibles a extremos) de `suicidio` | misma unidad | Derivado en Oro (src/oro.py) | numérico | 0.0 | 0.0 | 8.625 |
| `suicidio_minmax` | Normalización min-max a [0, 1] de `suicidio` | 0-1 | Derivado en Oro (src/oro.py) | numérico | 0.0 | 0.0 | 1.0 |
| `suicidio_z` | Estandarización z-score (media 0, desviación 1) de `suicidio` | adimensional | Derivado en Oro (src/oro.py) | numérico | 0.0 | -1.8949 | 3.529 |
| `trastorno_mental` | Defunciones con causa CIE-10 capítulo F (trastornos mentales y del comportamiento) | conteo | EDR: causa_def, ent_resid=06 | numérico | 0.0 | 0.0 | 8.0 |
| `trastorno_mental_mes_imputado` | 1 si el mes de ocurrencia faltaba y se imputó (ver reporte de limpieza) de `trastorno_mental` | 0/1 | Derivado en Oro (src/oro.py) | numérico | 0.0 | 0.0 | 0.0 |
| `trastorno_mental_atipico_iqr` | True si queda fuera de [Q1 − 1.5·IQR, Q3 + 1.5·IQR] (marcado, no borrado) de `trastorno_mental` | booleano | Derivado en Oro (src/oro.py) | booleano | 0.0 |  |  |
| `trastorno_mental_z_robusto` | 0.6745·(x − mediana)/MAD de `trastorno_mental` | adimensional | Derivado en Oro (src/oro.py) | numérico | 0.0 | -2.023 | 3.372 |
| `trastorno_mental_atipico_z_robusto` | True si |z robusto| > 3.5 de `trastorno_mental` | booleano | Derivado en Oro (src/oro.py) | booleano | 0.0 |  |  |
| `trastorno_mental_winsor` | Valor recortado a los límites IQR (para modelos sensibles a extremos) de `trastorno_mental` | misma unidad | Derivado en Oro (src/oro.py) | numérico | 0.0 | 0.0 | 8.0 |
| `trastorno_mental_minmax` | Normalización min-max a [0, 1] de `trastorno_mental` | 0-1 | Derivado en Oro (src/oro.py) | numérico | 0.0 | 0.0 | 1.0 |
| `trastorno_mental_z` | Estandarización z-score (media 0, desviación 1) de `trastorno_mental` | adimensional | Derivado en Oro (src/oro.py) | numérico | 0.0 | -1.564 | 2.9859 |
| `n_registros_fuente` | Registros de Bronce que sostienen la fila (ver linaje_oro.csv) | conteo | Linaje | numérico | 0.0 | 2.0 | 19.0 |
| `fecha_ingesta_max` | Fecha UTC de la captura más reciente entre los registros que forman la fila | ISO 8601 | manifiesto Bronce | texto | 0.0 |  |  |

## `serie_trimestral_colima.csv` (24 filas)

La misma serie agregada por trimestre (reducción de datos por agregación).

| Columna | Descripción | Unidad / dominio | Origen | Tipo | Nulos % | Mín | Máx |
|---|---|---|---|---|---|---|---|
| `periodo` | Mes (AAAA-MM) o trimestre (AAAA-Tn) de ocurrencia | texto | EDR: anio_ocur + mes_ocurr | texto | 0.0 |  |  |
| `anio` | Año de ocurrencia de la defunción | 2018-2023 | EDR: anio_ocur | numérico | 0.0 | 2018.0 | 2023.0 |
| `trimestre` | Trimestre de ocurrencia | 1-4 | Derivado del mes | numérico | 0.0 | 1.0 | 4.0 |
| `suicidio` | Defunciones de residentes de Colima con causa CIE-10 X60-X84 (lesiones autoinfligidas) | conteo | EDR: causa_def, ent_resid=06 | numérico | 0.0 | 6.0 | 25.0 |
| `trastorno_mental` | Defunciones con causa CIE-10 capítulo F (trastornos mentales y del comportamiento) | conteo | EDR: causa_def, ent_resid=06 | numérico | 0.0 | 2.0 | 15.0 |
| `suicidio_minmax` | Normalización min-max a [0, 1] de `suicidio` | 0-1 | Derivado en Oro (src/oro.py) | numérico | 0.0 | 0.0 | 1.0 |
| `suicidio_z` | Estandarización z-score (media 0, desviación 1) de `suicidio` | adimensional | Derivado en Oro (src/oro.py) | numérico | 0.0 | -1.8247 | 2.7221 |
| `trastorno_mental_minmax` | Normalización min-max a [0, 1] de `trastorno_mental` | 0-1 | Derivado en Oro (src/oro.py) | numérico | 0.0 | 0.0 | 1.0 |
| `trastorno_mental_z` | Estandarización z-score (media 0, desviación 1) de `trastorno_mental` | adimensional | Derivado en Oro (src/oro.py) | numérico | 0.0 | -2.0466 | 2.2103 |
| `n_registros_fuente` | Registros de Bronce que sostienen la fila (ver linaje_oro.csv) | conteo | Linaje | numérico | 0.0 | 14.0 | 38.0 |
| `fecha_ingesta_max` | Fecha UTC de la captura más reciente entre los registros que forman la fila | ISO 8601 | manifiesto Bronce | texto | 0.0 |  |  |

## `factores_suicidio.csv` (137 filas)

Conteos de suicidios por año, trimestre, sexo, grupo de edad y zona. Base de los factores del experimento y de la comparación de grupos.

| Columna | Descripción | Unidad / dominio | Origen | Tipo | Nulos % | Mín | Máx |
|---|---|---|---|---|---|---|---|
| `anio` | Año de ocurrencia de la defunción | 2018-2023 | EDR: anio_ocur | numérico | 0.0 | 2018.0 | 2023.0 |
| `trimestre` | Trimestre de ocurrencia | 1-4 | Derivado del mes | numérico | 0.0 | 1.0 | 4.0 |
| `sexo` | Sexo de la persona fallecida (NE = no especificado) | H / M / NE | EDR: sexo | texto | 0.0 |  |  |
| `grupo_edad` | Grupo de edad en años cumplidos (NE = no especificado) | rangos | EDR: edad (discretizada) | texto | 0.0 |  |  |
| `zona` | Zona Metropolitana Colima-Villa de Álvarez (002, 003, 004, 005, 010) vs resto del estado | metropolitana / resto / NE | Jerarquía municipio -> zona | texto | 0.0 |  |  |
| `suicidios` | Suicidios en la combinación de factores | conteo | EDR | numérico | 0.0 | 1.0 | 9.0 |
| `n_registros_fuente` | Registros de Bronce que sostienen la fila (ver linaje_oro.csv) | conteo | Linaje | numérico | 0.0 | 1.0 | 9.0 |
| `fecha_ingesta_max` | Fecha UTC de la captura más reciente entre los registros que forman la fila | ISO 8601 | manifiesto Bronce | texto | 0.0 |  |  |

## `municipios_colima.csv` (10 filas)

Una fila por municipio (10): población, oferta de consultorios de psicología y tasas de necesidad. Integra EDR + DENUE + Censo 2020.

| Columna | Descripción | Unidad / dominio | Origen | Tipo | Nulos % | Mín | Máx |
|---|---|---|---|---|---|---|---|
| `cve_mun` | Clave INEGI del municipio (3 dígitos) | 001-010 | DENUE / Censo / EDR | texto | 0.0 |  |  |
| `nom_mun` | Nombre del municipio | texto | Censo 2020 | texto | 0.0 |  |  |
| `pobtot` | Población total 2020 | personas | Censo 2020 ITER | numérico | 0.0 | 5623.0 | 191031.0 |
| `suicidios_2018_2023` | Suicidios de residentes del municipio, 6 años | conteo | EDR | numérico | 0.0 | 0.0 | 84.0 |
| `trastornos_mentales_2018_2023` | Defunciones por trastornos mentales de residentes, 6 años | conteo | EDR | numérico | 0.0 | 3.0 | 61.0 |
| `consultorios_psic_privados` | Consultorios de psicología del sector privado (SCIAN 621331) | conteo | DENUE | numérico | 0.0 | 0.0 | 59.0 |
| `consultorios_psic_publicos` | Consultorios de psicología del sector público (SCIAN 621332) | conteo | DENUE | numérico | 0.0 | 0.0 | 3.0 |
| `consultorios_psic` | Total de consultorios de psicología | conteo | DENUE | numérico | 0.0 | 0.0 | 62.0 |
| `consultorios_por_100k` | Consultorios por cada 100 mil habitantes (indicador de OFERTA) | tasa | DENUE / Censo | numérico | 0.0 | 0.0 | 39.48 |
| `tasa_suicidio_anual_100k` | Suicidios por año por cada 100 mil habitantes (indicador de NECESIDAD) | tasa | EDR / Censo | numérico | 0.0 | 0.0 | 11.86 |
| `tasa_trast_mental_anual_100k` | Defunciones por trastorno mental por año por 100 mil hab. | tasa | EDR / Censo | numérico | 0.0 | 2.67 | 8.89 |
| `zona` | Zona Metropolitana Colima-Villa de Álvarez (002, 003, 004, 005, 010) vs resto del estado | metropolitana / resto / NE | Jerarquía municipio -> zona | texto | 0.0 |  |  |
| `consultorios_por_100k_minmax` | Normalización min-max a [0, 1] de `consultorios_por_100k` | 0-1 | Derivado en Oro (src/oro.py) | numérico | 0.0 | 0.0 | 1.0 |
| `consultorios_por_100k_z` | Estandarización z-score (media 0, desviación 1) de `consultorios_por_100k` | adimensional | Derivado en Oro (src/oro.py) | numérico | 0.0 | -0.9566 | 2.562 |
| `tasa_suicidio_anual_100k_minmax` | Normalización min-max a [0, 1] de `tasa_suicidio_anual_100k` | 0-1 | Derivado en Oro (src/oro.py) | numérico | 0.0 | 0.0 | 1.0 |
| `tasa_suicidio_anual_100k_z` | Estandarización z-score (media 0, desviación 1) de `tasa_suicidio_anual_100k` | adimensional | Derivado en Oro (src/oro.py) | numérico | 0.0 | -2.2048 | 1.3456 |
| `tasa_trast_mental_anual_100k_minmax` | Normalización min-max a [0, 1] de `tasa_trast_mental_anual_100k` | 0-1 | Derivado en Oro (src/oro.py) | numérico | 0.0 | 0.0 | 1.0 |
| `tasa_trast_mental_anual_100k_z` | Estandarización z-score (media 0, desviación 1) de `tasa_trast_mental_anual_100k` | adimensional | Derivado en Oro (src/oro.py) | numérico | 0.0 | -1.4963 | 1.8856 |
| `pobtot_minmax` | Normalización min-max a [0, 1] de `pobtot` | 0-1 | Derivado en Oro (src/oro.py) | numérico | 0.0 | 0.0 | 1.0 |
| `pobtot_z` | Estandarización z-score (media 0, desviación 1) de `pobtot` | adimensional | Derivado en Oro (src/oro.py) | numérico | 0.0 | -0.9403 | 1.6419 |
| `oferta_nivel` | Tercil de consultorios_por_100k | baja / media / alta | Discretización por frecuencia | texto | 0.0 |  |  |
| `necesidad_nivel` | Tercil de tasa_suicidio_anual_100k | baja / media / alta | Discretización por frecuencia | texto | 0.0 |  |  |
| `n_registros_fuente` | Registros de Bronce que sostienen la fila (ver linaje_oro.csv) | conteo | Linaje | numérico | 0.0 | 5.0 | 191.0 |
| `fecha_ingesta_max` | Fecha UTC de la captura más reciente entre los registros que forman la fila | ISO 8601 | manifiesto Bronce | texto | 0.0 |  |  |

## `consultorios_psicologia_geo.csv` (117 filas)

Un registro por consultorio de psicología del DENUE (SCIAN 621331/621332) con coordenadas y distancia al centro de Colima (E2 geoespacial).

| Columna | Descripción | Unidad / dominio | Origen | Tipo | Nulos % | Mín | Máx |
|---|---|---|---|---|---|---|---|
| `id_registro` | Identificador de linaje FUENTE:archivo:fila | texto | Generado en Plata | texto | 0.0 |  |  |
| `clee` | Clave Única del Establecimiento del DENUE (identificador público del negocio, no de una persona) | texto | DENUE | texto | 0.0 |  |  |
| `codigo_act` | Código SCIAN de la actividad | 621331 privado / 621332 público | DENUE | texto | 0.0 |  |  |
| `sector` | Sector del consultorio, derivado del código SCIAN | privado / publico | DENUE | texto | 0.0 |  |  |
| `cve_mun` | Clave INEGI del municipio (3 dígitos) | 001-010 | DENUE / Censo / EDR | texto | 0.0 |  |  |
| `cve_mun_geo` | Municipio en el que cae el punto según el polígono del Marco Geoestadístico | 001-010 | Unión espacial (GeoPandas) | texto | 0.0 |  |  |
| `ubicacion_consistente` | True si cve_mun (declarado) = cve_mun_geo (calculado por el punto) | booleano | Validación espacial | booleano | 0.0 |  |  |
| `per_ocu` | Rango de personal ocupado del establecimiento | texto (p. ej. 0 a 5 personas) | DENUE | texto | 0.0 |  |  |
| `fecha_alta` | Mes en que el establecimiento se dio de alta en el DENUE | AAAA-MM | DENUE | texto | 0.0 |  |  |
| `latitud` | Latitud WGS84 | grados | DENUE | numérico | 0.0 | 18.9093 | 19.3868 |
| `longitud` | Longitud WGS84 | grados | DENUE | numérico | 0.0 | -104.3538 | -103.5731 |
| `distancia_centro_m` | Distancia en línea recta al Jardín Libertad (centro de Colima), medida en EPSG:6372 | metros | Cálculo geoespacial | numérico | 0.0 | 320.0 | 67355.0 |
| `archivo_bronce` | Archivo de Bronce del que viene el registro | ruta | Linaje | texto | 0.0 |  |  |
| `fila_bronce` | Número de fila dentro del archivo de Bronce | entero | Linaje | numérico | 0.0 | 15.0 | 1651.0 |
| `fecha_ingesta_utc` | Fecha UTC en que se capturó el registro de Bronce | ISO 8601 | manifiesto Bronce | texto | 0.0 |  |  |
| `n_registros_fuente` | Registros de Bronce que sostienen la fila (ver linaje_oro.csv) | conteo | Linaje | numérico | 0.0 | 1.0 | 1.0 |
| `fecha_ingesta_max` | Fecha UTC de la captura más reciente entre los registros que forman la fila | ISO 8601 | manifiesto Bronce | texto | 0.0 |  |  |

## `competencia_centro_colima.csv` (3 filas)

Consultorios a 500 m, 1 km y 2 km del centro histórico de Colima: la competencia directa de la cliente.

| Columna | Descripción | Unidad / dominio | Origen | Tipo | Nulos % | Mín | Máx |
|---|---|---|---|---|---|---|---|
| `radio_m` | Radio alrededor del centro de Colima | 500 / 1000 / 2000 m | Parámetro | numérico | 0.0 | 500.0 | 2000.0 |
| `consultorios_psic` | Total de consultorios de psicología | conteo | DENUE | numérico | 0.0 | 3.0 | 31.0 |
| `privados` | Consultorios privados dentro del radio | conteo | DENUE | numérico | 0.0 | 3.0 | 30.0 |
| `publicos` | Consultorios públicos dentro del radio | conteo | DENUE | numérico | 0.0 | 0.0 | 1.0 |
| `pct_del_municipio_colima` | % de los consultorios del municipio de Colima que están dentro del radio | % | Cálculo | numérico | 0.0 | 4.8 | 50.0 |
| `n_registros_fuente` | Registros de Bronce que sostienen la fila (ver linaje_oro.csv) | conteo | Linaje | numérico | 0.0 | 3.0 | 31.0 |
| `fecha_ingesta_max` | Fecha UTC de la captura más reciente entre los registros que forman la fila | ISO 8601 | manifiesto Bronce | texto | 0.0 |  |  |

## `pronostico_suicidio_colima.csv` (12 filas)

Pronóstico de 12 meses del modelo ganador con su intervalo del 95 % (lo genera src/pronostico.py).

| Columna | Descripción | Unidad / dominio | Origen | Tipo | Nulos % | Mín | Máx |
|---|---|---|---|---|---|---|---|
| `periodo` | Mes (AAAA-MM) o trimestre (AAAA-Tn) de ocurrencia | texto | EDR: anio_ocur + mes_ocurr | texto | 0.0 |  |  |
| `modelo` | Modelo de pronóstico ganador (menor RMSE en la prueba 2023) | texto | src/pronostico.py | texto | 0.0 |  |  |
| `pronostico` | Valor esperado del mes | suicidios | src/pronostico.py | numérico | 0.0 | 4.54 | 4.54 |
| `limite_inferior_95` | Límite inferior del intervalo de predicción del 95 % (recortado a 0) | suicidios | src/pronostico.py | numérico | 0.0 | 0.0 | 0.0 |
| `limite_superior_95` | Límite superior del intervalo de predicción del 95 % | suicidios | src/pronostico.py | numérico | 0.0 | 9.21 | 9.21 |
| `fuente_entrada` | Tabla Oro usada para entrenar el modelo | ruta | Linaje | texto | 0.0 |  |  |
| `meses_entrenamiento` | Meses usados para ajustar el modelo final | entero | src/pronostico.py | numérico | 0.0 | 72.0 | 72.0 |

## `localidades_colima.csv` (65 filas)

Una fila por localidad con >= 500 habitantes (65): 8 indicadores del Censo 2020 + distancia al psicólogo más cercano, y sus coordenadas en los componentes principales (E3, src/multivariado.py).

| Columna | Descripción | Unidad / dominio | Origen | Tipo | Nulos % | Mín | Máx |
|---|---|---|---|---|---|---|---|
| `id_registro` | Identificador de linaje FUENTE:archivo:fila | texto | Generado en Plata | texto | 0.0 |  |  |
| `archivo_bronce` | Archivo de Bronce del que viene el registro | ruta | Linaje | texto | 0.0 |  |  |
| `fila_bronce` | Número de fila dentro del archivo de Bronce | entero | Linaje | numérico | 0.0 | 6.0 | 1200.0 |
| `cve_mun` | Clave INEGI del municipio (3 dígitos) | 001-010 | DENUE / Censo / EDR | texto | 0.0 |  |  |
| `nom_mun` | Nombre del municipio | texto | Censo 2020 | texto | 0.0 |  |  |
| `cve_loc` | Clave INEGI de la localidad (4 dígitos, única dentro del municipio) | texto | Censo 2020 ITER | numérico | 0.0 | 1.0 | 391.0 |
| `nom_loc` | Nombre de la localidad | texto | Censo 2020 ITER | texto | 0.0 |  |  |
| `pobtot` | Población total 2020 | personas | Censo 2020 ITER | numérico | 0.0 | 500.0 | 159853.0 |
| `pct_sin_afiliacion` | % de la población sin afiliación a servicios de salud | % | Censo: PSINDER / POBTOT | numérico | 0.0 | 0.8711 | 37.6603 |
| `escolaridad_prom` | Grado promedio de escolaridad de 15 años y más | años | Censo: GRAPROES | numérico | 0.0 | 6.47 | 11.61 |
| `pct_60ymas` | % de la población de 60 años y más | % | Censo: P_60YMAS / POBTOT | numérico | 0.0 | 1.3937 | 26.1665 |
| `pct_condicion_mental` | % de la población con algún problema o condición mental | % | Censo: PCLIM_PMEN / POBTOT | numérico | 0.0 | 0.1742 | 6.4833 |
| `pct_viv_internet` | % de viviendas particulares habitadas con internet | % | Censo: VPH_INTER / TVIVPARHAB | numérico | 0.0 | 4.8951 | 75.5977 |
| `pct_desocupacion` | % de la población económicamente activa desocupada | % | Censo: PDESOCUP / PEA | numérico | 0.0 | 0.0 | 3.4483 |
| `pct_hogares_jefa` | % de hogares con persona de referencia mujer | % | Censo: HOGJEF_F / TOTHOG | numérico | 0.0 | 3.871 | 54.6012 |
| `dist_psicologo_km` | Distancia en línea recta al consultorio de psicología más cercano (EPSG:6372) | km | Unión espacial Censo + DENUE | numérico | 0.0 | 0.068 | 23.604 |
| `log_dist_psicologo` | log(1 + dist_psicologo_km); reduce el sesgo para el análisis multivariado | log-km | Derivado | numérico | 0.0 | 0.0658 | 3.2029 |
| `zona` | Zona Metropolitana Colima-Villa de Álvarez (002, 003, 004, 005, 010) vs resto del estado | metropolitana / resto / NE | Jerarquía municipio -> zona | texto | 0.0 |  |  |
| `oferta_nivel` | Tercil de consultorios_por_100k | baja / media / alta | Discretización por frecuencia | texto | 0.0 |  |  |
| `latitud` | Latitud WGS84 | grados | DENUE | numérico | 0.0 | 18.7497 | 19.4103 |
| `longitud` | Longitud WGS84 | grados | DENUE | numérico | 0.0 | -104.5578 | -103.5283 |
| `mahalanobis2` | Distancia de Mahalanobis al cuadrado al centroide de las 8 variables (> 17.5 = perfil atípico al 97.5 %) | adimensional | src/multivariado.py | numérico | 0.0 | 1.307 | 27.949 |
| `cp1` | Puntaje en CP1 'Urbanización y acceso a psicólogos' (alto = más acceso) | z | PCA | numérico | 0.0 | -2.3986 | 4.533 |
| `cp2` | Puntaje en CP2 'Vulnerabilidad del hogar' (alto = más vulnerable) | z | PCA | numérico | 0.0 | -4.5228 | 2.6054 |
| `fecha_ingesta_utc` | Fecha UTC en que se capturó el registro de Bronce | ISO 8601 | manifiesto Bronce | texto | 0.0 |  |  |

## `linaje_oro.csv` (2191 filas)

Tabla puente: cada fila Oro -> cada registro Bronce que la originó (archivo y fila).

| Columna | Descripción | Unidad / dominio | Origen | Tipo | Nulos % | Mín | Máx |
|---|---|---|---|---|---|---|---|
| `tabla_oro` | Tabla Oro a la que pertenece la fila | nombre de tabla | Linaje | texto | 0.0 |  |  |
| `clave_oro` | Llave de la fila en esa tabla (periodo, municipio, id...) | texto | Linaje | texto | 0.0 |  |  |
| `id_registro` | Identificador de linaje FUENTE:archivo:fila | texto | Generado en Plata | texto | 0.0 |  |  |
| `archivo_bronce` | Archivo de Bronce del que viene el registro | ruta | Linaje | texto | 0.0 |  |  |
| `fila_bronce` | Número de fila dentro del archivo de Bronce | entero | Linaje | numérico | 0.0 | 5.0 | 7842.0 |
| `fecha_ingesta_utc` | Fecha UTC en que se capturó el registro de Bronce | ISO 8601 | manifiesto Bronce | texto | 0.0 |  |  |
