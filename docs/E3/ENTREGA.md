# Ficha de entrega — E3 · Mapa multivariado y sello

| Campo | Valor |
|---|---|
| Tag | `e3` |
| Equipo | Gael Alexandro Cortez Sarmienta · Luis Alejandro Mendoza Peñaloza |
| Fecha de entrega | Lunes 30 de noviembre de 2026 |
| Relatoría | [`docs/relatoria-E3.md`](../relatoria-E3.md) |

> ⚠️ **BORRADOR (2026-11-24).** Los renglones marcados con ⏳ todavía no tienen evidencia. No se crea el tag `e3` hasta que la columna "Estado" esté completa.

Leyenda: ✔ hecho · ◐ parcial · ⏳ pendiente

---

## 1. Análisis Estadístico (unidad 5)

| Criterio | Puntos | Evidencia | Estado |
|---|---|---|---|
| Matriz multivariada (≥ 5 variables) y normalidad multivariada | 15 | 65 localidades × 8 variables, matrices de covarianzas y correlaciones, Mardia (asimetría y curtosis) y Q-Q de Mahalanobis: [`multivariado.md`](multivariado.md) §1–2, [`02_qq_mahalanobis.png`](multivariado/02_qq_mahalanobis.png) | ✔ |
| Componentes principales | 35 | PCA sobre correlaciones (estandarizado), sedimentación, varianza explicada, cargas y biplot. CP1 "Urbanización y acceso a psicólogos", CP2 "Vulnerabilidad del hogar": [`multivariado.md`](multivariado.md) §3–4, [`04_biplot.png`](multivariado/04_biplot.png) | ✔ |
| MANOVA | 25 | Wilks y Pillai para zona (2 grupos) y nivel de oferta (3 grupos), M de Box, permutación y por qué no es lo mismo que varios ANOVA: [`multivariado.md`](multivariado.md) §5 | ✔ |
| Mapa en el tablero | 15 | Pestaña del mapa en [`tablero/app.py`](../../tablero/app.py) con su interpretación para la cliente | ◐ local; ⏳ falta publicar el tablero en Streamlit Community Cloud y poner aquí el enlace |

**Reproducir:** `python src/multivariado.py` (unos 25 s). La prueba `test_multivariado_reproducible` comprueba el resultado.

## 2. Calidad en SI (temas 4.3 a 4.7)

| Criterio | Puntos | Evidencia | Estado |
|---|---|---|---|
| Cierre de la auditoría | 30 | `docs/E3/cierre-auditoria.md`: cada hallazgo recibido con su severidad, acción correctiva, commit de evidencia y estado | ⏳ **No hay reporte de la auditoría cruzada en el repo** |
| Modelos de proceso | 25 | Autoevaluación MoProSoft y CMMI con brechas concretas, y tabla comparativa de ISO 9001, MoProSoft, SPICE, CMMI y PSP/TSP: [`modelos-proceso.md`](modelos-proceso.md) | ✔ |
| Retrospectiva PSP | 25 | `docs/E3/retrospectiva-psp.md` con datos de `calidad/` | ⏳ Falta el PSP de Luis |
| Tendencias | 10 | Observabilidad de datos aplicada al observatorio: [`tendencias.md`](tendencias.md) | ✔ |
| Solicitud del Sello TDL | — | Sección 4 de esta ficha | ◐ |

## 3. Ingeniería de Datos (tema 4.2)

| Criterio | Puntos | Evidencia | Estado |
|---|---|---|---|
| Optimización medida | 50 | Antes y después en tiempo, memoria, errores y calidad: captura −59 % de tiempo y −100 % de descargas innecesarias; limpieza −26 % (Welch p = 0.0004); salida idéntica byte a byte: [`optimizacion.md`](optimizacion.md), [`optimizacion/mediciones.csv`](optimizacion/mediciones.csv) | ✔ |
| Dataset publicado | 40 | Capa Oro (`data/oro/`) con licencia CC BY 4.0 ([`data/oro/LICENCIA.md`](../../data/oro/LICENCIA.md)), datasheet completo ([`datasheet.md`](datasheet.md)) y diccionario de columnas | ◐ Confirmar que el repositorio (o una copia del dataset) sea **público**; si el repo es privado, el dataset no está "publicado" para terceros |
| Relatoría de etapa | 10 | [`docs/relatoria-E3.md`](../relatoria-E3.md) | ⏳ |

---

## 4. Solicitud del Sello TDL

| Criterio | Umbral | Valor medido | Evidencia | ¿Cumple? |
|---|---|---|---|---|
| Disponibilidad de la captura | ≥ 95 % en los últimos 14 días | ⏳ | `data/bitacora/capturas.csv` | ⏳ **No.** La captura diaria con bitácora empezó la semana del 23-nov; el 30-nov no habrá 14 días de historial. Se reporta el valor de los días disponibles y se declara la falta |
| Completitud de Oro (ISO/IEC 25012) | ≥ 95 % | 100 % | `data/oro/diccionario_oro.csv`, [`../E2/evaluacion-iso.md`](../E2/evaluacion-iso.md) | ✔ |
| Cobertura de pruebas | ≥ 60 % | 71 % (24-nov) | Job `pruebas` de `.github/workflows/ci.yml` (`--cov-fail-under=60`) | ✔ |
| Secretos expuestos | 0 | 0 | Job `secretos` (gitleaks) de la CI | ✔ |
| Hallazgos críticos de auditoría abiertos | 0 | ⏳ | `docs/E3/cierre-auditoria.md` | ⏳ |
| Reproducibilidad | Un tercero clona y obtiene lo mismo | Oro idéntico (tolerancia 1e-9) | `test_reproducibilidad`, [`../../COMO-EJECUTAR.md`](../../COMO-EJECUTAR.md) | ✔ |

## 5. Lista de revisión antes del tag (de `docs/plan-sqa.md` §5)

- [ ] La CI está en verde en el commit del tag.
- [ ] No hay archivos de Bronce modificados a mano.
- [ ] Hay una entrada nueva en el PSP de cada integrante.
- [ ] Todas las rutas de esta ficha existen.
- [ ] No hay datos personales.
- [ ] No hay credenciales.
- [ ] Revisó esta ficha el integrante que no la escribió: ________
