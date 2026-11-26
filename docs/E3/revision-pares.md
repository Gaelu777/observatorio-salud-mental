# Revisión entre pares — E3

**Revisor:** Luis Alejandro Mendoza Peñaloza (revisor SQA de E3, `docs/plan-sqa.md` §2)
**Fecha:** 2026-11-26
**Veredicto:** **Aprobado con cambios**

## Alcance y referencias revisadas

- Diferencia `main...origin/calidad-e3`: `README.md`, `docs/E3/ENTREGA.md` y `docs/E3/modelos-proceso.md`. Referencias: `main` en `2e1a6b2` y `origin/calidad-e3` en `4a94ad5`.
- Commit `914774e90ed86e9362cd0db2135d85c05c206e77`: `src/extraer_denue.py` y `tests/test_pipeline.py`.
- Lista de revisión de `docs/plan-sqa.md` §5 y criterios de Calidad de la rúbrica E3 del PDF del proyecto.

La rama `origin/calidad-e3` parte de `bd0ff0f` y no contiene seis commits posteriores de `main`, entre ellos `914774e` y la corrida exitosa `160bf78`. La diferencia solicitada se revisó tal cual; no se integraron ni reescribieron cambios de Gael.

## Observaciones

### R1 — Criterios de entrega y checklist pendientes

- **Archivo:** `docs/E3/ENTREGA.md`
- **Severidad:** Mayor
- **Evidencia y razón:** La propia ficha deja pendientes el cierre de auditoría, la retrospectiva PSP del revisor, la relatoría E3, la publicación pública del dataset, la publicación del tablero y la medición de disponibilidad. En la referencia revisada no existen `docs/E3/cierre-auditoria.md`, `docs/E3/retrospectiva-psp.md` ni `docs/relatoria-E3.md`; `calidad/tiempo-luis-mendoza.csv` solo contiene el encabezado. La lista §5 permanece sin marcar. La rúbrica E3 requiere el cierre documentado de auditoría y cero hallazgos críticos abiertos.
- **Recomendación:** Completar y enlazar los entregables faltantes, sustituir el reporte cruzado no recibido por la auditoría interna acordada, registrar ambos PSP y actualizar cada estado únicamente cuando exista evidencia. No crear el tag mientras queden requisitos pendientes.

### R2 — Rama E3 desactualizada respecto de `main`

- **Archivo:** `docs/E3/ENTREGA.md` (referencia de la rama revisada)
- **Severidad:** Mayor
- **Evidencia y razón:** `origin/calidad-e3` está basada en `bd0ff0f`; `main` avanzó seis commits, incluido el arreglo DENUE `914774e` y la corrida correcta `160bf78`. Por ello, la ficha E3 aún no incorpora la evidencia posterior sobre la falla y recuperación de captura.
- **Recomendación:** Sincronizar la rama de trabajo con el `main` actualizado y volver a verificar la ficha, los archivos enlazados y la CI antes del tag. Esta revisión no hace esa integración.

### R3 — Falta una prueba de compatibilidad con encabezados históricos

- **Archivo:** `tests/test_pipeline.py`
- **Severidad:** Menor
- **Evidencia y razón:** Las pruebas añadidas cubren encabezados nuevos en mayúsculas y el error ante columnas requeridas ausentes. No ejercitan explícitamente la compatibilidad con los encabezados históricos mezclados, que `normalizar_columnas` también pretende mantener.
- **Recomendación:** Añadir un caso de regresión con encabezados del esquema histórico (`tipoCenCom`, `ageb` y `manzana`) y comprobar que la normalización conserva los nombres que espera Plata.

## Revisión del arreglo DENUE (`914774e`)

`normalizar_columnas` convierte los encabezados a minúsculas, aplica los renombres conocidos y valida columnas requeridas antes del filtrado y la escritura. El cambio conserva el descarte de columnas personales existente. Las dos pruebas nuevas cubren el formato reportado por INEGI y un error de esquema comprensible. No encontré un defecto funcional comprobable en el cambio.

## Lista SQA §5

| Criterio | Resultado | Evidencia |
|---|---|---|
| CI en verde | Cumple para las referencias revisadas | CI `4a94ad5`: éxito; CI de `914774e`: éxito; CI de `2e1a6b2`: éxito. |
| Bronce no modificado a mano | Cumple en la diferencia revisada | `main...origin/calidad-e3` no modifica `data/bronce/`; `914774e` modifica solo código y pruebas. |
| Entrada PSP de cada integrante | No cumple en `origin/calidad-e3` | El CSV PSP de Luis contiene solo encabezado; el de Gael sí contiene registros. |
| Rutas de la ficha existentes | No cumple | Faltan los tres archivos señalados en R1. |
| Sin datos personales | Cumple en los cambios revisados | El arreglo DENUE elimina las columnas personales antes de guardar; los documentos nuevos no incluyen datos de pacientes ni identificadores personales. |
| Sin credenciales | Cumple en los cambios revisados | No se encontraron credenciales en las diferencias inspeccionadas. |

**Verificaciones externas:** CI de `origin/calidad-e3` (`4a94ad5`) y de `914774e` concluyeron con éxito; el pipeline manual del 2026-11-26 a las 06:37 UTC también concluyó con éxito. La CI de `main` en `2e1a6b2` está verde.

**Conclusión:** el arreglo DENUE se aprueba funcionalmente. La revisión de la entrega E3 queda **aprobada con cambios** por R1 y R2, que deben resolverse antes de considerar completa la ficha o crear el tag.
