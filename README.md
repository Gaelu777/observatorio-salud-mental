# Observatorio de Salud Mental — Colima

Proyecto integrador. Observatorio que captura datos públicos oficiales de forma automática, los limpia por capas (Bronce → Plata → Oro) y los usa para pronosticar, experimentar y comparar grupos.

**Pregunta detonadora:** ¿Cómo evoluciona la necesidad de atención en salud mental en Colima y en qué zonas hay menos oferta de consultorios de psicología?

| Entrega | Documentos |
|---|---|
| E0 | [`docs/E0/propuesta.md`](docs/E0/propuesta.md) · [`docs/E0/ENTREGA.md`](docs/E0/ENTREGA.md) |
| E1 | [`docs/E1/ENTREGA.md`](docs/E1/ENTREGA.md) · [`docs/E1/reporte_limpieza.md`](docs/E1/reporte_limpieza.md) · [`docs/relatoria-E1.md`](docs/relatoria-E1.md) |
| E2 | [`docs/E2/ENTREGA.md`](docs/E2/ENTREGA.md) · [`docs/etica-datos.md`](docs/etica-datos.md) · [`docs/relatoria-E2.md`](docs/relatoria-E2.md) · mapas en `docs/E2/` |

## Estructura

```
src/                  extractores (extraer_*.py) y pipelines (plata.py, oro.py)
tests/                prueba de la Puerta de Calidad
data/bronce/          datos crudos de INEGI + manifiesto.csv (linaje)
data/plata/           datos limpios y validados
data/oro/             datos listos para análisis
data/cuarentena/      registros inválidos con motivo
calidad/              registros PSP por integrante
.github/workflows/    pipeline automático mensual (Bronce → Plata → Oro → mapas → verificación de linaje)
```

## Fuentes

- INEGI, *Estadística de Defunciones Registradas* (datos abiertos).
- INEGI, *Directorio Estadístico Nacional de Unidades Económicas (DENUE)*.
- INEGI, *Censo de Población y Vivienda 2020*, Principales resultados por localidad (ITER).
- INEGI, *Marco Geoestadístico 2020*, Colima.

Información de INEGI usada conforme a sus Términos de Libre Uso. Este proyecto no está respaldado por INEGI.
