# Auditoría interna — ISO/IEC 25010 e ISO/IEC 25012

**Fecha:** 2026-11-26
**Objeto:** observatorio en `main` (`2e1a6b2`), con datos actualizados en `160bf78`.
**Alcance:** calidad del producto (ISO/IEC 25010) y de los datos (ISO/IEC 25012). Esta revisión documental y de artefactos no constituye una certificación.

## Método y escala

Se inspeccionaron el código, los archivos de datos, la bitácora, la documentación y los controles de CI. Para las métricas se usaron los artefactos versionados y los criterios documentados en `docs/E2/evaluacion-iso.md` y `docs/requerimientos.md`. La CI de `main` en `2e1a6b2` concluyó con éxito (GitHub Actions, ejecución `45771142956`); no se volvió a ejecutar pytest localmente.

| Estado | Interpretación |
|---|---|
| **Cumple** | La evidencia inspeccionada alcanza el criterio medible. |
| **Parcial** | Hay controles, pero la evidencia no permite acreditar el criterio completo. |
| **No cumple** | La evidencia confirma una brecha frente al criterio. |
| **Sin medición** | No existe información suficiente para calcular el resultado. |

Las severidades (crítico, mayor o menor) se asignan con la regla de severidad y el ejemplo de defecto mayor de `docs/plan-sqa.md` §6. No se encontró evidencia para clasificar un hallazgo como crítico.

## 1. ISO/IEC 25012 — calidad de los datos Oro

| Característica | Métrica y evidencia | Resultado frente al criterio | Estado |
|---|---|---|---|
| Exactitud | `data/plata/resumen_plata.json`: registros DENUE y defunciones pasan Pandera; 0 en cuarentena. | Hay controles de dominio y esquema; no se hizo comparación independiente con una fuente de verdad registro a registro. | Parcial |
| Completitud | `data/oro/DICCIONARIO.md`; `data/oro/diccionario_oro.csv`. | El diccionario registra 100 % de celdas no nulas en 128 columnas, por encima de la meta ≥95 %. | Cumple |
| Consistencia | `docs/E2/verificacion_linaje.md` y paso `src/verificar_linaje.py` en el workflow. | El reporte de linaje marca 652/652 registros fuente verificados; la corrida completa del 26-nov terminó con éxito. | Cumple |
| Credibilidad | `data/bronce/manifiesto.csv`; hash SHA-256 en `src/comun.py`. | Las fuentes se identifican como oficiales del INEGI y se conserva la huella de cada descarga. | Cumple |
| Actualidad | `data/oro/serie_mensual_colima.csv`, `docs/E2/evaluacion-iso.md` y `docs/E3/datasheet.md`. | La serie de defunciones llega a dic-2023; a nov-2026 son aproximadamente 35 meses de desfase, frente al criterio ≤12 meses documentado en E2. | **No cumple (A-01)** |
| Trazabilidad | `data/oro/linaje_oro.csv`, `docs/E2/verificacion_linaje.md` y `src/verificar_linaje.py`. | El linaje registra archivo y fila de Bronce; el verificador comprueba las rutas, filas y valores de control. | Cumple |
| Confidencialidad | `src/extraer_denue.py`, `data/oro/DICCIONARIO.md` y `docs/E3/datasheet.md`. | Se eliminan nombres, razón social, teléfono, correo y web antes de guardar DENUE; Oro contiene agregados y datos de establecimientos, no registros de pacientes. La ficha advierte que algunos conteos agregados son pequeños. | Cumple con riesgo residual documentado |
| Conformidad | `data/oro/LICENCIA.md`, `docs/E3/datasheet.md` y formatos CSV/GeoJSON. | La licencia y las fuentes están documentadas; los formatos son abiertos. | Cumple |
| Comprensibilidad | `data/oro/DICCIONARIO.md` y `docs/E3/datasheet.md`. | Hay definiciones, tipos, unidades y limitaciones; la fecha de captura del DENUE no coincide con los datos actuales (A-04). | Parcial |
| Disponibilidad | `data/bitacora/capturas.csv` y RNF-01 en `docs/requerimientos.md`. | Hay 4 corridas entre el 24 y 26-nov, 2 fallidas; el historial no cubre los 14 días requeridos para calcular la disponibilidad. | **Sin medición suficiente (A-02)** |
| Recuperabilidad | `data/bronce/manifiesto.csv`, historial Git y `docs/E2/evaluacion-iso.md`. | Bronce está versionado y tiene URL/hash para re-descarga; el informe E2 deja pendiente probar una restauración. | Parcial |
| Precisión | `data/oro/DICCIONARIO.md`; granularidades de las tablas Oro. | Conteos, tasas y coordenadas tienen unidades y precisión descritas; no se contrastó cada coordenada con una fuente independiente. | Parcial |
| Accesibilidad | Archivos Oro en el repositorio y `README.md`. | Los archivos se pueden consultar desde el repositorio; la consulta del tablero para la cliente sigue pendiente de publicación (A-03). | Parcial |

## 2. ISO/IEC 25010 — calidad del producto

| Característica | Métrica y evidencia | Resultado | Estado |
|---|---|---|---|
| Adecuación funcional | Extractores, capas Bronce/Plata/Oro, análisis, pruebas y `docs/requerimientos.md`. | Las funciones de captura, limpieza, análisis y tablero local están implementadas; queda pendiente la publicación del tablero para la cliente. | Parcial (A-03) |
| Eficiencia de desempeño | `docs/E3/optimizacion.md` y mediciones reproducibles. | Reporta −59 % de tiempo de captura y −26 % en limpieza; la salida de Plata conserva el mismo SHA-256. | Cumple según la medición documentada |
| Compatibilidad | CSV, GeoJSON y Shapefile de INEGI en `data/`. | Se usan formatos abiertos y convenciones geoestadísticas declaradas. | Cumple |
| Capacidad de interacción | `tablero/app.py`, `README.md` y RF-07 en `docs/requerimientos.md`. | El tablero tiene cuatro pestañas y explicaciones para la cliente, pero el README solo documenta ejecución local; RF-07 también dice que falta publicarlo. | **No cumple (A-03)** |
| Fiabilidad | `data/bitacora/capturas.csv`, RNF-01 y `.github/workflows/extraccion-bronce.yml`. | La automatización existe, pero el historial es corto y contiene dos fallas; no acredita ≥95 % en 14 días ni permite estimar MTBF/MTTR. | **Sin medición suficiente (A-02)** |
| Seguridad | Job `secretos` (gitleaks), `pip-audit` en `.github/workflows/ci.yml`, minimización DENUE. | Ambos análisis están integrados a CI y la ejecución de `main` indicada arriba terminó con éxito; el extractor elimina campos personales antes de escribir. | Cumple con controles automatizados |
| Mantenibilidad | Módulos por fuente, `tests/`, `ruff` y `pytest --cov --cov-fail-under=60` en CI. | La estructura es modular y la CI aplica lint y umbral de cobertura; la última ejecución observada concluyó con éxito. | Cumple |
| Portabilidad | `.github/workflows/ci.yml` (Ubuntu, Python 3.12) y `docs/E3/optimizacion.md` (medición en Windows 11). | Hay evidencia documentada en Windows y CI sobre Ubuntu. | Cumple según evidencia documentada |

## 3. Hallazgos

### A-01 — Actualidad insuficiente de la serie de defunciones

- **Característica ISO:** ISO/IEC 25012 — Actualidad.
- **Descripción:** la capa Oro contiene defunciones hasta diciembre de 2023. En noviembre de 2026, el desfase aproximado es de 35 meses, mayor que la meta de ≤12 meses registrada en la evaluación E2. La serie y el pronóstico 2024 no representan datos recientes.
- **Evidencia:** `data/oro/serie_mensual_colima.csv` (periodos 2018-01 a 2023-12); `docs/E2/evaluacion-iso.md` (meta de actualidad); `docs/E3/datasheet.md` (periodo y limitación de rezago).
- **Severidad:** **Mayor**. Limita la vigencia de los hallazgos de necesidad y del pronóstico para decisiones actuales.
- **Recomendación:** verificar la edición más reciente disponible de la fuente oficial, incorporarla mediante el pipeline y volver a validar serie, linaje y pronóstico. Si la fuente aún no publica periodos posteriores, declarar explícitamente el límite temporal en las vistas y conclusiones.

### A-02 — Evidencia insuficiente de disponibilidad y fiabilidad

- **Característica ISO:** ISO/IEC 25010 — Fiabilidad; ISO/IEC 25012 — Disponibilidad.
- **Descripción:** la bitácora solo contiene cuatro ejecuciones entre el 24 y el 26-nov; dos registran `failure`. Aunque la ejecución manual posterior del 26-nov fue exitosa, el periodo no permite demostrar el umbral de ≥95 % en los últimos 14 días ni calcular MTBF/MTTR.
- **Evidencia:** `data/bitacora/capturas.csv`; `docs/requerimientos.md` RNF-01; workflow `.github/workflows/extraccion-bronce.yml`.
- **Severidad:** **Mayor**. La fiabilidad es un criterio explícito del Sello TDL y todavía no tiene ventana de medición suficiente.
- **Recomendación:** mantener la captura diaria, conservar cada resultado en la bitácora y reportar la tasa sobre la ventana completa de 14 días cuando exista. No presentar el umbral como cumplido antes de contar con esa evidencia.

### A-03 — Tablero sin publicación para la cliente

- **Característica ISO:** ISO/IEC 25010 — Capacidad de interacción y adecuación funcional.
- **Descripción:** existe una aplicación Streamlit local con vistas de pronóstico, oferta, mapa multivariado y calidad, pero el repositorio no ofrece un enlace público. RF-07 marca expresamente la publicación como pendiente; por tanto, la cliente no puede consultar el producto en línea sin ejecutar el proyecto.
- **Evidencia:** `README.md` indica `http://localhost:8501`; `tablero/app.py` documenta uso local; `docs/requerimientos.md` RF-07 dice “falta publicarlo”.
- **Severidad:** **Mayor**. Falta un componente público del observatorio definido en los requisitos del proyecto.
- **Recomendación:** publicar el tablero en un servicio accesible, añadir la URL al README y verificar desde una sesión externa que carga datos y visualizaciones sin requerir el entorno de desarrollo.

### A-04 — Fecha del datasheet no coincide con el DENUE en Oro

- **Característica ISO:** ISO/IEC 25012 — Consistencia y Comprensibilidad.
- **Descripción:** `docs/E3/datasheet.md` indica que los consultorios provienen de la captura del 23-nov; la tabla Oro versionada contiene `fecha_ingesta_max=2026-11-26T06:38:25Z`. El datasheet no refleja la actualización registrada por la corrida del 26-nov.
- **Evidencia:** fila de `data/oro/consultorios_psicologia_geo.csv`; `docs/E3/datasheet.md`, tabla “Composición”; commit `160bf78`.
- **Severidad:** **Menor**. La discrepancia no cambia los registros, pero puede llevar a interpretar mal su vigencia.
- **Recomendación:** actualizar la fecha y conteos del datasheet al publicar cada versión del dataset, o generar esa sección automáticamente a partir de los metadatos de Oro.

## 4. Resultado

Se registran **4 hallazgos: 3 mayores y 1 menor; 0 críticos**. No se observó evidencia de datos de pacientes, columnas personales en Oro o credenciales en los artefactos inspeccionados. Los controles de CI, calidad y linaje están implementados; los hallazgos pendientes son la antigüedad de la serie, la falta de una ventana de fiabilidad suficiente, la publicación del tablero y la sincronización de metadatos del datasheet.
