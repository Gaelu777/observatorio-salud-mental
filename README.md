# Observatorio de Salud Mental — Colima

Proyecto integrador. Observatorio que captura datos públicos oficiales de forma automática, los limpia por capas (Bronce → Plata → Oro) y los usa para pronosticar, experimentar y comparar grupos.

**Pregunta detonadora:** ¿Cómo evoluciona la necesidad de atención en salud mental en Colima y en qué zonas hay menos oferta de consultorios de psicología?

| Entrega | Documentos |
|---|---|
| E0 | [`docs/E0/propuesta.md`](docs/E0/propuesta.md) · [`docs/E0/ENTREGA.md`](docs/E0/ENTREGA.md) |
| E1 | [`docs/E1/ENTREGA.md`](docs/E1/ENTREGA.md) · [`docs/E1/reporte_limpieza.md`](docs/E1/reporte_limpieza.md) · [`docs/E1/pronostico.md`](docs/E1/pronostico.md) · [`docs/relatoria-E1.md`](docs/relatoria-E1.md) · [`data/oro/DICCIONARIO.md`](data/oro/DICCIONARIO.md) |
| Calidad | [`docs/plan-sqa.md`](docs/plan-sqa.md) · [`docs/requerimientos.md`](docs/requerimientos.md) · [`calidad/`](calidad/) · CI en [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |
| E2 | [`docs/E2/ENTREGA.md`](docs/E2/ENTREGA.md) · [`docs/etica-datos.md`](docs/etica-datos.md) · [`docs/relatoria-E2.md`](docs/relatoria-E2.md) · mapas en `docs/E2/` |
| E3 (en curso) | [`docs/E3/multivariado.md`](docs/E3/multivariado.md) · [`docs/E3/tendencias.md`](docs/E3/tendencias.md) · [`docs/E3/datasheet.md`](docs/E3/datasheet.md) |

## Cómo ejecutarlo

```bash
pip install -r requirements-dev.txt          # Python 3.11+
python src/plata.py && python src/oro.py && python src/geoespacial.py   # Bronce -> Plata -> Oro
python src/pronostico.py && python src/multivariado.py && python src/diccionario_oro.py
streamlit run tablero/app.py                 # tablero en http://localhost:8501
pytest --cov                                 # pruebas (incluye reproducibilidad completa)
```

## Estructura

```
src/                  extractores (extraer_*.py), pipelines (plata.py, oro.py, geoespacial.py) y
                      laboratorio (pronostico.py, experimento_factorial.py, multivariado.py)
tablero/              tablero Streamlit (lee solo la capa Oro)
tests/                pruebas: Puerta de Calidad, reproducibilidad Bronce -> Oro, análisis y tablero
data/bronce/          datos crudos de INEGI + manifiesto.csv (linaje)
data/plata/           datos limpios y validados
data/oro/             datos listos para análisis + DICCIONARIO.md + LICENCIA.md (CC BY 4.0)
data/cuarentena/      registros inválidos con motivo
calidad/              registros PSP por integrante
data/bitacora/        una fila por corrida automática (disponibilidad, MTBF, MTTR)
.github/workflows/    extraccion-bronce.yml: captura diaria + pipeline completo · ci.yml: ruff, pytest, pip-audit, gitleaks
```

## Fuentes

- INEGI, *Estadística de Defunciones Registradas* (datos abiertos).
- INEGI, *Directorio Estadístico Nacional de Unidades Económicas (DENUE)*.
- INEGI, *Censo de Población y Vivienda 2020*, Principales resultados por localidad (ITER).
- INEGI, *Marco Geoestadístico 2020*, Colima.

Información de INEGI usada conforme a sus Términos de Libre Uso. Este proyecto no está respaldado por INEGI.
