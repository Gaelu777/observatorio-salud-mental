# Sistema de Calidad (PSP)

Cada integrante registra **su propio** tiempo y defectos en `tiempo-<nombre>.csv` y `defectos-<nombre>.csv`.
Se registra al momento (no al final de la semana).

## Registro de tiempo
| Campo | Significado |
|---|---|
| `fecha`, `inicio`, `fin` | Formato `AAAA-MM-DD` y `HH:MM` |
| `interrupcion_min` | Minutos de interrupciones dentro del bloque |
| `delta_min` | `fin - inicio - interrupcion_min` |
| `fase` | Planeacion, Diseno, Codigo, Revision, Pruebas, Documentacion, Postmortem |

## Registro de defectos
Tipos estándar PSP: 10-Documentacion, 20-Sintaxis, 30-Construccion, 40-Asignacion, 50-Interfaz,
60-Verificacion, 70-Datos, 80-Funcion, 90-Sistema, 100-Entorno.
`defecto_origen` = id del defecto que provocó este (si aplica).

## Objetivos de calidad medibles

| # | Objetivo | Métrica | Meta | Cómo se mide |
|---|---|---|---|---|
| OC1 | Captura confiable | % de ejecuciones diarias del workflow `Pipeline Bronce-Plata-Oro` terminadas con éxito | ≥ 95 % | `data/bitacora/capturas.csv` (una fila por corrida, exitosa o fallida) + historial de GitHub Actions |
| OC2 | Cero pérdida silenciosa | `registros_bronce = registros_plata + registros_cuarentena` en cada corrida | 100 % de corridas (diferencia = 0) | Chequeo automático del pipeline de Plata (E1) |
| OC3 | Defectos detectados temprano | % de defectos removidos en Revisión o Pruebas (antes de llegar a `main`/tag) | ≥ 80 % | Columna `fase_remocion` de `defectos-*.csv` |
