# Requerimientos verificables del observatorio

Cada requerimiento se revisó contra cuatro características:
- **Necesario:** quitarlo rompe la pregunta o una entrega.
- **No ambiguo:** tiene un solo número o una sola condición.
- **Verificable:** tiene una comprobación automática o un procedimiento.
- **Rastreable:** se sabe de dónde viene (rúbrica, cliente o norma) y qué archivo lo implementa.

Estado al 2026-11-24.

## Funcionales

| ID | Requerimiento | Origen | Implementado en | Cómo se comprueba | Estado |
|---|---|---|---|---|---|
| RF-01 | El sistema descarga sin intervención humana el DENUE de Colima **cada día** a las 07:00 (hora de Colima), y las demás fuentes el día 5 de cada mes. | Rúbrica E0 (captura programada) | `.github/workflows/extraccion-bronce.yml` | Una fila por día en `data/bitacora/capturas.csv`, más el historial de Actions | ✔ desde el 2026-11-24 |
| RF-02 | Cada archivo de Bronce queda registrado con su URL, la fecha de captura en UTC, su SHA-256 y el número de registros. | Rúbrica E0 (metadatos de captura) | `src/comun.py` → `data/bronce/manifiesto.csv` | La prueba `test_sha256` y la revisión del manifiesto | ✔ |
| RF-03 | La serie histórica tiene **36 periodos mensuales o más**. | Rúbrica E0 | `data/oro/serie_mensual_colima.csv` | Conteo de filas: 72 ≥ 36 | ✔ |
| RF-04 | Todo registro de Bronce termina en Plata **o** en cuarentena con su motivo: `bronce = plata + cuarentena`. | Rúbrica E1, OC2 | `src/plata.py` (Pandera) | `test_puerta_calidad_cuarentena` y `resumen_plata.json` (`oc2_sin_perdida`) | ✔ |
| RF-05 | Cada fila de Oro se puede rastrear hasta un archivo y una fila de Bronce. | Rúbrica E2 (linaje) | `data/oro/linaje_oro.csv` | `src/verificar_linaje.py` detiene el pipeline si falla; `test_linaje_completo` | ✔ 652/652 |
| RF-06 | El sistema publica un pronóstico de 12 meses con un intervalo del 95 %, elegido por el menor RMSE en datos de prueba. | Rúbrica E1 | `src/pronostico.py` | `test_pronostico_reproducible` (comprueba límites ≤ pronóstico ≤ límites y que no haya negativos) | ✔ |
| RF-07 | El tablero muestra el pronóstico, el mapa de oferta y el mapa de componentes principales, cada uno con una frase de interpretación para la cliente. | Rúbrica E1/E2/E3 | `tablero/app.py` | `test_tablero_carga_sin_errores` y revisión visual | ✔ local; falta publicarlo |
| RF-08 | Toda columna de Oro está documentada en el diccionario. | Rúbrica E1 | `src/diccionario_oro.py` | El script falla si encuentra una columna sin descripción; `test_diccionario_documenta_todo` | ✔ |

## No funcionales

| ID | Requerimiento | Origen | Cómo se comprueba | Meta | Estado |
|---|---|---|---|---|---|
| RNF-01 | **Disponibilidad** de la captura programada | OC1, Sello TDL | Corridas exitosas / corridas programadas en `capturas.csv` | ≥ 95 % en los últimos 14 días | ⏳ La bitácora empezó el 2026-11-23; hay que juntar 7 días para el MTBF y el MTTR |
| RNF-02 | **Cero secretos** en el historial de git | Sello TDL | gitleaks en la CI (`.github/workflows/ci.yml`, job `secretos`) | 0 hallazgos | ⏳ Se medirá en la primera corrida de la CI |
| RNF-03 | **Cero vulnerabilidades conocidas** sin atender en las dependencias | Rúbrica E1 Calidad | pip-audit en la CI | 0 | ✔ Se encontró y corrigió la CVE-2026-25087 de pyarrow (2026-11-24) |
| RNF-04 | **Cobertura** de pruebas automáticas | Sello TDL | `pytest --cov --cov-fail-under=60` en la CI | ≥ 60 % | ✔ 71 % (2026-11-24) |
| RNF-05 | **Reproducibilidad:** un tercero que clona el repositorio obtiene las mismas tablas de Oro | Sello TDL | `test_reproducibilidad` corre Bronce → Oro y compara contra las tablas versionadas | Diferencias = 0 (tolerancia de 1e-9) | ✔ |
| RNF-06 | **Completitud** de la capa Oro (ISO/IEC 25012) | Sello TDL | % de celdas no nulas en `diccionario_oro.csv` | ≥ 95 % | ✔ 100 % |
| RNF-07 | **Privacidad:** ninguna columna con nombre, teléfono o dato clínico de una persona | CLAUDE.md, ética | Revisión del diccionario: las únicas llaves son CLEE (establecimiento) e id de linaje | 0 columnas personales | ✔ |
| RNF-08 | **Respeto a la fuente:** User-Agent identificable, 5 s de pausa entre descargas y solo rutas permitidas por robots.txt | Ética, E0 | `src/comun.py` y `docs/E0/evidencia/robots_inegi_2026-11-23.txt` | Revisión de código | ✔ |
| RNF-09 | **Estilo:** el código pasa el linter sin errores | Rúbrica E1 (CI) | `ruff check src tests tablero` en la CI | 0 errores | ✔ |
| RNF-10 | **Tiempo del pipeline completo** (Plata → Oro → mapas → linaje → pronóstico → multivariado) | ISO 25010, eficiencia | Duración en `capturas.csv` | ≤ 10 min por corrida diaria | ⏳ Se mide en las corridas |

## Requerimientos que se corrigieron en la revisión

| Antes (ambiguo) | Problema | Después |
|---|---|---|
| "La captura debe ser confiable" | No tiene número | RNF-01: ≥ 95 % de corridas exitosas en 14 días |
| "Los datos deben estar limpios" | No se puede verificar | RF-04: `bronce = plata + cuarentena`, con motivo por registro |
| "El pronóstico debe ser bueno" | "Bueno" según quién | RF-06: el menor RMSE en 12 meses que el modelo no vio, más Ljung-Box aprobado |
