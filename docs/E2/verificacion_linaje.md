# Verificación de linaje — E2

> Generado por `src/verificar_linaje.py`. Se ejecuta en cada corrida del workflow; si falla, el pipeline se detiene.

## Cobertura por tabla Oro

| Tabla | Filas | Filas con linaje | Entradas de linaje | Estado |
|---|---|---|---|---|
| `serie_mensual_colima` | 72 | 72 | 525 | OK |
| `serie_trimestral_colima` | 24 | 24 | 525 | OK |
| `factores_suicidio` | 137 | 137 | 327 | OK |
| `municipios_colima` | 10 | 10 | 651 | OK |
| `competencia_centro_colima` | 3 | 3 | 46 | OK |
| `consultorios_psicologia_geo` | 117 | 117 | 117 | OK |

## Cadena Oro → Plata → Bronce → origen

- Registros fuente distintos citados en el linaje: **652**
- Encontrados en Plata con el mismo archivo y fila de Bronce: **652**
- Fila exacta re-leída en Bronce y valor de control idéntico: **652**
- Cada archivo de Bronce está en `data/bronce/manifiesto.csv` con su URL de origen, fecha de ingesta y SHA-256 del archivo descargado.

## Resultado

**OK: todas las filas de Oro son rastreables hasta su origen.**
