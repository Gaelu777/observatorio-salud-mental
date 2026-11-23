# Observatorio de Salud Mental — Colima

Proyecto integrador. Observatorio que captura datos públicos oficiales de forma automática, los limpia por capas (Bronce → Plata → Oro) y los usa para pronosticar, experimentar y comparar grupos.

**Pregunta detonadora:** ¿Cómo evoluciona la necesidad de atención en salud mental en Colima y en qué zonas hay menos oferta de consultorios de psicología?

| Entrega | Documentos |
|---|---|
| E0 | [`docs/E0/propuesta.md`](docs/E0/propuesta.md) · [`docs/E0/ENTREGA.md`](docs/E0/ENTREGA.md) |

## Estructura

```
src/                  extractores y pipelines
data/bronce/          datos crudos de INEGI + manifiesto.csv (linaje)
data/plata/           datos limpios y validados
data/oro/             datos listos para análisis
data/cuarentena/      registros inválidos con motivo
calidad/              registros PSP por integrante
.github/workflows/    extracción automática mensual
```

## Fuentes

- INEGI, *Estadística de Defunciones Registradas* (datos abiertos).
- INEGI, *Directorio Estadístico Nacional de Unidades Económicas (DENUE)*.

Información de INEGI usada conforme a sus Términos de Libre Uso. Este proyecto no está respaldado por INEGI.
