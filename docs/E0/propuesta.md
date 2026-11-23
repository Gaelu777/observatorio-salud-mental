# Propuesta del Observatorio de Salud Mental — Colima

**Equipo:** Gael Alexandro Cortez Sarmienta · Luis Alejandro Mendoza Peñaloza
**Repositorio:** https://github.com/Gaelu777/observatorio-salud-mental
**Entrega:** E0 (tag `e0`)

---

## 1. Ficha del observatorio

| Campo | Definición |
|---|---|
| **Sector** | Servicios de salud: atención psicológica privada (SCIAN 621331 *Consultorios de psicología del sector privado*). |
| **Región** | Estado de Colima, con foco en el municipio de Colima (zona centro de la ciudad) y su zona conurbada con Villa de Álvarez. |
| **Pregunta detonadora** | *¿Cómo evoluciona la necesidad de atención en salud mental en Colima a lo largo del tiempo, y en qué zonas del estado hay menos oferta de consultorios de psicología respecto a esa necesidad?* |
| **Cliente potencial** | Una psicóloga que atiende en un consultorio compartido con otros psicólogos en la zona centro de Colima. Necesita saber: (a) en qué meses o temporadas se espera más necesidad de atención, (b) cuánta competencia hay cerca de su consultorio y (c) en qué municipios hay poca oferta, para decidir si le conviene abrir horarios, atender a distancia o abrir otra sede. |

**Por qué este enfoque.** No existen datos públicos de "consultas psicológicas privadas por mes". Por eso el observatorio usa **indicadores públicos de necesidad** (mortalidad por suicidio y por trastornos mentales, registrada por INEGI) y **oferta** (consultorios registrados en DENUE). Es un *proxy*: no mide directamente cuántas personas buscan terapia, pero sí la carga de salud mental en la población. Esta limitación se declara en cada hallazgo.

---

## 2. Entrevista de campo

> **Estado: PENDIENTE.** La entrevista (mínimo 15 minutos) se hará con la psicóloga cliente. En este documento solo se registra lo que ella diga **sobre el sector**; no se registra ningún dato de sus pacientes, ni siquiera anonimizado.

- **Fecha:** _pendiente_
- **Duración:** _pendiente (≥ 15 min)_
- **Medio:** _pendiente (presencial / videollamada)_
- **Entrevistada:** psicóloga con consultorio en la zona centro de Colima (se omite su nombre por privacidad).

### Preguntas y respuestas

| # | Pregunta | Qué valida | Respuesta (resumen) |
|---|---|---|---|
| 1 | ¿En qué meses o épocas del año nota que llegan más personas a pedir atención, y en cuáles menos? | Estacionalidad → variable a pronosticar (E1) y factor "temporada" (E2) | _pendiente_ |
| 2 | ¿Qué motivos de consulta son los más comunes hoy (ansiedad, depresión, duelo, pareja, etc.) y han cambiado en los últimos años? | Qué indicador de necesidad tiene sentido seguir | _pendiente_ |
| 3 | ¿Qué perfil de personas busca más atención (edad, sexo, si vienen de otros municipios)? | Factores "sexo", "edad" y "municipio" (E2) | _pendiente_ |
| 4 | ¿Cómo percibe la competencia en el centro de Colima? ¿Hay zonas del estado donde sabe que casi no hay psicólogos? | Grupos a comparar: oferta por municipio (E3) | _pendiente_ |
| 5 | Si tuviera un tablero con datos públicos, ¿qué decisión le ayudaría a tomar (horarios, precios, abrir sede, atención en línea)? | Valida que el observatorio le sirve a la cliente | _pendiente_ |

### Aprendizajes

_Pendiente. Escribir 3 a 5 aprendizajes concretos y, para cada uno, si **confirma** o **cambia** algo de las preguntas analíticas de la sección 3._

---

## 3. Las 3 preguntas analíticas

### E1 — Variable a pronosticar
**¿Cuántas defunciones por lesiones autoinfligidas (suicidio) de residentes del estado de Colima se esperan por mes en los próximos 12 meses?**

- **Variable:** conteo mensual de defunciones con causa básica CIE-10 **X60–X84**, residencia en Colima (`ent_resid = 06`), por mes de ocurrencia.
- **Serie disponible:** enero 2018 – diciembre 2023 = **72 periodos mensuales** (el mínimo pedido es 36). Ya descargada en `data/bronce/inegi_defunciones/`.
- **Variable complementaria:** defunciones con causa en el capítulo F (trastornos mentales y del comportamiento).
- **Reto conocido:** los conteos son bajos (entre 0 y 13 por mes), así que el pronóstico tendrá intervalos amplios. Se evaluará agregar por trimestre como técnica de reducción de datos.
- **Uso para la cliente:** anticipar los meses de mayor riesgo para reforzar la disponibilidad o las campañas de prevención.

### E2 — Factores a experimentar
**¿La incidencia mensual cambia según la temporada, el sexo, el grupo de edad y la zona de residencia?**

| Factor | Niveles |
|---|---|
| Temporada | Trimestre del año (T1–T4); también vacaciones/fiestas de diciembre vs. resto |
| Sexo | Hombre / Mujer |
| Grupo de edad | 0–14, 15–24, 25–59, 60+ (cortes compatibles con el Censo 2020 para poder calcular tasas) |
| Zona | Zona conurbada Colima–Villa de Álvarez vs. resto del estado |

Los datos son observacionales, no un experimento controlado. Se analizarán como diseño factorial (conteos por combinación de niveles) y se declarará que no se puede afirmar causalidad.

### E3 — Grupos multivariados a comparar
**¿Qué municipios de Colima tienen mucha necesidad de salud mental y poca oferta de consultorios de psicología?**

- **Unidades:** los 10 municipios del estado.
- **Variables por municipio:** consultorios de psicología por cada 100 mil habitantes (DENUE + población del Censo 2020), tasa de suicidio por 100 mil, tasa de defunciones por trastornos mentales, % de consultorios públicos vs. privados, y número de consultorios a 500 m, 1 km y 2 km del centro de Colima (competencia directa de la cliente).
- **Comparación:** agrupar los municipios (p. ej. "alta necesidad / baja oferta") y comparar los grupos con varias variables a la vez.
- **Dato inicial:** DENUE registra **117 consultorios de psicología** en el estado; **62** están en el municipio de Colima y 20 en Villa de Álvarez (descarga del 23-nov-2026). La oferta está muy concentrada en la capital.

---

## 4. Plan de recopilación de datos

Solo se usan **fuentes oficiales** y descargas públicas que **no requieren token** ni registro.

| # | Fuente | Qué aporta | Formato / periodicidad | Uso |
|---|---|---|---|---|
| F1 | **INEGI — Estadística de Defunciones Registradas (EDR), datos abiertos** | Registro de cada defunción (sin nombres): causa CIE-10, sexo, edad, municipio de residencia y ocurrencia, mes | ZIP con CSV, anual (2018–2023 disponibles) | E0 (serie ≥36), E1, E2, E3 |
| F2 | **INEGI — DENUE, descarga masiva Colima** | Establecimientos con actividad SCIAN, coordenadas y municipio | ZIP con CSV, actualización semestral aprox. | E2 (geoespacial), E3 |
| F3 | **INEGI — Censo de Población y Vivienda 2020, ITER Colima** (se incorporó en E1; CONAPO no tenía descargas que funcionaran) | Población por municipio, sexo y edad | CSV, fijo 2020 | Calcular tasas por 100 mil habitantes |
| F4 | **INEGI — Marco Geoestadístico 2020, Colima** (E2) | Polígonos de los 10 municipios | Shapefile, fijo 2020 | Mapas y validación espacial |

### 4.1 Análisis ético y legal

**robots.txt de inegi.org.mx** (copia guardada en `docs/E0/evidencia/robots_inegi_2026-11-23.txt`):
- Permite explícitamente `/contenidos/programas` (ruta de F1).
- `/contenidos/masiva` (ruta de F2) no está prohibida. Solo se prohíben rutas del catálogo de microdatos (`/catalog/...`, `/metadata/...`) y de registro (`/auth/register/`), que **no** se usan.

**Términos de uso:** la información de INEGI se publica bajo los *Términos de Libre Uso de la Información del INEGI*. Permiten copiar, distribuir y adaptar los datos, incluso con fines comerciales, siempre que **se cite la fuente** y no se dé a entender que INEGI respalda el trabajo. El observatorio cita la fuente en cada archivo derivado. Las cuatro fuentes son de INEGI, así que aplican los mismos términos.

**Privacidad:**
- F1 no contiene nombres ni identificadores directos; INEGI la publica anonimizada. Aun así, en Colima hay pocos casos por mes en municipios pequeños, así que **los resultados se publican solo agregados** (nunca registros individuales en tablas o gráficas) y se suprimen celdas con menos de 3 casos en cruces muy detallados.
- F2 sí puede contener datos personales, porque muchos consultorios están a nombre de una persona física. El extractor **elimina nombre, razón social, teléfono, correo y web antes de guardar** (`src/extraer_denue.py`).
- No se usa ningún dato de la cliente ni de sus pacientes.

**Extracción responsable:** User-Agent identificable sin datos personales, pausa de 5 s entre descargas, solo una ejecución al mes y no se vuelve a descargar lo que no cambió (comparación de hash SHA-256).

**Por qué no Google Trends:** no tiene API pública oficial estable. Las librerías existentes extraen datos de forma no oficial, se bloquean desde servidores como los de GitHub Actions y no cumplirían un análisis ético limpio.

### 4.2 Máquina de captura (capa Bronce)

- `src/extraer_defunciones.py` y `src/extraer_denue.py`, ejecutados por `.github/workflows/extraccion-bronce.yml` el día 5 de cada mes y a demanda.
- Bronce guarda los registros **tal cual** vienen de INEGI (todo como texto, sin limpiar; p. ej. los tabuladores pegados a los valores en 2018–2019 se conservan para limpiarlos en Plata). Solo se seleccionan las filas de Colima y, en DENUE, se quitan las columnas personales.
- `data/bronce/manifiesto.csv` registra el linaje de cada archivo: URL de origen, fecha de ingesta (UTC), hash SHA-256 del ZIP original y número de registros.

---

## 5. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| INEGI cambia rutas de descarga (ya pasó: la ruta `microdatos/` dejó de existir) | El extractor valida que la respuesta sea un ZIP y falla de forma visible; la alerta queda en Actions |
| Conteos mensuales bajos → pronóstico poco preciso | Agregación trimestral y variable complementaria (capítulo F) |
| Retraso de publicación (INEGI publica el año *t* hacia finales de *t+1*) | El workflow revisa cada mes y agrega el año nuevo en cuanto aparece |
| El indicador es un proxy de necesidad, no de demanda de consulta | Se declara en cada hallazgo y se contrasta con la entrevista |
