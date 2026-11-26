# Observatorio de Salud Mental — Colima (Proyecto Integrador escolar)

> Instrucciones para cualquier asistente de IA que trabaje en este repositorio.
> Última actualización: 26 de noviembre de 2026.

## Qué es este proyecto

Proyecto escolar que integra tres materias: **Ingeniería de Datos**, **Análisis Estadístico** y **Calidad en Sistemas de Información**. Es un "observatorio" que captura datos públicos del INEGI de forma automática, los limpia por capas (Bronce → Plata → Oro) y los usa para pronosticar, experimentar y comparar grupos.

**Equipo (2 integrantes):**
- Gael Alexandro Cortez Sarmienta: dueño del repositorio, desarrollo del pipeline y análisis.
- Luis Alejandro Mendoza Peñaloza: revisor SQA y auditor interno en E3 (planeación, investigación y diseño en etapas anteriores).

**Región:** estado de **Colima**, México (10 municipios; en E3 la unidad de análisis son las 65 localidades de 500 habitantes o más).

## Rúbrica (fuente de verdad)

- La rúbrica **completa** de las 3 materias es el PDF `proyecto 4434#.pdf`. **No está en el repositorio** (cada integrante lo tiene de la escuela). Si no lo tienes, pídeselo al usuario antes de evaluar criterios de Calidad o de Estadística.
- `docs/rubrica/ContextoEscuela0.txt` a `ContextoEscuela3.txt` solo cubren **Ingeniería de Datos**.
- La evaluación es literal: rutas de archivos, tags de git y número de periodos. Verifica cada punto contra la rúbrica.

## Cliente real

Una **psicóloga con consultorio propio en México**. Es la persona de la entrevista de campo (E0) y la usuaria potencial del observatorio: los hallazgos deben servirle (competencia cercana, zonas con poca oferta, temporadas de demanda).

## Regla de privacidad (no negociable)

- Este repositorio lo ven 3 profesores. Solo contiene **datos públicos y agregados**.
- **Cero datos personales.** Nunca datos de pacientes, ni nombres, teléfonos o información clínica, ni siquiera "anonimizados".
- La entrevista se documenta solo con lo que ella dijo **sobre el sector**.
- El sistema de gestión del consultorio es otro proyecto, sin relación técnica con este. **Nunca** se usan sus datos aquí.
- El extractor del DENUE elimina nombre, razón social, teléfono, correo y web **antes** de escribir a disco (excepción documentada a "Bronce = crudo").
- Nada de credenciales en el código. Las fuentes actuales no usan token. Si alguna lo necesitara: `.env` (en `.gitignore`) o GitHub Secrets.

## Decisiones ya tomadas (no volver a preguntarlas)

| Tema | Decisión | Dónde está justificada |
|---|---|---|
| Fuentes | Solo **INEGI oficial y sin token**: DENUE (consultorios, SCIAN 621331/621332), Defunciones registradas (serie mensual), Censo 2020 ITER y Marco Geoestadístico 2020. Google Trends se **descartó** | `docs/E0/propuesta.md`, `README.md` |
| Pronóstico (E1) | Ganó ARIMA(0,0,0), que equivale a la media histórica. Se presenta como hallazgo (la serie es ruido), no como fracaso | `docs/E1/pronostico.md` |
| Unidad de E3 | 65 localidades ≥ 500 hab., no municipios (con n = 10 no alcanza para el MANOVA) | `docs/E3/multivariado.md` |
| Licencia de Oro | CC BY 4.0 | `data/oro/LICENCIA.md`, `docs/E3/datasheet.md` |
| Puerta de calidad | Pandera; los registros inválidos van a `data/cuarentena/` con motivo, nunca se borran en silencio | `src/plata.py` |
| Auditoría cruzada de E2 | **No se hizo**: no se asignó equipo auditor ni hubo reporte. Se sustituye con una **auditoría interna** (ISO/IEC 25010 y 25012) que hace Luis; se cierra en `docs/E3/cierre-auditoria.md` | — |

## Entregas

| Entrega | Tag | Estado (26-nov) |
|---|---|---|
| E0 | `e0` | Todo hecho excepto la entrevista (sección 2 de `docs/E0/propuesta.md`). **Aún no hay tag** |
| E1 | `e1` | Entregada |
| E2 | `e2` | Entregada |
| E3 | `e3` | **Lunes 30 de noviembre de 2026.** Ficha con lo pendiente (⏳) en `docs/E3/ENTREGA.md` (rama `calidad-e3` hasta que se haga merge) |
| Demo Day | — | Miércoles 2 de diciembre |
| E4 | `e4` | Viernes 4 de diciembre (reporte final) |

Pendientes principales de E3: cierre de auditoría, retrospectiva PSP (necesita el PSP de Luis), relatoría E3, publicar el tablero y confirmar que el dataset sea público.

## Registro PSP (`calidad/`)

- Cada integrante llena **solo su propio** `tiempo-<nombre>.csv` y `defectos-<nombre>.csv` (formato en `calidad/README.md`).
- **Nunca inventes horas, fechas ni defectos.** Lo reconstruido de memoria se marca como *estimado* en comentarios; lo que no se recuerda se deja como no recordado.
- La fase debe coincidir con la evidencia de git: si alguien investigó o planeó algo que otro programó, es Planeación o Diseño, no Código.
- Lo nuevo se registra en el momento, con hora real de inicio y fin.

## Stack y entorno

- Python 3.12 con versiones **fijadas** en `requirements*.txt` (pandas 2.2.3, Pandera, GeoPandas, statsmodels, Streamlit). Usa un entorno virtual: con pandas 3.x el pipeline falla localmente aunque en la CI pase.
- Si instalas o cambias dependencias, explica qué hace cada una y por qué sobre las alternativas.
- Comandos de uso diario: `COMO-EJECUTAR.md`.

## Automatización (GitHub Actions)

- `extraccion-bronce.yml` (**Pipeline Bronce-Plata-Oro**): todos los días a las 13:00 UTC (07:00 de Colima). Cada corrida, exitosa o fallida, agrega una fila a `data/bitacora/capturas.csv` (evidencia de disponibilidad, MTBF y MTTR).
- `ci.yml`: ruff, pytest con cobertura ≥ 60 %, pip-audit y gitleaks en cada push.
- El robot hace commits en `main` todos los días: **siempre `git pull` antes de un merge**.
- Para volver a correr el pipeline usa **"Run workflow"**, no "Re-run jobs" (que repite un commit viejo y choca al hacer push).
- 25-nov: el INEGI cambió los encabezados del DENUE a mayúsculas; se corrigió en el commit 914774e (`normalizar_columnas` en `src/extraer_denue.py`).

## Estructura

```
docs/rubrica/            ContextoEscuela0-3.txt (solo Ing. de Datos)
docs/E0..E3/             ENTREGA.md de cada etapa + documentos de análisis
docs/relatoria-EX.md     relatoría de cada etapa (formato de 6 preguntas)
docs/plan-sqa.md         plan de calidad: roles, revisiones, lista antes del tag
calidad/                 PSP por integrante
src/                     extractores, plata.py, oro.py, análisis
tablero/app.py           tablero Streamlit
tests/                   pytest (incluye reproducibilidad Bronce -> Oro)
data/bronce/             crudo tal cual se descarga (no se modifica a mano)
data/plata/, data/oro/   limpio y listo para análisis, con linaje a Bronce
data/cuarentena/         registros inválidos con motivo
data/bitacora/           una fila por corrida del pipeline
```

## Flujo de git

1. Rama nueva a partir de `main` actualizado.
2. Commits cortos, **sin la línea "Co-Authored-By"**.
3. Push y esperar la CI en verde.
4. `git merge --ff-only` a `main` y push. **Solo Gael** hace los merge a `main` y crea los tags.

No borres archivos sin confirmar.

## Cómo comportarte

- Sé directo. Si algo no cumple la rúbrica, dilo.
- Si no estás seguro de algo, dilo y propón cómo verificarlo. No inventes resultados, hallazgos ni registros.
- El usuario es de nivel intermedio: explica las decisiones no triviales, no lo obvio.
- Comentarios y documentación en español.
- Trabajo por etapas: termina y verifica una entrega antes de pasar a la siguiente.
