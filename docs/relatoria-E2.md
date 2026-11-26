# Relatoría E2 · Observatorio de Salud Mental — Colima

**Equipo:** Gael Alexandro Cortez Sarmienta · Luis Alejandro Mendoza Peñaloza · **Periodo:** 17 al 23 de noviembre de 2026

## 1. Qué nos propusimos

- Integrar una fuente geoespacial al pipeline, con 100 % de las filas de Oro rastreables hasta Bronce.
- Declarar la ética y legalidad de cada fuente.
- Correr un experimento factorial 2³ con réplicas que reduzca el tiempo del pipeline **sin introducir errores**.
- Evaluar el observatorio con ISO/IEC 25010 y 25012 usando métricas medidas.

## 2. Qué hicimos

| Fecha | Actividad | Responsable | Evidencia |
|---|---|---|---|
| 2026-11-23 | Extractor del Marco Geoestadístico 2020 (solo la capa municipal, 300 KB de un zip de 29 MB) | Gael | `src/extraer_marcogeo.py` |
| 2026-11-23 | Análisis con GeoPandas: reproyección a EPSG:6372, punto en polígono, competencia por radio y 2 mapas | Gael | `src/geoespacial.py`, `docs/E2/*.png` |
| 2026-11-23 | Linaje completo y verificador automático que re-lee Bronce | Gael | `src/verificar_linaje.py`, `docs/E2/verificacion_linaje.md` |
| 2026-11-23 | Declaración de ética y legalidad | Gael | `docs/etica-datos.md` |
| 2026-11-23 | Captura diaria del DENUE y bitácora de ejecuciones (una fila por corrida, exitosa o fallida) | Gael | `.github/workflows/extraccion-bronce.yml`, `data/bitacora/capturas.csv` |
| 2026-11-23 | Experimento factorial 2³ (24 corridas), diseño 2 × 3 (18 corridas), matrices 2⁴ y 2⁴⁻¹, y confirmación (5 corridas) | Gael | `src/experimento_factorial.py`, `docs/E2/experimento.md` |
| 2026-11-23 | Evaluación ISO/IEC 25010 y 25012 | Gael | `docs/E2/evaluacion-iso.md` |
| Desde 2026-11-18; aprox. 3 días (fin no recordado) | Revisó los criterios de la rúbrica y diseñó qué datos serían necesarios para el observatorio | Luis | Actividad recordada; duración aproximada no disponible. Registro en `calidad/tiempo-luis-mendoza.csv` |
| 2026-11-20 | Inició trabajo de código del proyecto en ratos libres | Luis y Gael | Según recuerdo de Luis; el repositorio se creó el 2026-11-23. No se atribuyen archivos ni commits concretos a Luis. |

Horas por actividad: `calidad/tiempo-gael-cortez.csv` y `calidad/tiempo-luis-mendoza.csv`; los campos no recordados quedan vacíos.

## 3. Qué decidimos y por qué

1. **Fuente geoespacial en vez de redes sociales o una API con OAuth.**
   - El DENUE responde directamente la pregunta de la clienta: dónde está su competencia.
   - No toca datos de personas.
   - Se descartaron YouTube y Reddit: las menciones de "ansiedad" no se pueden ligar a Colima sin geolocalizar usuarios, y eso es un riesgo de privacidad.
2. **Ruta ingeniería para el experimento, en vez de la ruta negocio.**
   - La ruta negocio requería que la clienta corriera una campaña con un acuerdo cerrado en E1, y no lo teníamos.
   - Se experimentó sobre nuestro propio pipeline contra la copia local de Bronce, sin peticiones al INEGI.
3. **La combinación ganadora se elige solo entre configuraciones con 0 % de error.**
   - La más rápida (motor pyarrow, 0.24 s) producía una serie vacía.
   - Se eligió motor `c` + solo las columnas necesarias + Parquet: 0.54 s confirmados, −77 % frente a la configuración actual.
4. **EPSG:6372 para distancias.** Es la proyección oficial del INEGI, en metros. Medir en grados distorsiona las distancias.
5. **El centro se mide desde el Jardín Libertad**, un punto público, y no desde el consultorio de la clienta, para no exponer su ubicación.

## 4. Qué salió mal y cómo lo corregimos

| Defecto | Qué pasó | Corrección |
|---|---|---|
| **D11** (datos) | El motor `pyarrow` de pandas ignora `dtype=str` y convierte `"06"` en `"6"`. La serie salía vacía **sin ningún error**. Lo detectó la respuesta *error* del experimento: 35 corridas con error | pyarrow se descartó como nivel válido y la ganadora se elige con error = 0. También hubo un falso arranque: el primer análisis eligió pyarrow por ser el más rápido. Se corrigió antes de publicar |
| **D9** (verificación) | El verificador de linaje lanzaba una excepción en vez de reportar cuando una fila apuntaba fuera del archivo | Se probó con linaje corrompido a propósito; ahora reporta y falla de forma controlada |
| **D10** (función) | Etiquetas encimadas en los mapas | Líneas guía y un recuadro con los conteos por radio |
| — | La confirmación salió 20 % más lenta que lo predicho (0.54 s contra 0.45 s) | Se reporta tal cual en `experimento.md`. La causa probable es el estado de la caché al final de 42 corridas. La mejora frente a la configuración actual se mantiene |
| — | La captura era mensual, y el documento del curso pide diaria con bitácora desde E0 | Se cambió hoy. La disponibilidad de 14 días para el Sello TDL ya no se alcanza antes del Demo Day |

## 5. Qué aprendimos

### Ingeniería de Datos
Un linaje solo sirve si se verifica automáticamente. El verificador re-lee las 652 filas fuente en Bronce y compara un valor de control. Probarlo con datos rotos a propósito encontró el defecto D9, que con datos buenos no aparecía.

### Análisis Estadístico
Medir solo el tiempo habría recomendado una configuración que borra los datos; la segunda respuesta (error) cambió la conclusión. También vimos que la interacción importa: el formato del intermedio ahorra 1.0 s cuando se leen todas las columnas y solo 0.1 s con las 5 necesarias (F = 271.8, p < 0.001). Sin el diseño de dos factores habríamos sobrestimado el efecto del formato.

### Calidad en los Sistemas de Información
- Calificar con métricas nos obligó a admitir lo que falta. En la 25012, completitud, trazabilidad y confidencialidad están al 100 %, pero comprensibilidad (no hay diccionario de Oro) y accesibilidad (no hay tablero) no cumplen.
- En la 25010, la fiabilidad todavía no se puede medir: la bitácora empezó hoy.

## 6. Distribución del trabajo y evidencias

| Integrante | Actividades |
|---|---|
| Luis Alejandro Mendoza Peñaloza | Desde el 18-nov, revisó criterios de la rúbrica y diseñó los datos necesarios para el observatorio (aprox. 3 días; fin no recordado). El 20-nov inició trabajo de código en ratos libres, según su recuerdo; no se atribuyen archivos ni commits concretos a Luis. El tiempo no recordado queda sin cuantificar en `calidad/tiempo-luis-mendoza.csv`. |

- Commits: `88037d9` (geoespacial, linaje y ética), `6d30205` (captura diaria y bitácora), `f85eef5` (experimento factorial), `16adb5c` (evaluación ISO).
- Mapas: `docs/E2/mapa_oferta_necesidad.png`, `docs/E2/mapa_centro_colima.png`.
- Experimento: `docs/E2/experimento/` (corridas, tablas ANOVA, gráficas de interacción y de residuos, `resumen.json`).
- Linaje: `docs/E2/verificacion_linaje.md`.

## Uso de IA generativa

Se usó **Claude Code** (asistente de código de Anthropic) para:
- Escribir y depurar los scripts de `src/`.
- Proponer el diseño del experimento.
- Redactar los borradores de la documentación.

Cada resultado numérico sale de ejecutar los scripts del repositorio. Los integrantes revisaron el código y las conclusiones, y deben poder explicarlos en la defensa.
