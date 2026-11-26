# Relatoría de etapa — E1

**Equipo:** Gael Alexandro Cortez Sarmienta · Luis Alejandro Mendoza Peñaloza
**Periodo:** noviembre 2026

## 1. Objetivo de la etapa

Automatizar el paso de los datos crudos (Bronce) a datos limpios y validados (Plata) y a tablas listas para análisis (Oro), con una Puerta de Calidad que nunca descarte registros en silencio.

## 2. Qué se hizo

1. **Se agregó una tercera fuente** (Censo 2020, ITER Colima) porque las tasas por 100 mil habitantes necesitan población. CONAPO no tenía descargas que funcionaran, y el Censo es oficial, pequeño y está bajo la misma ruta de INEGI permitida en robots.txt.
2. **Capa Plata** (`src/plata.py`): limpieza de ruido de texto, decodificación de los códigos INEGI, tipado y validación con Pandera. Los inválidos van a cuarentena.
3. **Capa Oro** (`src/oro.py`): diagnóstico e imputación de faltantes, atípicos, normalización, discretización, jerarquías, reducción e integración municipal. Genera el reporte con cifras reales.
4. **Prueba automática** de la Puerta de Calidad con registros inválidos inyectados.
5. **Workflow** extendido para correr todo el flujo cada mes.

## 3. Problemas encontrados y cómo se resolvieron

| Problema | Cómo se detectó | Solución |
|---|---|---|
| Los archivos 2018–2021 traen tabuladores pegados a los valores (`"06\t"`) | El filtro por Colima devolvía 0 registros | Bronce los conserva tal cual; Plata los limpia y cuenta cuántas celdas corrigió |
| La misma variable cambia de nombre (`presunto` → `tipo_defun`) y el número de columnas pasa de 59 a 74 | Comparación de esquemas entre años | Renombrar y seleccionar solo las variables comunes |
| El Censo mezcla filas de estado, municipio y localidad | Inspección del archivo | Tomar solo los totales municipales oficiales (`LOC=0000`) |
| Con datos reales la cuarentena queda vacía, lo que no demuestra que la puerta funcione | Revisión del resultado | Prueba con registros defectuosos inyectados |
| Una edición automática rompió la sintaxis de 3 archivos | `py_compile` | Corrección y verificación de compilación (defecto D7 del PSP) |

## 4. Decisiones relevantes (y por qué)

- **Hot-deck condicional en vez de moda para el mes faltante:** la prueba chi-cuadrada mostró que el mes falta más en muertes violentas (MAR). Imputar dentro del mismo grupo de causa respeta esa relación; la moda habría inflado un solo mes.
- **IQR y Z robusto en vez de Z clásico:** con conteos de 0 a 13 por mes, la media y la desviación estándar se distorsionan con el propio atípico.
- **No borrar atípicos:** son muertes reales. Se marcan y se crea una versión winsorizada para los modelos.
- **Terciles en vez de intervalos de igual ancho:** la oferta está tan concentrada en Colima capital que con intervalos iguales casi todos los municipios quedarían en la misma categoría.
- **Grupos de edad compatibles con el Censo** (0–14, 15–24, 25–59, 60+), no los propuestos en E0, porque sin denominador por edad no se pueden calcular tasas.

## 5. Primeros hallazgos (para la cliente)

- La serie mensual de suicidios en Colima va de 0 a 13 casos por mes (mediana 4). Hubo picos en dic-2020, ago-2021, feb-2022 y sep-2022.
- El municipio de Colima concentra 62 de los 117 consultorios de psicología del estado (39.5 por 100 mil habitantes). Armería e Ixtlahuacán no tienen ninguno registrado y tienen las tasas de suicidio más altas: zonas con **alta necesidad y nula oferta**. Ixtlahuacán tiene solo 5,623 habitantes, así que su tasa es inestable y hay que confirmarla con tasas suavizadas.

## 6. Distribución del trabajo

| Integrante | Actividades |
|---|---|
| Gael Alexandro Cortez Sarmienta | _completar_ |
| Luis Alejandro Mendoza Peñaloza | El 12-nov participó en la lluvia de ideas del proyecto y propuso inicialmente un mapa agrícola; el equipo después eligió el observatorio del sector de servicios psicológicos. Investigó fuentes oficiales y propuso INEGI como fuente. Fue trabajo de planeación e investigación; no se le atribuye código subido al repositorio en E1. El tiempo es estimado y los datos no recordados quedan sin cuantificar en `calidad/tiempo-luis-mendoza.csv`. |

## 7. Aprendizajes y siguiente etapa

- Validar el formato de cada año por separado: los datos oficiales también cambian de esquema.
- Una puerta de calidad solo está probada si se le dan casos que deben fallar.
- **E2:** visualización geoespacial de la oferta con GeoPandas, declaración de ética y verificación completa del linaje.
