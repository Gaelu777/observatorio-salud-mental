# Tendencia actual aplicada al observatorio: observabilidad de datos

## Qué es

La **observabilidad de datos** aplica a los *datos* lo que la observabilidad de software (registros, métricas y trazas) hace con las aplicaciones. Su objetivo es enterarse de que un dato está mal **antes** de que lo vea el cliente, y no cuando él lo reclama.

El término se popularizó alrededor de 2020 (Barr Moses, Monte Carlo) y hoy es parte de las prácticas de **DataOps**. Se resume en cinco pilares:

| Pilar | Pregunta que responde |
|---|---|
| **Frescura** | ¿Los datos están al día o la captura se detuvo? |
| **Volumen** | ¿Llegó la cantidad esperada de registros? |
| **Esquema** | ¿Cambiaron las columnas o los tipos en la fuente? |
| **Distribución** | ¿Los valores siguen en rangos razonables? |
| **Linaje** | Si algo falla, ¿qué tablas y qué gráficas del tablero se afectan? |

Es la diferencia entre **probar** (verificar lo que uno ya sabe que puede fallar) y **observar** (darse cuenta de fallas que nadie anticipó). Herramientas comerciales como Monte Carlo, Datadog Data Observability o Soda, y abiertas como Great Expectations, Elementary u OpenLineage, automatizan estos cinco pilares.

## Dónde está hoy nuestro observatorio

| Pilar | Lo que ya tenemos | Lo que falta |
|---|---|---|
| Frescura | `fecha_ingesta_max` en cada fila de Oro; bitácora diaria `capturas.csv` | Una **alerta** cuando el DENUE pase más de 48 h sin capturarse. Hoy hay que revisarlo a mano |
| Volumen | El manifiesto registra cuántos registros trae cada archivo; OC2 comprueba que `bronce = plata + cuarentena` | Comparar contra el volumen de la corrida anterior. Si el DENUE pasa de 1,649 a 300 establecimientos, hoy nadie se entera |
| Esquema | Pandera falla si falta una columna (error "estructural") | — (cubierto) |
| Distribución | Pandera valida rangos; atípicos marcados con IQR y Z robusto | Vigilar la deriva: que la media de un indicador no se mueva más de *k* desviaciones entre capturas |
| Linaje | `linaje_oro.csv` con 652/652 registros verificados; la verificación detiene el pipeline | Linaje a nivel de **columna** y hasta el tablero (OpenLineage) |

## Propuesta concreta (y barata) para E4

1. **Monitor de volumen y frescura** en el workflow diario, como un paso nuevo después de Plata:
   - Leer la última fila de cada fuente en el manifiesto.
   - Fallar si el volumen cambia más de ±20 % respecto a la captura anterior, o si la última captura del DENUE tiene más de 2 días.
   - La falla queda en la bitácora, y GitHub envía un correo al dueño del repositorio cuando falla un workflow. Así se tiene una alerta sin pagar nada.
2. **Indicador de salud en el tablero:** un semáforo en la pestaña "Calidad del sistema" con la última captura, el volumen frente a la captura anterior y la disponibilidad de los últimos 14 días. Usaría los colores de estado del tablero, siempre con icono y texto.
3. **Métricas que eso permite medir:** **MTTD** (tiempo medio para detectar una falla de datos), que hoy es "hasta que alguien mire", y **MTTR**, que ya se calcula con la bitácora.

## Por qué le importa a la cliente

La cliente no va a revisar el manifiesto ni la bitácora. Lo que ve es el tablero. Si un día el INEGI cambia el formato del DENUE y el pipeline carga solo una parte, el mapa le diría "hay menos competencia en el centro" **sin que sea cierto**, y ella podría tomar una decisión de negocio con un dato roto.

La observabilidad convierte "confíe en nosotros" en un **indicador visible** de que los datos de hoy son tan completos como los de ayer. Responde directamente a la tercera pregunta del Demo Day: *¿por qué se puede confiar en el sistema?*
