# Declaración de Ética y Legalidad de Datos

**Observatorio de Salud Mental — Colima**
**Equipo:** Gael Alexandro Cortez Sarmienta · Luis Alejandro Mendoza Peñaloza
**Fecha de revisión:** 23 de noviembre de 2026

## 1. Fuentes y términos de uso

| Fuente | Productor | Acceso | Licencia / términos |
|---|---|---|---|
| Estadística de Defunciones Registradas (datos abiertos) | INEGI | Descarga pública, sin registro ni token | Términos de Libre Uso de la Información del INEGI |
| DENUE, descarga masiva Colima | INEGI | Descarga pública, sin registro ni token | Términos de Libre Uso de la Información del INEGI |
| Censo de Población y Vivienda 2020, ITER Colima | INEGI | Descarga pública, sin registro ni token | Términos de Libre Uso de la Información del INEGI |
| Marco Geoestadístico 2020, Colima | INEGI | Descarga pública, sin registro ni token | Términos de Libre Uso de la Información del INEGI |

**Qué permiten los Términos de Libre Uso del INEGI:** copiar, distribuir, publicar, adaptar y explotar la información, incluso con fines comerciales, con dos condiciones:

1. **Citar la fuente**: "Fuente: INEGI, <nombre del producto>". Se hace en el `README.md`, en cada mapa y en los reportes.
2. **No dar a entender que INEGI respalda el trabajo.** El `README.md` lo aclara explícitamente.

**Cómo se cumple:** los datos se usan para un proyecto académico, con atribución en cada salida y sin modificar el significado de la información original. Las transformaciones quedan documentadas y son reversibles gracias al linaje.

## 2. Análisis de robots.txt

Copia fechada: `docs/E0/evidencia/robots_inegi_2026-11-23.txt`.

| Ruta usada | Regla en robots.txt | Veredicto |
|---|---|---|
| `/contenidos/programas/edr/datosabiertos/...` (defunciones) | `Allow: /contenidos/programas` | Permitida explícitamente |
| `/contenidos/programas/ccpv/2020/datosabiertos/...` (Censo) | `Allow: /contenidos/programas` | Permitida explícitamente |
| `/contenidos/productos/.../marcogeo/...` (Marco Geoestadístico) | `Allow: /contenidos/productos` | Permitida explícitamente |
| `/contenidos/masiva/denue/...` (DENUE) | No aparece en `Allow` ni en `Disallow` | Permitida: lo que no se prohíbe está permitido, y es el enlace oficial de "Descarga masiva" |

Las rutas prohibidas (`/catalog/*/download/*`, `/metadata/export_variable/...`, `/auth/register/`) **no se usan**.

**Conducta del extractor:**
- User-Agent identificable (`observatorio-salud-mental-colima/0.1 (proyecto academico; datos abiertos INEGI)`), sin datos personales.
- Pausa de 5 segundos entre descargas y reintentos con espera creciente.
- Una ejecución al mes. No se vuelve a ingerir un archivo cuyo hash SHA-256 no cambió, y los productos fijos (Marco Geoestadístico) ni siquiera se vuelven a descargar.
- No se hace scraping de páginas HTML: solo se descargan los archivos publicados para descarga.

**Fuente descartada por motivos éticos:** Google Trends no tiene API pública oficial estable. Las librerías existentes extraen datos de forma no autorizada, así que no se usó.

## 3. Privacidad

**Principio:** el observatorio solo publica **datos públicos y agregados**. No contiene ni contendrá datos de la cliente ni de sus pacientes.

| Riesgo | Fuente | Medida |
|---|---|---|
| Nombres, razón social, teléfono, correo y web de consultorios de **personas físicas** | DENUE | Se **eliminan antes de escribir a disco** en Bronce (`src/extraer_denue.py`). Nunca existen en el repositorio |
| Reidentificación de personas fallecidas en municipios pequeños (cruce de edad + sexo + municipio + fecha) | Defunciones | INEGI ya publica sin nombres ni direcciones. El análisis **solo publica conteos agregados** (por mes, trimestre o municipio), nunca registros individuales en reportes o gráficas |
| Celdas muy pequeñas en tablas cruzadas | `factores_suicidio.csv` | La tabla existe para el análisis interno de E2/E3. En presentaciones públicas se suprimen las celdas con menos de 3 casos |
| Revelar la ubicación del consultorio de la cliente | Mapas | El punto de referencia es un lugar público (Jardín Libertad), **no** su domicilio. Su consultorio no se marca |
| Información sensible del tema (suicidio) | Todas | Se reporta con lenguaje neutral, sin detalles de método y siempre en tasas o conteos |
| Credenciales | Repositorio | No se necesitan: todas las fuentes son abiertas. Si se agregara una API, el token iría en `.env` (ignorado por git) o en GitHub Secrets |

Los datos de defunciones no son datos personales en el sentido de la Ley Federal de Protección de Datos Personales: se refieren a personas fallecidas y están anonimizados por INEGI. Aun así, se tratan con el mismo cuidado por el riesgo de reidentificación en poblaciones pequeñas.

## 4. Sesgos y limitaciones (y cómo se mitigan)

| Sesgo | Efecto | Mitigación |
|---|---|---|
| **Proxy de necesidad, no de demanda:** la mortalidad por suicidio y por trastornos mentales no mide cuántas personas buscan terapia | Se podría confundir "riesgo" con "clientes potenciales" | Se declara en cada hallazgo; se contrasta con la entrevista a la psicóloga |
| **Subregistro:** algunas muertes por suicidio se certifican como accidente o causa indeterminada | La serie subestima la necesidad real | Se usa la causa CIE-10 certificada (estándar OMS) y se compara con `tipo_defun`: coinciden en 327 de 327 casos |
| **Registro tardío:** las defunciones de un año se siguen registrando en los años siguientes | El último año (2023) está ligeramente subcontado (~0.5 % según años anteriores) | Se mide y se declara; el workflow agrega años nuevos en cuanto INEGI los publica |
| **Faltantes no aleatorios (MAR/MNAR):** el mes falta más en muertes violentas | Imputar mal desplazaría casos entre meses | Hot-deck condicional por grupo de causa (ver `docs/E1/reporte_limpieza.md`) |
| **DENUE incompleto:** psicólogos que atienden en casa, en línea o sin registro no aparecen | La oferta real es mayor, sobre todo en municipios pequeños | Se presenta como "oferta registrada" y se pregunta a la cliente por la oferta informal |
| **Desfase temporal:** población 2020, oferta 2026, defunciones 2018–2023 | Las tasas mezclan momentos distintos | Se declara; 2020 es el punto medio del periodo de defunciones |
| **Áreas pequeñas:** municipios de 5 a 10 mil habitantes tienen tasas muy variables | Un solo caso cambia mucho la tasa | Advertencia en mapas y reporte; suavizado de tasas antes de comparar grupos |
| **Sesgo de la cliente:** el observatorio se diseña para una sola psicóloga del centro de Colima | Las conclusiones pueden no aplicar a otros perfiles | Las tablas se publican completas por municipio para que cualquiera pueda reinterpretarlas |

## 5. Trazabilidad

Cada fila de la capa Oro puede rastrearse hasta el archivo y la fila exacta de Bronce, su fecha de ingesta y la URL y hash del archivo original. La verificación es automática (`src/verificar_linaje.py`) y el pipeline se detiene si falla. Ver `docs/E2/ENTREGA.md`.

## 6. Compromisos

- No se agregarán fuentes con datos personales identificables ni de redes sociales a nivel individuo.
- No se usarán datos del sistema de gestión del consultorio de la cliente.
- Si INEGI cambia sus términos o su robots.txt, se revisará esta declaración antes de la siguiente extracción.
