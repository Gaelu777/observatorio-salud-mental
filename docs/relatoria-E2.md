# Relatoría de etapa — E2

**Equipo:** Gael Alexandro Cortez Sarmienta · Luis Alejandro Mendoza Peñaloza
**Periodo:** noviembre 2026

## 1. Objetivo de la etapa

Integrar una fuente avanzada (geoespacial), garantizar que cada dato de Oro se pueda rastrear hasta su origen y documentar la ética y legalidad del observatorio.

## 2. Qué se hizo

1. **Nueva fuente:** Marco Geoestadístico 2020 de INEGI. Solo se guarda la capa municipal (300 KB de un zip de 29 MB), y como es un producto fijo no se vuelve a descargar cada mes.
2. **Análisis geoespacial con GeoPandas:** reproyección a metros, validación punto en polígono, conteo de competencia por radio desde el centro y dos mapas.
3. **Linaje completo:** se agregaron las tablas geoespaciales al linaje, se cubrió el caso de conteos cero y se escribió un verificador automático que re-lee Bronce.
4. **Declaración de ética** (`docs/etica-datos.md`).

## 3. Problemas encontrados y cómo se resolvieron

| Problema | Solución |
|---|---|
| Manzanillo incluye las islas Revillagigedo, a cientos de km, y el mapa quedaba diminuto | Recorte a la zona continental solo para visualizar; los datos no se modifican |
| Etiquetas de municipios encimadas en la zona metropolitana | Etiquetas desplazadas con línea guía |
| Etiquetas de los radios encimadas con consultorios | Recuadro con los conteos por radio |
| El verificador de linaje tronaba en vez de reportar cuando una fila apuntaba fuera del archivo | Se probó con linaje corrompido a propósito y se corrigió para que reporte y falle de forma controlada (defecto D9) |

## 4. Decisiones relevantes

- **Geoespacial en vez de redes sociales o API OAuth:** DENUE responde directamente la pregunta de la cliente (¿dónde está la competencia?) y no implica datos de personas.
- **EPSG:6372 para distancias:** es la proyección oficial de INEGI para México, en metros. Medir en grados daría errores de distancia.
- **Punto de referencia público:** el centro se mide desde el Jardín Libertad y no desde el consultorio de la cliente, para no exponer su ubicación.
- **Rampas de un solo color en los mapas** (azul = oferta, naranja = necesidad): se lee "más oscuro = más" sin leyenda de categorías, y dos mapas lado a lado evitan mezclar dos escalas en uno.

## 5. Hallazgos para la cliente

- **Competencia:** 12 consultorios de psicología a 1 km o menos del centro y 31 a 2 km o menos (la mitad del municipio).
- **Huecos de oferta:** Armería e Ixtlahuacán no tienen consultorios registrados y tienen las tasas de suicidio más altas del estado. Tecomán (116 mil habitantes) tiene solo 7.
- **Calidad del dato:** las 117 ubicaciones de DENUE coinciden con el municipio declarado.

## 6. Distribución del trabajo

| Integrante | Actividades |
|---|---|
| Gael Alexandro Cortez Sarmienta | _completar_ |
| Luis Alejandro Mendoza Peñaloza | _completar_ |

## 7. Aprendizajes y siguiente etapa

- Un linaje solo sirve si se verifica automáticamente; documentarlo no basta.
- Probar los verificadores con datos rotos a propósito encuentra errores que los datos buenos esconden.
- **Siguiente (E3):** pronóstico de la serie mensual y comparación multivariada de municipios (con tasas suavizadas).
