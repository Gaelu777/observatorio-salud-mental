# Ficha de entrega técnica — E1

| Campo | Valor |
|---|---|
| Tag | `e1` |
| Equipo | Gael Alexandro Cortez Sarmienta · Luis Alejandro Mendoza Peñaloza |
| Pipeline | `src/plata.py` → `src/oro.py` (scripts en `src/`, permitido por la rúbrica en lugar de notebook) |
| Automatización | `.github/workflows/extraccion-bronce.yml` corre Bronce → prueba → Plata → Oro cada mes |

## Checklist contra la rúbrica

| # | Requisito | Dónde se cumple | Evidencia |
|---|---|---|---|
| 1.1 | Faltantes: diagnóstico MCAR/MAR/MNAR e imputación justificada | `src/oro.py` → `diagnostico_faltantes()`, `imputar()` | `docs/E1/reporte_limpieza.md` §1 (chi-cuadrada, conclusión MAR + componente MNAR, hot-deck condicional) |
| 1.2 | Atípicos y ruido (IQR / Z robusto) | `marcar_atipicos()`; ruido de tabuladores en `plata.py` → `quitar_ruido_texto()` | §2: 4 meses atípicos por IQR, 2 por Z robusto; columnas `*_atipico_*` y `*_winsor` |
| 1.3 | Normalización Min-Max y Z-Score | `escalar()` | Columnas `*_minmax` y `*_z` en las 3 tablas Oro |
| 1.4 | Discretización y jerarquías conceptuales | `jerarquias()`, terciles en `municipios()` | §5: jerarquías de causa, tiempo, lugar y edad; niveles baja/media/alta |
| 1.5 | Reducción de datos | selección de columnas en Plata; agregación en Oro | §6: 74→13 variables; registro → mensual → trimestral |
| 2 | Integración de fuentes heterogéneas | `municipios()` | §3: tabla con 9 conflictos de esquema, tipo, codificación y granularidad, y cómo se resolvió cada uno |
| 3 | Puerta de Calidad automática con Pandera + cuarentena con motivo | `src/plata.py` (`ESQUEMA_DEF`, `ESQUEMA_DENUE`, `ESQUEMA_CENSO`, `puerta_calidad()`) | `data/cuarentena/*.csv` (columna `motivo`); `tests/test_puerta_calidad.py` |
| 4 | Ficha técnica y relatoría | este archivo, `docs/relatoria-E1.md` | — |

## Fuentes integradas

| Fuente | Bronce | Plata | Rol |
|---|---|---|---|
| INEGI — Defunciones registradas 2018–2023 | 37,136 registros | `data/plata/defunciones.csv` | Necesidad (variable a pronosticar) |
| INEGI — DENUE Colima, SCIAN 621 | 1,649 establecimientos | `data/plata/denue.csv` | Oferta (117 consultorios de psicología) |
| INEGI — Censo 2020, ITER Colima | 1,259 filas | `data/plata/censo2020_municipios.csv` (10 municipios) | Denominador de población |

## Capa Oro

| Archivo | Filas | Para qué |
|---|---|---|
| `serie_mensual_colima.csv` | 72 | Pronóstico (suicidios y trastornos mentales por mes) |
| `serie_trimestral_colima.csv` | 24 | Versión reducida por agregación |
| `factores_suicidio.csv` | conteos por año × trimestre × sexo × edad × zona | Factores a experimentar |
| `municipios_colima.csv` | 10 | Grupos multivariados (necesidad vs. oferta) |
| `linaje_oro.csv` | 1 fila por registro fuente usado | Trazabilidad Oro → Plata → Bronce |

## Puerta de Calidad: cómo funciona

1. Plata decodifica los códigos de INEGI. Los "no especificado" (mes 99, sexo 9, edad 4998) pasan a **nulo**: son faltantes legítimos, no errores.
2. Pandera valida en modo **perezoso** (`lazy=True`), así que junta todos los errores de todas las filas en una sola pasada.
3. Cada fila con al menos un error va a `data/cuarentena/<fuente>_cuarentena.csv` con la columna `motivo` (p. ej. `edad_anios: in_range(0, 120) (valor=150)` o `regla fecha_ocurrencia_valida`).
4. Al final se verifica **Bronce = Plata + Cuarentena (+ fuera de alcance)**. Si no cuadra, el pipeline falla (objetivo de calidad OC2). El resultado queda en `data/plata/resumen_plata.json`.

**Resultado con los datos reales:** 0 registros en cuarentena. INEGI publica datos ya validados, así que la puerta se probó con **registros defectuosos inyectados a propósito** (`tests/test_puerta_calidad.py`): los 5 casos inválidos van a cuarentena con su motivo y los faltantes legítimos pasan. La prueba corre en cada ejecución del workflow.

## Cómo reproducir

```bash
pip install -r requirements.txt
python src/extraer_denue.py && python src/extraer_censo.py && python src/extraer_defunciones.py
python tests/test_puerta_calidad.py
python src/plata.py
python src/oro.py            # regenera docs/E1/reporte_limpieza.md
```

## Limitaciones declaradas

- El indicador mide **necesidad** de atención en salud mental (mortalidad), no la demanda de consultas.
- La población es fija (Censo 2020) para 2018–2023, y la oferta (DENUE) es una foto de 2026.
- Las tasas de municipios pequeños son inestables (ver reporte §7).
