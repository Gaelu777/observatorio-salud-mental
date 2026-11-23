# E2 · Evaluación de calidad con ISO/IEC 25010 y 25012

**Fecha de medición:** 2026-11-23 · **Objeto evaluado:** el observatorio en el commit `f85eef5` (capas Bronce/Plata/Oro, workflow y documentación).

**Escala de calificación por característica:**

| Calificación | Criterio |
|---|---|
| **Cumple** | Se alcanza la meta |
| **Parcial** | Hay una medición, pero no alcanza la meta |
| **No cumple** | No existe o la meta queda muy lejos |

Cada calificación sale de la métrica medida, no de una opinión. Donde no hay medición se dice explícitamente.

---

## 1. ISO/IEC 25012 — calidad de los datos (medida sobre la capa Oro)

### Características inherentes

| Característica | Métrica | Cómo se midió | Resultado | Meta | Calificación |
|---|---|---|---|---|---|
| **Exactitud** | % de registros Bronce que pasan la Puerta de Calidad (Pandera) | `data/plata/resumen_plata.json` | 37 136/37 136 defunciones, 1 649/1 649 DENUE, 10/10 municipios del Censo → **100 %**, 0 en cuarentena | ≥ 99 % | Cumple |
| **Exactitud** (valores imputados) | % de suicidios con mes imputado | `serie_mensual_colima.suicidio_mes_imputado` | **1 de 327 (0.3 %)**, marcado con su bandera | ≤ 5 % y marcado | Cumple |
| **Completitud** | % de celdas no nulas en las tablas Oro | conteo de `isna()` en las 7 tablas de `data/oro/` | **100 %** en las 7 tablas | ≥ 95 % (umbral del Sello TDL) | Cumple |
| **Completitud** (cobertura temporal) | Periodos mensuales sin hueco | `serie_mensual_colima` | **72/72** meses (ene-2018 a dic-2023) | ≥ 36 | Cumple |
| **Consistencia** | Mismo total de suicidios entre tablas Oro | suma en serie mensual, factores y municipios | 327 = 327; municipios = 326. La diferencia de 1 es un caso con municipio de residencia no especificado, que se excluye de las tasas municipales | Diferencias explicadas | Cumple |
| **Consistencia** (geográfica) | % de consultorios cuyo municipio del DENUE coincide con el polígono del Marco Geoestadístico | `consultorios_psicologia_geo.ubicacion_consistente` | **117/117 (100 %)** | ≥ 98 % | Cumple |
| **Credibilidad** | % de registros Oro de fuentes oficiales y con huella SHA-256 | `data/bronce/manifiesto.csv` | **100 %**: las 4 fuentes son del INEGI, con su hash | 100 % | Cumple |
| **Actualidad** | Desfase entre el último dato disponible y la fecha de captura | defunciones: último mes dic-2023, captura nov-2026; DENUE: edición vigente | defunciones **≈ 35 meses** (el INEGI publica con rezago de unos 10 meses; 2024 aún no estaba en la ruta usada); DENUE **0 días** | ≤ 12 meses | **Parcial**: defunciones 2024 pendiente |

### Características dependientes del sistema

| Característica | Métrica | Resultado | Meta | Calificación |
|---|---|---|---|---|
| **Trazabilidad** | % de filas Oro con linaje verificado hasta la fila exacta de Bronce | **363/363 filas** en 6 tablas; 652/652 registros fuente re-leídos con su valor de control idéntico (`docs/E2/verificacion_linaje.md`) | 100 % | Cumple |
| **Confidencialidad** | Columnas con datos personales en Bronce, Plata u Oro | **0**: nombre, razón social, teléfono, correo y web del DENUE se eliminan antes de escribir a disco (`src/extraer_denue.py`) | 0 | Cumple |
| **Conformidad** | Formatos abiertos y estándares usados | CSV UTF-8, GeoJSON, CIE-10, claves geoestadísticas del INEGI, SCIAN | 100 % | Cumple |
| **Portabilidad** | Capas legibles sin software propietario | **100 %** (CSV/GeoJSON) | 100 % | Cumple |
| **Recuperabilidad** | La capa Bronce tiene respaldo | Bronce versionado en git y en GitHub (2 copias) más el manifiesto con la URL para re-descargar | ≥ 2 copias | Cumple. Falta *probar* la restauración (E1 Calidad) |
| **Disponibilidad** | % de días con captura exitosa | La bitácora (`data/bitacora/capturas.csv`) empezó el 2026-11-23. Todavía **no hay datos suficientes** | ≥ 95 % | **Sin medición aún** |
| **Comprensibilidad** | ¿Existe un diccionario de datos de la capa Oro? | **No existe** | Sí, completo | **No cumple** |
| **Eficiencia** | Tiempo del paso Bronce → serie mensual | 2.34 s; se puede bajar a 0.54 s (−77 %) según el experimento factorial | — | Cumple. Mejora identificada |
| **Precisión** | Granularidad adecuada a la pregunta | conteos enteros por mes; tasas por 100 mil con 2 decimales; coordenadas con 6 decimales | adecuada | Cumple |
| **Accesibilidad** | Datos consultables sin instalar nada | solo vía repositorio; **no hay tablero público** | tablero en línea | **No cumple** |

**Resumen 25012:**
- **12 cumplen**, 1 parcial (actualidad), 2 no cumplen (comprensibilidad y accesibilidad) y 1 sin medición (disponibilidad).
- Lo que falta es el **diccionario de Oro** y el **tablero**. Los dos son entregables pendientes.

---

## 2. ISO/IEC 25010 — calidad del producto (el observatorio como software)

| Característica | Métrica | Resultado medido | Meta | Calificación |
|---|---|---|---|---|
| **Adecuación funcional** | % de los 5 componentes obligatorios del proyecto (sección 3 del documento del curso) que existen | Captura multifuente ✔, almacén por capas ✔ (falta el diccionario), laboratorio estadístico ◐ (experimento sí, pronóstico no), sistema de calidad ◐ (PSP, pruebas y Puerta sí; SQA y CI no), tablero ✘ → **2 completos y 2 parciales de 5 (60 %)** | 100 % | **Parcial** |
| **Eficiencia de desempeño** | Tiempo de procesamiento y tasa de error por configuración | Experimento factorial 2³ ([`experimento.md`](experimento.md)): configuración actual 2.34 s, ganadora confirmada 0.54 s, **0 % de error**. Se detectó que el motor pyarrow tiene **100 % de error** | Mejora medida con error 0 | Cumple |
| **Compatibilidad** | Formatos de intercambio estándar | CSV, GeoJSON (EPSG:4326), Shapefile del INEGI. Se abren en QGIS, Excel y pandas | 100 % estándar | Cumple |
| **Capacidad de interacción** (usabilidad) | ¿Puede la clienta consultar los hallazgos sin ser ingeniera? | Solo hay mapas PNG y Markdown en el repo; **no hay tablero** | Tablero en línea | **No cumple** |
| **Fiabilidad** | Tasa de éxito de la captura programada; MTBF/MTTR | Corridas del pipeline con éxito en Actions hasta hoy: la corrida automática del 2026-11-23 (`3b866b2`) terminó bien. La bitácora diaria empezó hoy. **MTBF y MTTR no se pueden calcular todavía**; se necesitan 7 días | ≥ 95 % | **Sin medición suficiente** |
| **Seguridad** | Secretos en el repo; datos personales | 0 tokens: todas las fuentes son abiertas y sin llave. 0 columnas personales. **gitleaks y pip-audit aún no se han corrido** | 0 hallazgos con herramienta | **Parcial** |
| **Mantenibilidad** | Modularidad y pruebas | 1 módulo por fuente (`src/extraer_*.py`), utilidades compartidas (`src/comun.py`), 1 archivo de pruebas (`tests/test_puerta_calidad.py`). Cobertura **no medida** | Cobertura ≥ 60 % | **Parcial** |
| **Portabilidad** | Ambientes donde corre igual | Corre en Ubuntu (GitHub Actions) y en Windows 11 (local), con `requirements.txt` de versiones fijas | ≥ 2 sistemas | Cumple |

**Resumen 25010:**
- **3 cumplen** (eficiencia, compatibilidad y portabilidad), 3 parciales, 1 no cumple (interacción) y 1 sin medición suficiente (fiabilidad).
- **Acciones derivadas** (entran al plan para E3):
  1. Tablero Streamlit con el mapa y el pronóstico.
  2. gitleaks y pip-audit en CI.
  3. Medir la cobertura con pytest-cov.
  4. MTBF y MTTR con 7 días de bitácora.

---

## 3. Antecedentes normativos

| Norma | Qué es | Estado | Relación con las demás |
|---|---|---|---|
| **ISO/IEC 9126** (1991, partes 2001–2004) | Modelo de calidad de *producto de software*: 6 características (funcionalidad, fiabilidad, usabilidad, eficiencia, mantenibilidad, portabilidad) | **Retirada**; reemplazada por la ISO/IEC 25010 | Es la base conceptual de SQuaRE |
| **ISO/IEC 25000 (SQuaRE)** | Familia *Systems and software Quality Requirements and Evaluation*. Unifica la 9126 (modelo) y la 14598 (proceso de evaluación) | Vigente | 2500n gestión, 2501n **modelos**, 2502n medición, 2503n requisitos, 2504n evaluación |
| **ISO/IEC 25010** (2011, rev. 2023) | Modelo de calidad del *producto*. **2011:** 8 características; frente a la 9126 agrega **seguridad** y **compatibilidad** como características propias. **2023:** 9 características; usabilidad pasa a *capacidad de interacción*, portabilidad a *flexibilidad*, y se agrega *protección (safety)*. Aquí se evalúan las 8 que lista el documento del curso | Vigente | Sucesora directa de la 9126-1 |
| **ISO/IEC 25012** (2008) | Modelo de calidad de *datos*: 15 características, divididas en inherentes y dependientes del sistema | Vigente | La 9126 no tenía equivalente. Complementa a la 25010: la 25010 evalúa el software, la 25012 los datos que maneja |
| **ISO 9001** (2015) | Sistema de gestión de la calidad de *cualquier organización*: enfoque a procesos, ciclo PHVA, pensamiento basado en riesgos y mejora continua | Vigente | **No evalúa productos**: evalúa cómo trabaja la organización. SQuaRE dice *qué* medir del producto; la 9001 asegura que exista un *proceso* para lograrlo de forma repetible |

**En nuestro observatorio:**
- La **9001** se refleja en el proceso. El pipeline es un proceso con entradas, controles y salidas: Puerta de Calidad, cuarentena y bitácora. Los registros PSP y las acciones correctivas son el ciclo PHVA.
- La **25010** evalúa el observatorio como software.
- La **25012** evalúa la capa Oro que se le entrega a la clienta.
