# E3 · Calidad: nuestro proceso frente a MoProSoft y CMMI

Autoevaluación del equipo (2 integrantes) con la evidencia que hay **en este repositorio** al 2026-11-24.
Regla que seguimos: un nivel solo se reclama si hay un archivo, commit o corrida que lo demuestre. Si la práctica se hace "de palabra" pero no deja rastro, cuenta como **no realizada**.

Escala de capacidad usada (la de ISO/IEC 15504 / 33020, que es la que adopta MoProSoft):

| Nivel | Nombre | Qué significa para nosotros |
|---|---|---|
| 0 | Incompleto | No se hace, o se hace sin producir sus productos de trabajo |
| 1 | Realizado | Se hace y produce sus productos, aunque sea sin plan |
| 2 | Gestionado | Se planea, se le da seguimiento y sus productos se revisan y controlan |
| 3 | Establecido | Sigue un proceso definido y documentado que se reutiliza entre proyectos |
| 4 | Predecible | Se mide y se controla con límites cuantitativos |
| 5 | Optimizado | Se mejora de forma continua con base en las mediciones |

---

## 1. MoProSoft (NMX-I-059-NYCE)

MoProSoft organiza los procesos en **3 categorías**: Alta Dirección, Gerencia y Operación. Está pensado para empresas pequeñas de software en México; nosotros somos un equipo de 2 dentro de un curso, así que algunos procesos casi no aplican. Lo decimos en cada caso en lugar de forzarlo.

### 1.1 Evaluación por proceso

| Categoría | Proceso | ¿Aplica? | Evidencia en el repo | Nivel | Qué falta para subir |
|---|---|---|---|---|---|
| Alta Dirección | **DIR.1 Gestión de Negocio** | Parcial | Cliente identificada y pregunta de negocio en `docs/E0/propuesta.md` | **1** | Plan estratégico y modelo de negocio (quién paga y cuánto): es entregable de E4. La entrevista con la cliente todavía no está documentada |
| Gerencia | **GES.1 Gestión de Procesos** | Sí | `docs/plan-sqa.md` define el flujo: rama → CI → revisión → tag | **1** | El proceso está escrito, pero no hay evidencia de que se haya **medido ni ajustado**. La revisión entre pares que define el plan no tiene registros |
| Gerencia | GES.2 Gestión de Proyectos (cartera) | No | Es un solo proyecto | N/A | — |
| Gerencia | **GES.3 Gestión de Recursos** (humanos, infraestructura, conocimiento) | Parcial | Infraestructura: GitHub Actions y dependencias fijadas en `requirements.txt`. Conocimiento: `COMO-EJECUTAR.md`, relatorías, `docs/` | **1** | Roles confirmados (la tabla de roles del plan SQA es una propuesta); reparto real del trabajo (sección 6 de las relatorías dice `_completar_`) |
| Operación | **OPE.1 Administración de Proyectos Específicos** | Sí | Calendario de la rúbrica; riesgos en `docs/plan-sqa.md` §9; acciones correctivas en `calidad/defectos-*.csv`; lecciones en las relatorías | **1** | **Plan del proyecto con estimaciones propias** (no hay); reportes de seguimiento periódicos (el archivo de pendientes es local y no se versiona); revisar los riesgos durante el proyecto, no solo listarlos |
| Operación | **OPE.2 Desarrollo y Mantenimiento de Software** | Sí | Ver la tabla 1.2 | **2 (parcial)** | Documento de diseño y reporte de pruebas archivado por entrega |

### 1.2 OPE.2 en detalle: los productos que pide MoProSoft

OPE.2 es el proceso más fuerte del equipo, porque la rúbrica técnica empuja a producir casi todos sus productos.

| Producto de OPE.2 | ¿Existe? | Dónde |
|---|---|---|
| Especificación de requerimientos | ✔ | `docs/requerimientos.md` (RF y RNF verificables, con origen y prueba) |
| Bitácora de trazabilidad | ✔ | Columnas "Implementado en" y "Cómo se comprueba" de `docs/requerimientos.md`; linaje de datos en `data/oro/linaje_oro.csv` |
| Análisis y diseño | ◐ | Las decisiones están justificadas (Pandera vs. Great Expectations, IQR vs. Z, unidad de análisis de E3), pero repartidas en varios documentos. No hay un documento de arquitectura |
| Componentes (código) | ✔ | `src/`, `tablero/` |
| Plan de pruebas | ◐ | `docs/plan-sqa.md` §5 lista los niveles de prueba, pero no los casos con entrada y salida esperada |
| Reporte de pruebas | ◐ | Solo existe en los logs de la CI de GitHub, que caducan. No se guarda un reporte por entrega |
| Configuración del software | ✔ | Git, un tag por entrega, dependencias con versión exacta, Bronce inmutable |
| Manual de usuario / de operación | ✔ | `COMO-EJECUTAR.md`, `README.md`, `docs/E3/datasheet.md` |

**Por qué decimos "2 parcial" y no 2:** los productos existen y la CI los verifica en cada push (eso es *controlado*), pero el nivel 2 también pide que se **revisen** antes de liberarse, y la revisión por el otro integrante no deja evidencia.

### 1.3 Resultado MoProSoft

El equipo opera en **nivel de capacidad 1** en casi todos los procesos aplicables, con **OPE.2 cerca del nivel 2**. Lo que nos separa del nivel 2 no es técnico, es de **gestión**: planear con estimaciones, dar seguimiento por escrito y dejar evidencia de las revisiones.

---

## 2. CMMI (áreas de práctica que aplican al equipo)

Usamos las áreas de práctica de CMMI v2.0/v3.0. CMMI tiene niveles de **madurez** de la organización (1 Inicial, 2 Gestionado, 3 Definido, 4 Gestionado cuantitativamente, 5 En optimización) y niveles de **capacidad** por área. Para el nivel de madurez 2 hay que tener **todas** las áreas de ese nivel en capacidad 2.

| Área de práctica | Evidencia | Capacidad | Brecha concreta |
|---|---|---|---|
| **CM** Gestión de la configuración | Git, tags `e1` y `e2`, `requirements.txt` fijado, Bronce inmutable con SHA-256 | **2** | Los tags `e0` y `e3` no existen todavía; `e1` quedó en un commit viejo y el trabajo de E1 se terminó después |
| **VV** Verificación y validación | 3 archivos de pruebas, cobertura 71 %, prueba de reproducibilidad, puerta Pandera, verificación de linaje 652/652 | **2** | La validación con la **cliente** (¿le sirve?) no ha ocurrido: depende de la entrevista |
| **RDM** Desarrollo y gestión de requerimientos | `docs/requerimientos.md` con 8 RF y 10 RNF verificables y rastreables | **2** | Los requerimientos vienen de la rúbrica, no de la cliente. Falta confirmarlos con ella |
| **TS** Solución técnica | Alternativas comparadas y decisión justificada en cada etapa (por ejemplo, Pandera vs. GE en `plan-sqa.md` §7; localidades vs. municipios en `multivariado.md` §0) | **2** | — |
| **PI** Integración del producto | Pipeline completo Bronce → Plata → Oro → tablero en un workflow | **2** | — |
| **PQA** Aseguramiento de la calidad del proceso | `docs/plan-sqa.md` con lista de revisión antes del tag | **1** | Nadie ha llenado la lista de revisión; no hay registro de que se haya aplicado |
| **PR** Revisiones entre pares | La regla "nadie aprueba su propio trabajo" está escrita | **0** | **No hay pull requests revisados por el otro integrante.** Hoy el mismo autor hace el merge a `main` |
| **CAR** Análisis causal y resolución | `calidad/defectos-gael-cortez.csv` registra el defecto que originó cada defecto (columna `defecto_origen`); el D11 se descubrió con el experimento | **1** | No se ha hecho un análisis de causas por tipo de defecto (se hará en la retrospectiva PSP) |
| **MPM** Medición y análisis del desempeño | Optimización medida antes y después (`docs/E3/optimizacion.md`), PSP de Gael, métricas ISO 25010/25012 | **1** | PSP de Luis vacío; la bitácora de capturas aún no tiene registros en `main`; no hay metas cuantitativas que se revisen |
| **PLAN** Planeación | Solo el calendario de la rúbrica | **1** | Plan propio con tareas, responsables y fechas |
| **EST** Estimación | — | **0** | **El registro de tiempo PSP no tiene columna de estimado**, así que no se puede medir la exactitud de las estimaciones |
| **MC** Monitoreo y control | Relatorías de etapa (al cierre, no durante) | **1** | Seguimiento durante la etapa (por ejemplo, issues de GitHub con responsable y fecha) |
| **RSK** Gestión de riesgos | Tabla de 5 riesgos en `docs/plan-sqa.md` §9 | **1** | Revisar la tabla en cada entrega; el riesgo "trabajo concentrado en un integrante" ya se está materializando y no tiene acción |

### Resultado CMMI

**Nivel de madurez 1 (Inicial).** Cinco áreas técnicas (CM, VV, RDM, TS, PI) ya están en capacidad 2, pero las de gestión (PLAN, EST, MC, PR, PQA) no. Es el patrón típico de un equipo pequeño: la ingeniería está más madura que la administración.

---

## 3. Brechas priorizadas y qué vamos a hacer

Ordenadas por lo que cuesta cerrarlas contra lo que suben el nivel.

| # | Brecha | Modelo y área | Acción | Cuándo | Estado |
|---|---|---|---|---|---|
| B1 | No hay revisión entre pares con evidencia | CMMI PR, PQA · MoProSoft GES.1 | Cada cambio a `main` entra por pull request **aprobado por el otro integrante**; activar la protección de rama que exige 1 aprobación | Antes del tag `e3` | Abierta |
| B2 | PSP sin estimaciones | CMMI EST · PSP | Agregar la columna `estimado_min` a `calidad/tiempo-*.csv` y estimar **antes** de empezar cada tarea | Desde E4 | Abierta |
| B3 | PSP de Luis vacío | CMMI MPM · PSP | Luis reconstruye su registro con las fechas de sus commits y su trabajo | 25-nov | Abierta |
| B4 | Seguimiento solo al cierre de la etapa | CMMI MC · MoProSoft OPE.1 | Issues de GitHub con responsable y fecha para cada pendiente de E3 y E4 | Esta semana | Abierta |
| B5 | Requerimientos no validados con la cliente | CMMI RDM, VV · MoProSoft DIR.1 | Validar en la entrevista los 3 hallazgos y los RF-06 y RF-07 | 25-nov | Abierta |
| B6 | No se guarda el reporte de pruebas | MoProSoft OPE.2 | Guardar la salida de `pytest --cov` en `docs/E<n>/` antes de cada tag | Antes del tag `e3` | Abierta |
| B7 | Roles y reparto de trabajo sin confirmar | MoProSoft GES.3 | Llenar la sección 6 de las relatorías y confirmar la tabla de roles del plan SQA | Antes del tag `e3` | Abierta |

Si se cierran B1, B2, B4 y B7, las áreas PR, EST, MC y PQA pueden llegar a capacidad 2, y el equipo quedaría cerca del nivel de madurez 2.

---

## 4. Tabla comparativa de modelos

| | **ISO 9001:2015** | **MoProSoft** (NMX-I-059-NYCE) | **SPICE** (ISO/IEC 15504, hoy serie ISO/IEC 33000) | **CMMI** (v2.0 / v3.0) | **PSP / TSP** |
|---|---|---|---|---|---|
| **Origen** | ISO (internacional) | México: Secretaría de Economía y NYCE, para la industria nacional de software | ISO/IEC (internacional) | SEI de Carnegie Mellon; hoy lo administra ISACA | SEI (Watts Humphrey) |
| **Qué evalúa** | El sistema de gestión de la calidad de **cualquier** organización | Los procesos de una **empresa pequeña o mediana** de software | La **capacidad de cada proceso** (es un marco para evaluar, no un modelo de procesos en sí) | La **madurez de la organización** y la capacidad por área de práctica | El trabajo de **cada ingeniero** (PSP) y del **equipo** (TSP) |
| **Estructura** | Cláusulas 4 a 10 con el ciclo PHVA y el enfoque a procesos | 3 categorías (Alta Dirección, Gerencia, Operación) y 9 procesos | Modelo de referencia de procesos + modelo de evaluación con atributos de proceso | Áreas de práctica agrupadas en capacidades | Scripts, formularios y métricas: tiempo, tamaño, defectos y rendimiento |
| **Niveles** | No tiene: se cumple o no se cumple | Capacidad 0 a 5 por proceso (basado en 15504) | Capacidad 0 a 5 por proceso | Madurez 1 a 5; capacidad 0 a 3 por área | PSP0 a PSP2.1 |
| **Resultado** | Certificado de un organismo acreditado | Evaluación con EvalProSoft y certificación con NYCE | Perfil de capacidad de los procesos | Calificación (appraisal) por un evaluador autorizado | Datos personales y de equipo para estimar y mejorar |
| **Costo para un equipo como el nuestro** | Alto; pensado para organizaciones con un sistema documental | Medio; diseñado para equipos pequeños y en español | Alto; requiere un evaluador | Muy alto; la calificación oficial es cara | **Bajo**; solo pide disciplina y un registro |
| **Qué tomamos en este proyecto** | El enfoque a procesos y la acción correctiva (`plan-sqa.md` §6) | La lista de productos de OPE.2 y la autoevaluación de este documento | La escala de capacidad 0 a 5 usada aquí | Las áreas de práctica para encontrar las brechas de la sección 3 | Los registros de tiempo y defectos en `calidad/` |

**La diferencia clave entre los cinco:** ISO 9001 dice *qué* debe tener un sistema de calidad, pero no es específico de software. MoProSoft y CMMI dicen *qué procesos* debe tener una organización de software. SPICE dice *cómo medir* qué tan capaz es cada proceso. PSP/TSP baja al nivel de la persona y del equipo. Para nosotros, PSP y MoProSoft son los que más aplican, porque son los únicos pensados para unidades tan pequeñas.
