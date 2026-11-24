# Plan de Aseguramiento de la Calidad del Software (SQA)

Estructura basada en **IEEE 730-2014**, adaptada a un equipo de 2 personas y a un observatorio de datos públicos.
Versión 1.0 · 2026-11-24.

---

## 1. Propósito y alcance

**Propósito:** asegurar que el observatorio entregue a la cliente (una psicóloga con consultorio en Colima) datos y análisis **correctos, rastreables y disponibles**, y que cualquier defecto se detecte antes de llegar a un tag de entrega.

**Alcance:**

| Incluye | No incluye |
|---|---|
| Extractores (`src/extraer_*.py`), pipeline Bronce → Plata → Oro, análisis (`pronostico.py`, `experimento_factorial.py`, `multivariado.py`), tablero (`tablero/app.py`), workflows de GitHub Actions y documentación de entregas | Los servidores del INEGI (no los controlamos; solo medimos su disponibilidad), el sistema de gestión del consultorio de la cliente (proyecto aparte, sin relación técnica) |

**Aseguramiento vs. control:**
- El **control de calidad** revisa el producto: pruebas, puerta Pandera y verificación de linaje.
- El **aseguramiento** revisa el proceso: que las pruebas existan y se corran, que los defectos se registren y que haya revisión antes de cada tag.

Este plan cubre los dos.

## 2. Roles y responsabilidades

| Rol | Persona | Responsabilidades |
|---|---|---|
| Desarrollo de captura y pipeline | Gael Alexandro Cortez Sarmienta | Extractores, Plata/Oro, workflows |
| Análisis estadístico y tablero | Luis Alejandro Mendoza Peñaloza | Pronóstico, experimento, multivariado, tablero |
| **Revisor SQA** | **Rotativo: revisa quien NO escribió el cambio** | Revisa el pull request o commit contra la lista de la sección 5 antes del tag |
| Auditor externo | Equipo asignado en la auditoría cruzada (E2) | Auditoría con ISO 25010/25012; sus hallazgos entran al registro de la sección 7 |

**Independencia del revisor:** con 2 integrantes no hay un área de calidad separada. La independencia se logra con la regla *nadie aprueba su propio trabajo*: el revisor siempre es el otro integrante, y la CI hace una revisión automática que no depende de ninguno de los dos.

> ⚠️ Esta tabla de roles es una **propuesta**. El equipo debe confirmarla o corregirla según cómo se repartió el trabajo en realidad (ver la sección 6 de las relatorías).

## 3. Estándares y métricas

| Área | Estándar adoptado | Métrica | Meta |
|---|---|---|---|
| Código Python | PEP 8 vía **ruff** (reglas E, W, F, B; línea ≤ 160) | errores de ruff | 0 |
| Datos | Esquemas **Pandera** por fuente (tipos, rangos, unicidad, reglas de negocio) | `bronce − plata − cuarentena` | 0 (OC2) |
| Calidad de producto | **ISO/IEC 25010** | 8 características medidas (`docs/E2/evaluacion-iso.md`) | — |
| Calidad de datos | **ISO/IEC 25012** | completitud de Oro | ≥ 95 % |
| Proceso personal | **PSP**: registros de tiempo y defectos por integrante (`calidad/`) | % de defectos removidos antes de `main` | ≥ 80 % (OC3) |
| Fiabilidad | Bitácora de capturas | disponibilidad, MTBF y MTTR | ≥ 95 % (OC1) |
| Pruebas | pytest + pytest-cov | cobertura de líneas | ≥ 60 % |
| Seguridad | gitleaks + pip-audit | secretos / CVE sin atender | 0 / 0 |
| Documentación | Diccionario de Oro generado del código | columnas sin documentar | 0 |
| Comentarios y documentación | En español | — | — |

## 4. Revisiones y auditorías

| Revisión | Cuándo | Quién | Evidencia |
|---|---|---|---|
| Revisión automática (CI) | En cada push | GitHub Actions (`ci.yml`) | Palomita verde o tache rojo en el commit |
| Revisión entre pares | Antes de crear cada tag (`e0` a `e4`) | El integrante que no escribió el cambio | Comentario en el commit o PR con la lista de la sección 5 |
| Revisión contra la rúbrica | Antes de cada tag | Ambos | Tabla "criterio → archivo" en `docs/EX/ENTREGA.md` |
| Auditoría cruzada | Del 19 al 23 de noviembre (E2) | Otro equipo | Reporte de hallazgos; cierre en E3 |
| Postmortem | Al cerrar cada entrega | Ambos | Relatoría de etapa (`docs/relatoria-EX.md`) |

## 5. Pruebas

| Nivel | Qué prueba | Archivo |
|---|---|---|
| Unitarias | Métricas de error, Mardia, Pillai, conversión de coordenadas, SHA-256 y el rechazo de respuestas HTML del INEGI | `tests/test_pipeline.py` |
| Puerta de calidad | 5 registros inválidos inyectados van a cuarentena con el motivo correcto, y los faltantes legítimos pasan | `tests/test_puerta_calidad.py` |
| Integración / reproducibilidad | El pipeline completo desde Bronce produce exactamente las mismas tablas de Oro | `test_reproducibilidad`, `test_multivariado_reproducible`, `test_pronostico_reproducible` |
| Linaje | Todas las filas de Oro llegan a Bronce | `test_linaje_completo` y el paso del workflow |
| Humo del tablero | La app corre sin excepciones y muestra sus 4 pestañas | `tests/test_tablero.py` |

**Lista de revisión antes del tag:**
1. La CI está en verde.
2. No hay archivos de datos modificados a mano en Bronce.
3. Hay una entrada nueva en el PSP de cada integrante.
4. `ENTREGA.md` apunta a archivos que existen.
5. No hay datos personales.
6. No hay credenciales.

## 6. Reporte de problemas y acciones correctivas

- **Sistema de reporte:** los registros de defectos PSP (`calidad/defectos-<nombre>.csv`), abiertos desde E0. Cada defecto anota tipo, fase de inyección, fase de remoción, minutos de corrección y el defecto que lo originó.
- **Fallas de operación:** la bitácora `data/bitacora/capturas.csv` registra cada corrida automática, exitosa o fallida, con su duración.
- **Hallazgos de auditoría:** se registran en `docs/E3/cierre-auditoria.md` con severidad (crítico, mayor o menor), acción correctiva, evidencia (commit) y estado.

**Flujo:** se detecta (CI, revisión, auditoría o falla de la captura) → se registra → se corrige en una rama o commit → la CI queda en verde → se cierra con el commit como evidencia.

**Regla de severidad:** un defecto **crítico**, es decir, uno que produce datos incorrectos en Oro, expone secretos o datos personales, o detiene la captura más de 48 h, bloquea el tag hasta corregirse.

**Ejemplo real (2026-11-24):**
- **Detección:** pip-audit encontró la CVE-2026-25087 en pyarrow 22.0.0.
- **Severidad:** mayor, porque el experimento de E2 lee archivos Feather (Arrow IPC).
- **Acción:** se actualizó a 23.0.1 en `requirements.txt`.
- **Verificación:** pip-audit sin hallazgos y pruebas en verde.

## 7. Herramientas

| Herramienta | Uso | Por qué esta |
|---|---|---|
| GitHub Actions | Captura programada y CI | Gratis para repositorios públicos o educativos; corre aunque nadie tenga la computadora prendida |
| Pandera | Puerta de calidad | Esquemas declarativos dentro de pandas, sin servidor (se prefirió sobre Great Expectations) |
| pytest, pytest-cov | Pruebas y cobertura | Es el estándar en Python |
| ruff | Linter | Una sola herramienta que reemplaza flake8 e isort, y es muy rápida |
| pip-audit | Vulnerabilidades de dependencias | Usa la base de datos oficial PyPA/OSV |
| gitleaks | Secretos en el historial | Revisa todos los commits, no solo el estado actual |
| Streamlit | Tablero | Es la opción recomendada por el kit del curso; se escribe en Python |

## 8. Control de versiones y configuración

- **Repositorio:** git en GitHub, rama `main`, un **tag por entrega** (`e0` a `e4`). Un tag no se mueve sin avisar al profesor.
- **Dependencias** fijadas con versión exacta en `requirements*.txt`.
- **Bronce es inmutable:** cada captura crea un archivo nuevo identificado por su hash, y los archivos existentes no se editan.
- **Datos generados:** Plata y Oro se regeneran con el pipeline y se versionan para tener evidencia y poder reproducirlos.
- **Secretos:** solo en `.env` (ignorado por git) o en GitHub Secrets. Hoy no hay ninguno, porque todas las fuentes son abiertas.

## 9. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| El INEGI cambia una URL o devuelve HTML en lugar del archivo | Media | Alto: falla la captura | Validación del Content-Type (defecto D1); la bitácora registra la falla; los reintentos tienen espera |
| El INEGI publica 2024 con otro formato | Media | Medio | La Puerta Pandera detiene registros fuera de esquema y los manda a cuarentena |
| El trabajo queda concentrado en un integrante | Alta | Alto: la defensa individual multiplica la calificación por 0.5 si alguien no sabe explicar | Revisión cruzada obligatoria; cada integrante explica la parte del otro antes del Demo Day |
| Se suben datos personales por error | Baja | Crítico | Solo hay fuentes agregadas; el diccionario documenta cada columna |
| La captura automática deja de correr (GitHub desactiva los schedules tras 60 días sin actividad) | Baja dentro del curso | Medio | Commits frecuentes; disparo manual disponible |
