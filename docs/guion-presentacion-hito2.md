# Guion de presentación — Hito 2 · PP2
### Ciencia de Datos · ITSE — Grupo 8

**Equipo:** Pablo Castillo · Sara Lombardi · Valeria Martinetti · Santiago Gallardo · Enzo Pazzelli
**Duración objetivo:** 10 minutos + preguntas
**Audiencia:** profesor de la cátedra y compañeros de PP2
*(La presentación al Arq. Fernández, Subsecretario, será en una instancia posterior — este guion apunta a la defensa académica.)*

> ⚠️ **Documento histórico (Hito 2, ya presentado).** La devolución marcó que el guion se usó mal (memorizado/leído). Para futuros guiones y su protocolo de preparación, leer primero `docs/guia-presentaciones.md`.

---

## Cómo usar este guion

Esto **no es para leer las slides**. La slide ya dice qué hicimos; el que habla aporta el *por qué* y el *qué significa*. Cada punto de abajo es **subtexto**: una decisión técnica, una lectura analítica o una conexión con el problema real que no está escrita en pantalla.

Regla de oro: **si lo que vas a decir ya se lee en la slide, no lo digas.** Mostralo con la mano y agregá la capa que no se ve.

Tono: concisos, seguros, conversacionales. Frente al profesor mostramos **criterio y rigor** (por qué cada decisión); frente a los compañeros, **cómo lo resolvimos** (es un proyecto del que se puede aprender). No somos un equipo que aprendió pandas: somos un equipo que entendió un problema y eligió las herramientas para resolverlo.

---

## Mapa de tiempos (10 min)

| Bloque | Slides | Quién | Tiempo |
|---|---|---|---|
| Apertura + contexto + arquitectura | 1–4 | Persona A | 1:45 |
| Datos y preparación | 5–6 | Persona B | 1:45 |
| EDA + modelo de riesgo | 7–8 | Persona C | 2:00 |
| Cuellos de botella + cómo calculamos + indicadores | 9–11 | Persona D | 2:15 |
| Equipo técnico + dashboard + portal + cierre | 12–15 | Persona E | 2:15 |

> Asignación sugerida (ajústenla a quién se siente más cómodo con cada tema). Lo importante: **las transiciones se nombran** — cada uno cierra pasándole la palabra al siguiente.

---

## Apertura — Persona A · 1:45

**Hook (no leer la portada).** Arrancar con la tensión real, no con "somos el grupo 8":
> *"El programa de viviendas tiene cientos de obras, tres ONGs ejecutoras y seis técnicos para supervisarlas. La pregunta que nos hicimos no fue 'qué datos hay', sino 'qué decisiones no se pueden tomar hoy por falta de información'. Todo lo que sigue responde a eso."*

**Valor agregado (lo que no está en las slides 2-4):**
- **Por qué una base local propia y no la del equipo de Programación:** decisión de arquitectura, no de comodidad. Trabajar sobre su MySQL nos haría dependientes de su ritmo y un cambio de ellos rompería lo nuestro. SQLite local nos da independencia; la integración es **una variable de entorno**, no una reescritura.
- **Por qué datos sintéticos no es un parche:** es construir todo el pipeline *antes* de que existan los datos reales, para que el día que el backend esté listo, todo funcione sin tocar análisis ni dashboard. Los datos sintéticos reproducen distribuciones reales (peso por departamento, proporciones de estados).
- **La relación entre los dos equipos:** consumimos el "contrato" de la API (la forma de los datos) antes de que existiera. Eso es lo que permite el plug-and-play.

**Transición:** *"Sara/Persona B les va a mostrar que el trabajo no empieza en el gráfico, empieza mucho antes."*

---

## Datos y preparación — Persona B · 1:45

**Valor agregado (slides 5-6):**
- **Recuperamos una dimensión que el sistema nuevo había perdido.** El backend Java implementó 6 clasificaciones; el sistema legacy real (VISOC) tiene **15, agrupadas por criterio** (Inclusión / Exclusión / Otro). Volvimos a la fuente original. No aceptamos el esquema que nos dieron: lo cuestionamos. Eso habilita una pregunta nueva: *¿hay viviendas que no deberían estar en el programa y aun así avanzan?*
- **La columna `observacion` parece vacía pero es estratégica.** Es donde el técnico escribe el contexto cualitativo — "obra paralizada", "falta de materiales". Hoy es escasa, pero es el puente hacia minería de texto y OCR de los formularios en papel. La modelamos para que el día que se llene, ya tenga lugar.
- **Las inconsistencias no se borran, se marcan.** Una obra "Finalizada" con avance < 80% es un error de carga. En vez de ocultarlo, lo marcamos con una bandera y se lo devolvemos al equipo de Programación. Tratamos al dataset como un **circuito de feedback**, no como algo que solo consumimos.
- **El detalle que parece menor — encoding manual de `criterio`:** la herramienta por defecto ordena alfabético; nosotros preservamos el orden de negocio (Inclusión → Otro → Exclusión). Decisiones chicas que mantienen el sentido para quien después lee el resultado.

**Transición:** *"Con los datos limpios, lo primero que encontramos nos cambió la lectura de todo el programa."*

---

## EDA + Modelo de riesgo — Persona C · 2:00

**Valor agregado (slide 7 — el hallazgo que reordena todo):**
- **El número que importa: ~70% de las obras activas no tiene ninguna visita técnica.** Esto no es un dato más — significa que **el avance que reporta el programa es, en su mayoría, no verificado**. Todo el resto del análisis se apoya en entender esa brecha. Decirlo con peso: cambia cómo se lee cualquier KPI de avance.
- Las ONGs, en promedio, **sobreestiman** el avance frente a lo que el técnico verifica. No lo presentamos como acusación: lo presentamos como señal de dónde poner el control.

**Valor agregado (slide 8 — decisión técnica fuerte):**
- **Elegimos una regla transparente, no un modelo de machine learning.** Podríamos haber hecho clustering o un clasificador — de hecho probamos clustering y lo descartamos: daba grupos pobres (k=2) que no habilitaban ninguna decisión. El modelo de riesgo es una **regla de tres condiciones** porque el ministerio tiene que poder *explicarle a una ONG* por qué su obra está marcada en riesgo. Una caja negra no es defendible en una mesa de gestión; una regla sí.
- El umbral de 90 días no es arbitrario: es el **plazo contractual** de la etapa de construcción. El dato fuerte: el ~85% de las obras terminadas lo superó (promedio real ~167 días) — el atraso es estructural, no la excepción.

**Transición:** *"Esa regla nos dijo cuáles obras están en riesgo. La pregunta siguiente fue: ¿por qué se traban? Y ahí encontramos que no hay una sola respuesta."*

---

## Cuellos de botella + Cómo calculamos + Indicadores — Persona D · 2:15

**Valor agregado (slide 9 — el punto más fuerte de la presentación):**
- **Este hallazgo salió de escuchar al área, no de los datos.** Cuando profundizamos en cómo funciona el programa, apareció algo que el esquema de datos no mostraba: una obra puede estar **100% construida y aun así frenada**, esperando que se tramite el *acta de finalización*. Lo modelamos después de entenderlo. Son **dos cuellos de botella distintos**:
  - **Constructivo** — la obra no se construye (falta cuadrilla, materiales). Se resuelve con logística.
  - **Administrativo** — la obra está terminada pero el acta no se tramita por falta de seguimiento. Se resuelve **destrabando papeles** — es el arreglo más rápido y barato del programa, y hoy nadie lo está midiendo.
- Frase para fijar: *"El ministerio puede estar mandando una cuadrilla a una obra que en realidad solo necesita una firma."*

**Valor agregado (slide 10 — mostrar criterio, no código):**
- **La restricción de que los rubros son secuenciales es lo que vuelve útil al AFO.** "35% de avance" no dice nada. Pero como cada etapa requiere que la anterior esté terminada, podemos ubicar la traba exacta: *"está en mampostería y solo avanzó el 15% de esa etapa"*. Eso sí es accionable.
- **Por qué el índice de confiabilidad pesa más el avance que la finalización:** una ONG eficiente con muchas obras en curso sanas no debe quedar mal rankeada solo por no haber terminado todavía. La fórmula está diseñada para no castigar el buen trabajo en proceso.

**Valor agregado (slide 11):**
- Cada indicador termina en una **decisión**, no en un gráfico. El índice de confiabilidad responde "a quién audito"; las actas atascadas, "qué entregas destrabo esta semana".

**Transición:** *"Todo esto sería un informe muerto si no llegara a quien toma las decisiones. Persona E les muestra cómo lo pusimos en sus manos."*

---

## Equipo técnico + Dashboard + Portal + Cierre — Persona E · 2:15

**Valor agregado (slide 12):**
- **Convertimos el recurso más escaso en un problema de optimización.** Con 2 visitas máximo por obra y 70% sin visitar, el técnico no puede ir a todas. El score de priorización le arma la lista del día con un criterio objetivo — saca de la ecuación el sesgo de "voy a la que me queda cerca".
- **La alerta de sobre-reporte toca un tema sensible con cuidado:** son obras con avance alto declarado y cero verificación. No afirmamos que haya fraude; señalamos dónde el programa estaría **certificando o pagando sobre datos no validados**. Es control, no acusación.

**Valor agregado (slides 13-14):**
- **El dashboard no es un entregable aparte:** consume el mismo dataset que los notebooks y se conecta a la API real con una variable de entorno. No hay trabajo de migración pendiente.
- **El portal de ONGs cierra la brecha del 0 al 100%:** entre las dos visitas técnicas, la ONG sube avance con fotos. Es lo que llena el vacío de verificación que mostramos al principio.

**Cierre (no leer "gracias"):**
> *"Empezamos preguntándonos qué decisiones no se podían tomar por falta de información. Hoy el área puede saber qué obra visitar primero, qué ONG auditar y qué vivienda terminada está esperando solo una firma. Eso es lo que cambió entre el Hito 1 y hoy."*

---

## Preguntas que probablemente nos hagan (y cómo responder)

*Pensadas para profesor y compañeros: apuntan a metodología, decisiones técnicas y proceso de equipo.*

**"¿Por qué datos sintéticos? ¿No invalida el análisis?"**
> El backend real todavía no tiene datos cargados. Generamos datos que imitan las distribuciones reales (peso por departamento, proporciones de estados) para validar que el pipeline completo funciona. Es validación de arquitectura: con datos reales solo cambia el origen, no el análisis. Y nos permitió modelar problemáticas concretas como las actas.

**"¿Por qué una regla para el riesgo y no un modelo de machine learning?"**
> Lo evaluamos: probamos clustering y daba grupos sin valor de decisión (k=2). Elegimos una regla de tres condiciones porque tiene que ser **explicable y auditable** — el área debe poder justificar ante una ONG por qué su obra está marcada. En este dominio, poder defender el número vale más que un decimal de precisión.

**"¿Cómo validaron que el problema de las actas es real?"**
> No salió de los datos, salió de **entender el dominio**: al profundizar en cómo funciona el programa apareció el cuello administrativo. Lo modelamos *después* de identificarlo. Es el ejemplo de que el análisis no arranca en el código, arranca en la pregunta correcta.

**"¿Cómo se integra esto con lo que hace el equipo de Programación?"**
> Trabajamos con base local propia (SQLite) a propósito, para no depender de su ritmo. La integración es una variable de entorno apuntando a su API — sin reescritura. Es una decisión de arquitectura que tomamos al inicio.

**"¿Por qué Colab / Streamlit y no otra cosa?"**
> Colab para que el equipo trabaje los notebooks en paralelo sin instalar nada y compartir resultados fácil. Streamlit porque el dashboard se arma en Python puro, con el mismo dataset que los notebooks — cero duplicación de lógica entre análisis y visualización.

**"¿Cómo se repartió el trabajo en el equipo?"**
> (Respuesta honesta del grupo.) Vale la pena nombrar quién llevó datos/ETL, quién los notebooks de análisis, quién el dashboard y quién la integración — muestra que fue trabajo coordinado, no cinco partes sueltas.

**"¿Qué fue lo más difícil / qué harían distinto?"**
> Buena oportunidad para mostrar madurez: por ejemplo, modelar la secuencia de rubros de forma realista costó varias iteraciones, o decidir qué indicadores agregaban valor real y cuáles eran ruido (descartamos varios). Mostrar que sabemos distinguir lo que aporta de lo que sobra.

---

## Recordatorios finales para todos

- **No leer la pantalla.** La slide es el respaldo visual; ustedes son el contenido.
- **Nombrar la transición** antes de pasar la palabra — la presentación se siente un solo relato, no cinco.
- **Un dato fuerte por bloque**, dicho despacio: 70% sin visita · dos cuellos de botella · 158 actas atascadas · a quién auditar.
- Si se va el tiempo, **el bloque sacrificable es el EDA** (slide 7 se resume en una frase). Los cuellos de botella y los indicadores **no se recortan** — son lo diferencial.
- Frente al profesor: cada decisión tiene un *por qué* — tenerlo listo. Frente a los compañeros: es un proyecto del que se aprende, mostrarlo con seguridad.
- Cerrar mirando al profesor y al curso, no a la pantalla.
