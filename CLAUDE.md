# Observatorio de Servicios Psicológicos — Proyecto Integrador (escuela)

## Qué es este proyecto

Proyecto escolar de **ingeniería/ciencia de datos**: un "observatorio" que captura datos públicos de forma automática, los limpia por capas (Bronce → Plata → Oro) y los usa para pronosticar, experimentar y comparar grupos.

La rúbrica oficial está en los archivos `docs/rubrica/ContextoEscuela0.txt` (E0), `ContextoEscuela1.txt` (E1) y `ContextoEscuela2.txt` (E2). **Esos archivos son la fuente de verdad de lo que se evalúa.** Léelos antes de proponer cualquier entregable y verifica cada punto contra ellos; la evaluación es literal (rutas de archivos, tags de git, número de periodos).

## Cliente real

El cliente es una **psicóloga con consultorio propio en México**. Ella es:
- La persona entrevistada para la "Entrevista de campo" de E0.
- El "cliente potencial" del observatorio: los hallazgos deben servirle a ella (competencia cercana, temporadas de mayor demanda, zonas con poca oferta, etc.).

Existe un proyecto aparte (`D:\sistemaPsicologia`, sistema de gestión del consultorio en Node + Supabase). **No tiene relación técnica con este repo**: no se comparte código ni base de datos, y NUNCA se usan datos de ese sistema aquí.

## Regla de privacidad (no negociable)

- Este repo lo ven 3 profesores como colaboradores. Solo contiene **datos públicos y agregados**.
- **Cero datos personales.** Nunca datos de pacientes de la psicóloga, ni nombres, teléfonos o información clínica. Ni siquiera "anonimizados".
- La entrevista se documenta con lo que ella dijo sobre el sector, no con información de sus pacientes.
- Nada de credenciales en el código: tokens/API keys van en `.env` (en `.gitignore`) o en GitHub Secrets para Actions.

## Pregunta y fuentes (propuesta inicial, pendiente de validar)

Pregunta detonadora tentativa: *"¿Cómo evoluciona la demanda de atención psicológica en [ciudad/región] y dónde hay huecos de oferta?"*

Fuentes candidatas (verificar disponibilidad, granularidad para la región, robots.txt y términos de uso ANTES de comprometerse):
- **DENUE (INEGI)**: consultorios de psicología registrados, con ubicación → sirve también como fuente geoespacial de E2.
- **Google Trends**: búsquedas tipo "psicólogo", "ansiedad", "terapia" por región → serie mensual con ≥36 periodos (requisito E0).
- **INEGI / Secretaría de Salud / datos.gob.mx**: encuestas y estadísticas de salud mental.

Las 3 preguntas analíticas (E0) deben mapear a:
- E1 → variable a **pronosticar** (ej. índice mensual de búsqueda).
- E2 → **factores a experimentar** (ej. temporada, región, tipo de servicio).
- E3 → **grupos multivariados a comparar** (ej. municipios por oferta vs. demanda).

## Stack

- Python (pandas, requests; Pandera o Great Expectations para la puerta de calidad; GeoPandas para lo geoespacial).
- GitHub Actions para ejecutar la extracción automáticamente (capa Bronce).
- Notebooks o scripts en `src/` según pida cada entrega.

Si vas a instalar dependencias, explica qué hace cada una y por qué sobre alternativas. Usa un `requirements.txt` con versiones fijadas.

## Estructura esperada

```
docs/
  rubrica/              ← los ContextoEscuela*.txt del maestro
  E0/propuesta.md       ← 3 a 5 páginas
  E0/ENTREGA.md
  E1/ENTREGA.md, E1/limpieza.ipynb (o scripts en src/)
  E2/ENTREGA.md
  etica-datos.md        ← E2
  relatoria-E1.md, relatoria-E2.md
calidad/
  tiempo-<nombre>.csv   ← uno por integrante (PSP)
  defectos-<nombre>.csv
src/                    ← extractores y pipelines
data/bronce/            ← datos crudos tal cual se descargan (no se modifican)
data/plata/             ← limpios y validados
data/oro/               ← listos para análisis, con linaje hacia bronce
data/cuarentena/        ← registros inválidos con motivo (nunca borrar en silencio)
.github/workflows/      ← extracción automática
```

## Entregas y estado

- **E0** (tag `e0`): fecha oficial era el lunes 9 de noviembre de 2026; **ya está atrasada**. Prioridad máxima.
- **E1** (tag `e1`) y **E2** (tag `e2`): ver rúbricas.

## Datos que aún NO sabes (pregúntaselos al usuario, no inventes)

- Ciudad/región exacta del observatorio.
- Nombres de los integrantes del equipo (o si es individual), para los archivos de `calidad/`.
- Si la entrevista con la psicóloga ya se hizo y qué respondió.
- Fechas límite de E1 y E2.
- Si la extensión o entrega tardía de E0 está permitida.

## Cómo comportarte

- Sé directo. Si algo no cumple la rúbrica, dilo.
- Si no estás seguro de algo (ej. si una fuente tiene datos suficientes), dilo y propón cómo verificarlo.
- El usuario es nivel intermedio: explica decisiones no triviales (por qué IQR vs Z-Score, por qué cierto mecanismo de faltantes), no lo obvio.
- Comentarios y documentación en español.
- Trabajo por etapas: termina y verifica una entrega antes de pasar a la siguiente.
- Commits cortos, sin línea "Co-Authored-By". Sugiere commit tras cada cambio significativo.
- No borres archivos sin confirmar.
