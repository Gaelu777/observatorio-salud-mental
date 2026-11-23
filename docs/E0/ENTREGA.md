# Ficha de entrega técnica — E0

| Campo | Valor |
|---|---|
| Tag | `e0` |
| Equipo | Gaelu777 · Luis Alejandro Mendoza Peñaloza |
| Región | Estado de Colima (foco: zona centro del municipio de Colima) |

## Checklist contra la rúbrica

| # | Entregable | Ubicación | Estado |
|---|---|---|---|
| 1 | Propuesta (ficha, entrevista, 3 preguntas, plan de datos) | `docs/E0/propuesta.md` | Completa, **excepto la entrevista (pendiente)** |
| 2a | Extractor ético automático con GitHub Actions | `src/extraer_defunciones.py`, `src/extraer_denue.py`, `.github/workflows/extraccion-bronce.yml` | Listo |
| 2b | Serie histórica cruda ≥ 36 periodos | `data/bronce/inegi_defunciones/` (2018-01 a 2023-12 = 72 meses) | Listo |
| 3a | Registros PSP por integrante | `calidad/tiempo-*.csv`, `calidad/defectos-*.csv` | Abiertos |
| 3b | 3 objetivos de calidad medibles | `calidad/README.md` | Listo |
| 4 | Ficha técnica | este archivo | Listo |

## Cómo reproducir

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python src/extraer_denue.py
python src/extraer_defunciones.py          # todos los años disponibles
python src/extraer_defunciones.py 2018 2023  # o un rango
```

La ejecución automática corre el día 5 de cada mes. Para lanzarla a mano: pestaña **Actions → Extraccion Bronce → Run workflow**.

## Datos en Bronce (ingesta inicial 2026-11-23)

| Fuente | Archivo(s) | Registros |
|---|---|---|
| INEGI EDR 2018–2023 | `data/bronce/inegi_defunciones/defunciones_colima_registradas_<año>.csv` | 37,136 en total (residencia u ocurrencia en Colima) |
| INEGI DENUE | `data/bronce/inegi_denue/denue_colima_scian621_20261123.csv` | 1,649 establecimientos SCIAN 621, 117 de psicología |

El linaje (URL, fecha de ingesta, SHA-256 del original y registros) está en `data/bronce/manifiesto.csv`.

## Decisiones técnicas

- **Fuentes oficiales sin token:** INEGI publica descargas masivas abiertas, así que no hace falta guardar secretos en Actions.
- **Filtro de filas en Bronce:** el archivo nacional pesa unos 230 MB por año. Se guardan solo las filas de Colima, con valores idénticos al original. El hash del ZIP completo permite verificarlo.
- **Minimización en DENUE:** se eliminan nombre, razón social, teléfono, correo y web antes de escribir a disco (datos personales de personas físicas).
- **Idempotencia:** si el hash del archivo de origen no cambió, no se vuelve a ingerir. Así se evitan commits duplicados del bot.
- **Año de registro vs. año de ocurrencia:** cada archivo anual de INEGI agrupa las defunciones *registradas* ese año, e incluye algunas que ocurrieron en años anteriores. La serie se arma por **fecha de ocurrencia** en la capa Plata (E1).

## Pendientes conocidos

- Hacer la entrevista de campo y llenar la sección 2 de la propuesta.
- Confirmar el número de profesores colaboradores (la rúbrica dice 3).
