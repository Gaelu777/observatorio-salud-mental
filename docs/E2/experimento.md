# E2 · Experimento factorial (ruta ingeniería)

**Script:** [`src/experimento_factorial.py`](../../src/experimento_factorial.py) · **Resultados crudos:** [`docs/E2/experimento/`](experimento/) · **Fecha de corrida:** 2026-11-23

## 1. Pregunta y diseño

**¿Qué configuración del paso Bronce → serie mensual procesa más rápido *sin introducir errores*?**

La tarea medida es la misma en todas las corridas:
1. Leer los 6 CSV de defunciones de la capa Bronce (2018–2023, unas 37 mil filas).
2. Limpiar espacios y quedarse con los residentes de Colima.
3. Escribir el intermedio a disco y volver a leerlo.
4. Contar los suicidios (CIE-10 X60–X84) por mes.

Todo corre contra la **copia local** de Bronce. No se hace ninguna petición al INEGI.

| Factor | Nivel − | Nivel + |
|---|---|---|
| A · motor de lectura de pandas | `c` (el que usa hoy el pipeline) | `pyarrow` |
| B · columnas leídas | todas (59) | solo las 5 necesarias (`usecols`) |
| C · formato del intermedio | CSV | Parquet |

**Respuestas:**
- **Tiempo** en segundos, medido con `time.perf_counter`.
- **Error**: vale 1 si la serie resultante no es idéntica a la serie de referencia. La referencia es la configuración actual (A−, B−, C−).

**Principios del diseño:**
- **Réplicas:** 3 por tratamiento, 2³ × 3 = 24 corridas.
- **Aleatorización:** el orden de los tratamientos se baraja dentro de cada réplica con `numpy.random.default_rng(20261123)`. La semilla está fija para que el orden sea reproducible.
- **Bloqueo:** cada réplica es un bloque. Controla el calentamiento de la caché del disco y del sistema operativo entre pasadas, una fuente de variación que no controlamos. Además se hizo una corrida de calentamiento que no se midió.

## 2. Hallazgo principal: la configuración más rápida corrompe los datos

| A | B | C | Tiempo medio (s) | DE | Tasa de error |
|---|---|---|---|---|---|
| pyarrow | necesarias | CSV | 0.244 | 0.031 | **100 %** |
| pyarrow | necesarias | Parquet | 0.276 | 0.045 | **100 %** |
| **c** | **necesarias** | **Parquet** | **0.451** | 0.019 | **0 %** |
| c | necesarias | CSV | 0.493 | 0.026 | 0 % |
| pyarrow | todas | CSV | 1.276 | 0.048 | 100 % |
| pyarrow | todas | Parquet | 1.428 | 0.210 | 100 % |
| c | todas | Parquet | 1.822 | 0.226 | 0 % |
| c | todas | CSV (actual) | 2.336 | 0.391 | 0 % |

**Todas las corridas con `pyarrow` produjeron una serie vacía, y lo hicieron sin lanzar ningún error.** La causa: el motor `pyarrow` ignora `dtype=str`. Lee los códigos como enteros y después los convierte a texto, así que `"06"` se vuelve `"6"`. El filtro `ent_resid == "06"` deja de encontrar registros. Se registró como defecto en `calidad/defectos-gael-cortez.csv`.

Si solo se hubiera medido el tiempo, el experimento habría recomendado una configuración que borra todos los datos en silencio. **Por eso la combinación ganadora se elige entre las configuraciones con 0 % de error.** El motor `pyarrow` queda descartado como nivel válido.

## 3. ANOVA del 2³ (efectos fijos, con bloque)

Modelo: `tiempo ~ bloque + A * B * C`. Tabla completa en [`experimento/anova_2k3.csv`](experimento/anova_2k3.csv).

| Fuente | F | p |
|---|---|---|
| Bloque | 3.63 | 0.054 |
| A · motor | 55.19 | < 0.001 |
| **B · columnas** | **455.95** | **< 0.001** |
| C · formato | 2.15 | 0.165 |
| A × B | 16.57 | 0.001 |
| A × C | 8.51 | 0.011 |
| B × C | 1.94 | 0.185 |
| A × B × C | 5.48 | 0.035 |

**Efectos principales**, calculados como media(+) − media(−):
- B, leer solo las columnas necesarias: **−1.35 s**. Es el factor dominante.
- A, motor pyarrow: −0.47 s. No sirve porque corrompe los datos.
- C, Parquet: −0.09 s. No es significativo.

**Interacción A × B** ([gráfica](experimento/interaccion_AB.png)): la ventaja de pyarrow es mucho mayor cuando se leen todas las columnas. Con solo 5 columnas casi no queda nada que acelerar.

**Supuestos** ([residuos](experimento/residuos_2k3.png)):
- Normalidad, Shapiro-Wilk: W = 0.933, p = 0.115. No se rechaza.
- Varianzas iguales, Levene: p = 0.674. No se rechaza.
- Como el tiempo suele tener residuos sesgados, también se ajustó el modelo sobre **log(tiempo)** ([tabla](experimento/anova_2k3_log.csv)). Las conclusiones no cambian: A y B son significativos, C no (p = 0.50). La interacción triple deja de ser significativa (p = 0.36), así que se interpreta como un efecto de escala y no como algo estructural.

## 4. Diseño de dos factores con tres niveles (ANOVA de dos vías con interacción)

- Factores: B (todas / necesarias) × **formato del intermedio (CSV / Parquet / Feather)**.
- Motor fijo en `c`, el único nivel válido.
- 3 réplicas con bloque: 18 corridas.

| B \ formato | CSV | Parquet | Feather |
|---|---|---|---|
| todas | 2.801 | 2.108 | 1.799 |
| necesarias | 0.615 | 0.545 | 0.514 |

| Fuente | F | p |
|---|---|---|
| B · columnas | 10 763.6 | < 0.001 |
| Formato | 407.0 | < 0.001 |
| **B × formato** | **271.8** | **< 0.001** |

Supuestos: Shapiro p = 0.478, Levene p = 0.609. Ambos se cumplen.

**Interpretación de la interacción** ([gráfica](experimento/interaccion_formato.png)): cuando se leen todas las columnas, Feather ahorra 1.0 s frente a CSV. Con solo las 5 necesarias, el ahorro baja a 0.1 s. El formato importa en proporción al volumen que se escribe. Por eso no se puede hablar del "efecto del formato" sin decir cuántas columnas se procesan, y por eso la interacción no se puede ignorar.

## 5. Diseño completo vs. fraccionado (2⁴ y 2⁴⁻¹)

Si se agregara un cuarto factor **D**, por ejemplo tipar las columnas en la lectura contra hacerlo después:

- **2⁴ completo:** 16 tratamientos, en [`matriz_2k4_completa.csv`](experimento/matriz_2k4_completa.csv).
- **2⁴⁻¹ fraccionado:** 8 tratamientos, con generador **D = ABC** y relación de definición **I = ABCD**. Es un diseño de **resolución IV**. Está en [`matriz_2k4-1_fraccionada.csv`](experimento/matriz_2k4-1_fraccionada.csv).

| Corrida | A | B | C | D = ABC |
|---|---|---|---|---|
| 1 | − | − | − | − |
| 2 | + | − | − | + |
| 3 | − | + | − | + |
| 4 | + | + | − | − |
| 5 | − | − | + | + |
| 6 | + | − | + | − |
| 7 | − | + | + | − |
| 8 | + | + | + | + |

**Alias**, que son los efectos que no se pueden separar:

| Efecto | Confundido con |
|---|---|
| A | BCD |
| B | ACD |
| C | ABD |
| D | ABC |
| AB | CD |
| AC | BD |
| AD | BC |

- **Ahorro:** de 16 a 8 tratamientos (50 %). Con 3 réplicas son 48 contra 24 corridas.
- **Costo:** los efectos principales solo se confunden con interacciones triples, que suelen ser despreciables. Pero las interacciones dobles quedan confundidas entre sí, de dos en dos.
- En este experimento A × B resultó significativa. En un 2⁴⁻¹ no se podría distinguir de C × D. Por eso, para 3 factores conviene el diseño completo: solo son 8 tratamientos.

## 6. Corrida de confirmación

**Combinación ganadora entre las válidas:** motor `c` + solo columnas necesarias + Parquet.

| | Tiempo medio (s) |
|---|---|
| Configuración actual (c, todas, CSV) | 2.336 |
| Predicho para la ganadora (media del 2³) | 0.451 |
| **Confirmación (5 corridas nuevas)** | **0.543 ± 0.012** |
| **Mejora frente a la configuración actual** | **−76.8 %** |

- La confirmación salió **20 % más lenta que lo predicho**. La explicación más probable es que corrió al final, después de 42 corridas, con la caché en otro estado. Esto es la variación de máquina y momento que el bloqueo intenta controlar.
- Aun así, la mejora frente a la configuración actual se confirma con claridad, y la confirmación tuvo **0 errores**.
- Hay un matiz: en el 2³, Parquet contra CSV no fue significativo (diferencia de 0.04 s). La decisión robusta es **leer solo las columnas necesarias**. El formato es secundario.

## 7. Qué se hace con el resultado

- **Recomendación para el pipeline (optimización de E3):** usar `usecols` en `src/plata.py` y mantener el motor `c`.
- **Evidencia para ISO/IEC 25010:** este experimento es la evidencia de *eficiencia de desempeño*.
- **Reproducibilidad:** el orden de las corridas y las tablas se reproducen con `python src/experimento_factorial.py`. Los tiempos absolutos dependen de la máquina; las conclusiones (qué factor domina, que pyarrow corrompe) no.
- **Máquina:** laptop Windows 11, Python 3.13.3, pandas 2.2.3.
