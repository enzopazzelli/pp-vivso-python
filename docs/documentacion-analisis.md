# Documentación del análisis — Sistema VIVSO
## Componente de Ciencia de Datos · PP2 · ITSE

---

## Para quién es este documento

Este documento explica **qué análisis se realizó, con qué datos y por qué**, de una forma que permite entenderlo sin importar el punto de partida:

- **Estudiante de Ciencia de Datos**: encontrará la justificación técnica de cada decisión metodológica.
- **Profesor o evaluador**: encontrará la trazabilidad entre los datos disponibles, el análisis elegido y su utilidad concreta.
- **Técnico del ministerio**: encontrará explicaciones de lo que cada gráfico o indicador significa en la práctica del programa.
- **Representante del área** (subsecretaría): encontrará qué decisiones habilita cada análisis y por qué es relevante para la gestión.

---

## El problema que se analiza

La Subsecretaría de Promoción Humana de Santiago del Estero gestiona un programa de viviendas sociales que involucra cientos de obras distribuidas en 18 departamentos. Estas obras son ejecutadas por Organizaciones No Gubernamentales (ONGs) bajo contrato, y supervisadas por técnicos del ministerio.

El desafío principal es de **visibilidad y control**:
- ¿Cuántas obras están en riesgo de no terminar a tiempo?
- ¿Qué ONGs cumplen y cuáles necesitan seguimiento urgente?
- ¿En qué etapa de la construcción se están bloqueando las obras?
- ¿Los datos que reportan las ONGs coinciden con lo que verifica el técnico?

Antes de VIVSO, esta información estaba distribuida en tres sistemas desconectados. El análisis que se describe aquí es el puente entre los datos y las decisiones.

---

## Los datos disponibles

### Fuente de datos

El backend Java (equipo de Programación) está en desarrollo. Mientras no está disponible, el componente Python genera un **dataset sintético de 1.500 registros** que reproduce las distribuciones geográficas y estadísticas reales del programa. Cuando el backend esté disponible, el sistema cambia automáticamente a datos reales con una sola variable de configuración.

### Qué contiene el dataset

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| `vivienda` | 1.500 | Una fila por expediente de obra |
| `organizacion` | 3 | ONGs con sus datos institucionales |
| `tecnico` | 6 | Técnicos con zona de cobertura |
| `asignacion_tecnico` | 901 | Qué obras tiene asignadas cada técnico |
| `visita` | 1.057 | Cada visita de campo con avance verificado |
| `avance_rubro` | 22.500 | Avance de cada etapa constructiva por obra |

### Variables clave de cada vivienda

- **`num_exp`**: código único del expediente
- **`estado`**: Iniciada / Avanzada / Finalizada / Adjudicada
- **`avance_obra`**: porcentaje de avance físico (AFO), 0–100%
- **`dias_activa`**: días transcurridos desde el inicio (calculado)
- **`clasificacion`**: código del tipo de vivienda (15 posibles)
- **`criterio`**: macrocategoría del código (Inclusion / Exclusion / Otro)
- **`nivel_riesgo`**: alto / medio / bajo (calculado por el pipeline Python)
- **`cuit_org`**: ONG gestora asignada (puede ser nulo: ~20% de las obras)

---

## El sistema de clasificaciones (15 códigos)

El sistema VISOC original clasifica cada vivienda con un código de dos caracteres. Esta clasificación determina el tipo de intervención necesaria y la elegibilidad del beneficiario.

| Código | Criterio | Descripción |
|--------|----------|-------------|
| 1a | Inclusión | Vivienda Rancho |
| 2a | Inclusión | Vivienda Precaria |
| 2b | Inclusión | Vivienda con riesgo de derrumbe |
| 3a | Inclusión | Vivienda con integrantes discapacitados |
| 4a | Otro | Viviendas Mixtas (rancho y material) |
| 4b | Otro | Material con Techo de Chapa/Losa |
| 4c | Otro | Material con techo de chapa/losa |
| 5a | Exclusión | Viviendas Abandonadas |
| 5b | Exclusión | Viviendas precarias sin antigüedad |
| 5c | Exclusión | Precarias con conflicto de titularidad |
| 5d | Exclusión | Asentamientos espontáneos |
| 5e | Exclusión | Ya posee vivienda del gobierno |
| 5f | Otro | No posee vivienda / tiene terreno |
| 5g | Exclusión | Vivienda rechazada |
| OT | Otro | Otro |

**El campo `criterio`** agrupa estos 15 códigos en tres macrocategorías que permiten análisis de alto nivel:
- **Inclusión**: viviendas aptas para el programa — el caso típico de intervención
- **Exclusión**: casos que no deberían ingresar al programa — si aparecen en el sistema y muestran avance, es una señal de alerta de selección de beneficiarios
- **Otro**: casos especiales que requieren evaluación individual

**Por qué importa en el análisis**: si las obras con criterio Exclusión tienen mayor tasa de riesgo alto que las de Inclusión, el problema no es operativo (demora en la obra) sino de origen (selección incorrecta del beneficiario). Eso requiere una intervención distinta.

---

## El AFO y los rubros de construcción

### Qué es el AFO

El **Avance Físico de Obra (AFO)** es un número entre 0 y 100% que indica cuánto se completó de una vivienda. No es subjetivo: se calcula como la **suma ponderada de 15 rubros de construcción**, donde cada rubro tiene un peso proporcional a su complejidad y costo relativo.

```
AFO = Σ (avance_rubro_i / 100) × peso_rubro_i
```

Los pesos suman 100%, por lo que un AFO de 40% significa que se completó el equivalente al 40% del total ponderado de las etapas.

### La secuencia constructiva (restricción clave)

La característica fundamental de los rubros es que son **estrictamente secuenciales**: el rubro N solo puede iniciarse cuando el rubro N-1 está finalizado. Esto no es una decisión de diseño del sistema — es una restricción física de la construcción.

| N° | Rubro | Peso |
|----|-------|------|
| 1 | Terreno y limpieza | 3% |
| 2 | Excavación e impermeabilización | 5% |
| 3 | Mampostería hasta dintel | 10% |
| 4 | Mampostería cerámico/Block | 10% |
| 5 | Encadenado | 5% |
| 6 | Revoque interior | 10% |
| 7 | Revoque exterior | 8% |
| 8 | Cielorraso con aislante térmico | 5% |
| 9 | Construcción de cielorrasos | 4% |
| 10 | Carpintería | 10% |
| 11 | Instalación de agua | 7% |
| 12 | Instalación eléctrica | 8% |
| 13 | Instalación sanitaria | 7% |
| 14 | Revestimiento exterior | 5% |
| 15 | Varios | 3% |

**Por qué esta secuencia importa para el análisis**: si sabemos que una obra tiene AFO=35%, podemos calcular exactamente en qué rubro está y cuánto avanzó dentro de ese rubro. Esto es mucho más informativo que decir "tiene 35% de avance".

---

## Los análisis y por qué se eligieron

### Notebook 01 — Exploración inicial (EDA)

**Qué hace**: responde tres preguntas básicas antes de cualquier análisis: ¿cuántos registros hay?, ¿qué tan completos son los datos?, ¿cómo se distribuyen las variables clave?

**Por qué se hace primero**: en cualquier proyecto de datos, explorar el dataset antes de analizarlo es obligatorio. Permite detectar problemas (datos faltantes, errores de carga, distribuciones inesperadas) que invalidarían análisis posteriores si no se identifican. Es también la forma de conocer los datos antes de plantear hipótesis.

**Qué se analiza y por qué**:
- **Distribución de estados**: el estado (Iniciada/Avanzada/Finalizada/Adjudicada) es el indicador operativo principal. Ver cuántas obras hay en cada estado da el panorama general del programa.
- **Clasificación y criterio**: con 15 códigos y 3 macrocategorías, es importante entender cuáles predominan. Si hay muchas obras de criterio Exclusión, eso es una señal de alerta inmediata.
- **Distribución del AFO**: un histograma revela si las obras están concentradas al inicio (muchas al 0–20%) o si hay progresión uniforme. Un pico en 100% indica muchas terminadas.
- **Distribución geográfica**: los recursos técnicos (visitas) se planifican por departamento. Saber dónde se concentran las obras determina la logística.
- **Obras en riesgo**: se adelanta el indicador de riesgo como primer diagnóstico rápido del programa.

**Qué revela**: una fotografía honesta del estado actual del programa, sin filtros ni suposiciones.

---

### Notebook 02 — Normalización y preprocesamiento

**Qué hace**: transforma el dataset crudo en un formato limpio y consistente listo para los análisis siguientes. No modifica los datos originales — genera un archivo procesado nuevo.

**Por qué se hace**: los datos crudos del sistema tienen formatos que las herramientas de análisis no pueden usar directamente (fechas como texto, variables categóricas como strings, escalas numéricas muy distintas entre variables). Sin este paso, los notebooks siguientes no funcionan o dan resultados incorrectos.

**Transformaciones y justificación**:

| Transformación | Justificación técnica | Justificación de negocio |
|---|---|---|
| Fechas string → datetime | Python no puede restar textos | Calcular `dias_activa` requiere aritmética de fechas |
| `dias_activa` derivada | No está en el dataset original | Es la variable central del modelo de riesgo |
| `anio_inicio` derivada | Necesaria para análisis temporal | Permite ver tendencia del programa año a año |
| Detección de inconsistencias | No se eliminan, se marcan | Informar al equipo de Programación qué corregir en el sistema |
| Encoding de `criterio` (manual) | Preserva orden lógico Inclusión→Otro→Exclusión | Con encoding automático (alfabético) el orden no tendría sentido |
| Encoding automático de resto | scikit-learn requiere números | Sin esto el clustering y otros modelos no corren |
| MinMaxScaler a [0,1] | Escala uniforme entre variables | `dias_activa` (0–600) dominaría sobre `avance_obra` (0–100) si no se normaliza |

**Por qué `criterio` se encoda manualmente**: el LabelEncoder de scikit-learn asigna enteros por orden alfabético. Eso daría Exclusion=0, Inclusion=1, Otro=2. Ese orden no tiene sentido de negocio. El encoding manual (Inclusion=0, Otro=1, Exclusion=2) preserva la jerarquía del programa: de más apta a más rechazada.

---

### Notebook 03 — Correlaciones y análisis bivariado

**Qué hace**: busca relaciones entre variables partiendo de hipótesis concretas sobre el programa. Cada análisis responde una pregunta de negocio.

**Por qué se hace**: las distribuciones del EDA muestran "qué hay". Las correlaciones muestran "qué se relaciona con qué", que es lo que permite explicar por qué algunas obras van bien y otras no.

**Análisis y su justificación**:

**Avance por criterio × tipo de vivienda**:
Pregunta: ¿Las obras de criterio Inclusión avanzan más que las de Exclusión? ¿Varía esto por tipo (urbana/rural)?
Por qué importa: si las obras Exclusión que igualmente están en el programa tienen sistemáticamente menor avance, el problema es de selección de beneficiarios, no de ejecución. Eso requiere una corrección en el proceso de admisión, no en la supervisión técnica.

**Duración por tipo de vivienda (ANOVA)**:
Hipótesis: las rurales tardan más por dificultades de acceso y provisión de materiales.
Por qué ANOVA y no t-test: el t-test compara exactamente 2 grupos. Aquí hay 3 tipos (Urbana/Rural/Económica). Aplicar t-test múltiples veces sobre los mismos datos inflaría la probabilidad de falsos positivos (error tipo I). ANOVA resuelve esto en un solo test.
Por qué importa: si se confirma, los contratos con ONGs para obras rurales deberían tener plazos diferenciados. Actualmente se usa el mismo plazo para todo.

**Duración por clasificación**:
Pregunta: ¿Hay clasificaciones que sistemáticamente toman más tiempo?
Por qué importa: un ministerio que sepa que el código 2b tarda en promedio 400 días puede planificar mejor, asignar más recursos técnicos a esas obras o ajustar los plazos contractuales con las ONGs antes de firmar.

**Riesgo por criterio y clasificación**:
Pregunta: ¿Qué clasificaciones concentran más obras en riesgo alto?
Por qué importa: si ciertos códigos tienen sistemáticamente mayor tasa de riesgo, el ministerio puede priorizar la supervisión técnica de esas obras desde el inicio, antes de que lleguen a estar en riesgo.

---

### Notebook 04 — Indicadores operativos y análisis AFO

**Qué hace**: construye los KPIs que el ministerio necesita para tomar decisiones, más el análisis secuencial de rubros constructivos.

**Por qué se hace**: los análisis de exploración y correlación son descriptivos. Los indicadores son prescriptivos: cada uno habilita una acción concreta. Un KPI sin acción asociada no sirve de nada.

**Los 7 KPIs y qué acción habilita cada uno**:

**KPI 1 — Tasa de finalización**
Qué mide: % de viviendas completadas (Finalizada o Adjudicada) sobre el total.
Acción que habilita: el subsecretario puede reportar avance al gobierno provincial con un número concreto. Sin esto, el reporte es narrativo y subjetivo.

**KPI 2 — Obras en riesgo alto**
Qué mide: obras activas que superaron el plazo de 90 días con menos del 30% de avance.
Por qué ese umbral: el plazo contractual de la etapa de construcción es de 90 días. Una obra que ya lo superó y todavía está por debajo del 30% de avance tiene probabilidad cercana a cero de cerrarse sin intervención. El umbral de 90 días es el plazo contractual real del programa.
Acción que habilita: el jefe de área puede priorizar las visitas técnicas a esas obras y activar el protocolo de seguimiento de la ONG responsable.

**KPI 3 — Obras en riesgo medio**
Qué mide: obras activas que superaron el plazo de 90 días con avance entre 30–80%.
Acción que habilita: seguimiento preventivo. Son obras vencidas pero que todavía avanzan, así que pueden cerrarse con acompañamiento antes de escalar a riesgo alto.

**KPI 4 — Tiempo promedio de ejecución**
Por qué solo obras terminadas: incluir obras en curso sesga el promedio. Una obra activa de 200 días podría terminar en 250 o en 700 — su duración real es desconocida. Solo las terminadas dan un dato fiable.
Acción que habilita: comparar el tiempo de cada ONG contra el promedio. Las que sistemáticamente tardan más que la mediana necesitan revisión contractual.

**KPI 5 — Rendimiento por ONG**
Qué mide: avance promedio, obras en riesgo y días promedio activos por organización.
Acción que habilita: accountability. El programa paga a las ONGs por los avances certificados. Si una ONG tiene alto riesgo y bajo avance, el ministerio puede retener pagos, aumentar la frecuencia de visitas o cancelar el contrato.

**KPI 6 — Cobertura geográfica activa**
Qué mide: cuántos departamentos tienen obras en curso y cuántas hay en cada uno.
Acción que habilita: planificación de visitas técnicas. Con máximo 2 visitas por obra, la distribución geográfica determina los recorridos de los técnicos. Un departamento con 50 obras activas necesita más tiempo que uno con 5.

**KPI 7 — Etapa cuello de botella**
Qué mide: en qué rubro de la secuencia constructiva se acumula la mayor cantidad de obras activas simultáneamente.
Acción que habilita: focalizar el reclamo y el seguimiento. La construcción es responsabilidad de la **organización gestora** (que suele tercerizar los servicios) — el ministerio no manda cuadrillas. Pero si el 30% de las obras activas está trabada en "Mampostería hasta dintel", el ministerio puede exigirle explicaciones a cada gestora con precisión de etapa, priorizar las visitas técnicas de verificación en esas obras y detectar qué ONGs concentran los bloqueos.

**El análisis de etapa activa**

Para cada obra, se calcula su **etapa activa**: el primer rubro de la secuencia que no llegó al 98% de completitud. Esto permite responder:
- *¿Dónde está exactamente bloqueada esta obra?*: no "tiene 35% de avance", sino "está en la etapa de Mampostería cerámico/Block y completó el 15% de esa etapa".
- *¿Cuáles etapas son las más problemáticas?*: se mide el % de obras que llegaron a un rubro pero no avanzan dentro de él (avance < 30% dentro del rubro). Eso es distinto de que muchas obras estén en esa etapa — puede que las que están ahí avancen bien.

Diferencia entre "concentración" y "parálisis":
- Muchas obras en una etapa = esa etapa es frecuente en el programa (puede ser normal)
- Muchas obras bloqueadas dentro de una etapa = hay un problema específico en esa etapa (material, mano de obra, aprobación)

---

### Notebook 05 — Análisis del equipo técnico

**Qué hace**: analiza el rendimiento del equipo técnico desde dos perspectivas: el jefe de área (visión global) y el técnico individual (su carga de trabajo).

**Por qué se hace**: los técnicos son el vínculo entre el ministerio y las obras. Con un máximo de 2 visitas técnicas por obra, cada visita tiene que ser eficiente. Un técnico sobrecargado deja obras sin verificar, lo que expone al ministerio a reportes de avance no validados.

**Regla de negocio central**: máximo 2 visitas técnicas por obra (primera y segunda). Entre visitas, las ONGs cubren el avance con reportes fotográficos en el portal.

**Análisis y su justificación**:

**Cobertura de visitas por técnico**:
Métrica: obras con al menos 1 visita / total asignadas.
Por qué no se usa "visitas totales": un técnico puede acumular muchas segundas visitas a las mismas obras y dejar otras sin primer relevamiento. La cobertura mide si llegó a todas.
Umbral del 70%: se estableció como objetivo mínimo de cobertura. Por debajo, el técnico está sobrecargado o rezagado.

**Scatter carga vs. cobertura**:
Permite identificar el cuadrante problemático: alto volumen de obras + baja cobertura = técnico sobrecargado. El técnico Ibáñez (40% de cobertura con muchas obras asignadas) es el caso de alerta en el dataset.
Por qué un scatter y no una tabla: la relación entre dos variables numéricas se lee más rápido visualmente. Un punto fuera de la nube es inmediatamente visible.

**Discrepancias ONG vs. técnico**:
Qué es: avance reportado por la ONG menos avance verificado in situ por el técnico.
Por qué es importante: si la ONG reporta 70% y el técnico verifica 60%, la diferencia es +10 puntos. Eso puede indicar:
- Error de estimación (aceptable, pasa en cualquier registro)
- Reporte inflado intencional (preocupante, puede afectar los pagos certificados)
Un valor positivo consistente en la misma ONG es una señal de alerta. Un valor negativo (ONG subestimó) es menos crítico — la obra está mejor de lo que reportaron.

**Cola de prioridad del técnico**:
El técnico ve sus obras ordenadas: Sin visitar (alta prioridad) → Falta segunda visita → Completo. Dentro de cada grupo, las obras de riesgo alto van primero.
Por qué este orden: sin un sistema de priorización, el técnico puede visitar obras cercanas o fáciles primero, dejando sin atender las que realmente lo necesitan. La cola elimina ese sesgo.

---

## El modelo de riesgo

**Definición**: obra activa + superó el plazo de 90 días + todavía no está por terminar (avance < 80%).

**Por qué 90 días**: es el plazo contractual de la etapa de construcción del programa. Una obra que ya lo superó y sigue lejos de terminarse necesita intervención. El dato revelador es que el atraso es estructural: ~85% de las obras terminadas tardó más de 90 días (promedio real ~167) y ~58% de las activas ya está vencida. Por eso el indicador no marca "las pocas que se atrasan" sino "las que, además de vencidas, no están avanzando".

**Por qué el corte de avance**: una obra vencida pero con avance ≥ 80% está por entregarse — no es riesgo real de no terminar. El riesgo se concentra en las vencidas con bajo avance.

**Por qué dos niveles** (alto y medio):
- Riesgo alto (avance < 30%): la obra superó el plazo y está prácticamente paralizada. Intervención urgente.
- Riesgo medio (avance 30–80%): la obra superó el plazo pero avanza. Seguimiento preventivo antes de que escale.
Tener un solo nivel "en riesgo" no permite priorizar. El ministerio necesita saber dónde actuar hoy y dónde puede esperar a la próxima semana.

**Integración con el resto del sistema**: Python escribe `nivel_riesgo` en la base de datos local. Cuando el backend Java esté disponible, puede leer ese campo y exponerlo en la API. El portal Next.js lo muestra en el mapa y los dashboards sin ningún cambio adicional.

---

## El análisis de rubros AFO en detalle

Este análisis parte de una pregunta diferente a todas las demás: no "¿cuánto avanzó la obra?" sino "**¿en qué etapa exacta está bloqueada y qué tan bloqueada está?**"

**La restricción secuencial como herramienta**

Si los rubros son secuenciales (N requiere que N-1 esté al 100%), entonces para cualquier obra podemos identificar su **etapa activa**: el primer rubro que no llegó al 98% de completitud. Todo lo anterior en la secuencia está terminado. Todo lo posterior no ha comenzado.

Esto convierte el AFO de un número opaco en un diagnóstico preciso:
- AFO=35% + etapa activa=4 + avance en etapa=15% → "La obra terminó mampostería hasta dintel, encadenado y los dos primeros metros de mampostería Block. Está paralizada al inicio de esa etapa."
- AFO=35% + etapa activa=6 + avance en etapa=85% → "La obra está casi terminando el revoque interior. Está en buen ritmo."
Ambas tienen el mismo AFO, pero la situación es muy distinta.

**El cuello de botella vs. la parálisis**

Son dos indicadores distintos que se complementan:

*Cuello de botella*: la etapa donde más obras están activas simultáneamente. Si 40% de las obras están en "Mampostería hasta dintel", esa etapa absorbe la mayor parte de los recursos. Puede ser normal (es una etapa larga y pesada) o puede indicar que hay un problema de materiales o cuadrillas.

*Tasa de parálisis por etapa*: % de obras que llegaron a un rubro pero tienen menos del 30% de avance dentro de él. Una obra al 5% dentro del rubro activo está prácticamente paralizada — llegó a esa etapa pero no avanzó. Eso es específicamente preocupante porque significa que algo bloqueó el inicio de esa etapa (falta de aprobación, materiales, personal).

**Patrones reales de bloqueo (modelados en datos sintéticos)**:

| Nivel de riesgo | Etapa de bloqueo típica | Causa probable |
|---|---|---|
| Riesgo alto | Mampostería (r. 3–5) | Cuadrilla ausente, falta de materiales estructurales |
| Riesgo medio | Revoques (r. 6–7) | Requieren mano de obra especializada, escasa en zonas rurales |
| Sin riesgo | Carpintería y más adelante | Obra avanzando normalmente |

**Por qué esto es importante para el ministerio**: si el análisis muestra que el cuello de botella es "Instalación sanitaria" (rubro 13), y la tasa de parálisis en ese rubro es alta, el ministerio sabe que hay un problema de aprobaciones municipales — ese rubro requiere inspección y habilitación de la municipalidad. La solución no es enviar más técnicos, sino gestionar con el municipio. Sin el análisis de rubros, la única información disponible es "la obra no avanza".

---

## El dashboard como herramienta de gestión

El dashboard Streamlit no es una visualización decorativa — es la interfaz entre el análisis y la toma de decisiones.

**Página Viviendas**: permite al ministerio filtrar obras por criterio (Inclusión/Exclusión/Otro), estado, departamento y nivel de riesgo. El mapa GPS muestra la distribución geográfica coloreada por riesgo.
*Para el técnico*: puede ver qué obras de su zona están en riesgo antes de planificar visitas.
*Para el subsecretario*: puede ver el estado general del programa en un solo pantallazo.

**Página ONGs**: muestra el rendimiento comparativo de cada organización. Barras coloreadas en rojo indican ONGs con obras en riesgo.
*Para el responsable de contratos*: identifica qué ONGs necesitan conversación urgente.

**Página Minería**: muestra el modelo de riesgo interactivo (scatter días vs. avance) y el análisis de rubros AFO con los dos gráficos (cuello de botella y tasa de parálisis).
*Para el equipo técnico*: permite ver en qué etapa están concentradas las obras problemáticas.

**Página Equipo Técnico**: muestra cobertura de visitas por técnico y discrepancias con las ONGs.
*Para el jefe de área*: detecta quién está sobrecargado y quién tiene discrepancias sistemáticas.

**Página Mis Obras**: vista individual del técnico con su cola de prioridad.
*Para el técnico*: sabe exactamente en qué orden visitar sus obras sin necesidad de criterio propio.

---

## Decisiones técnicas que pueden necesitar explicación

**¿Por qué datos sintéticos y no datos reales?**
El sistema VIVSO es nuevo. La API Java estaba en desarrollo durante el Hito 2. Sin datos reales, el análisis sería imposible. Los datos sintéticos reproducen las distribuciones estadísticas reales del programa (pesos por departamento, proporciones de estados, etc.) sin exponer información sensible de beneficiarios reales.

**¿Por qué SQLite y no la base de datos de Programación (MySQL)?**
Independencia de equipos. Si el equipo de Ciencia de Datos trabajara sobre la misma base que el equipo Java, cualquier cambio de uno podría romper el trabajo del otro. SQLite local permite desarrollo independiente. La integración final es un cambio de una variable de entorno.

**¿Por qué Python/pandas y no Excel o Power BI?**
Reproducibilidad. Un análisis en Excel no puede re-ejecutarse automáticamente cuando llegan datos nuevos. Python ejecuta todos los notebooks en secuencia y regenera todos los gráficos e indicadores automáticamente. Además, la integración con scikit-learn, scipy y el dashboard Streamlit no es posible desde Excel.

**¿Por qué ANOVA para comparar tipos de vivienda y no un t-test?**
El t-test compara exactamente dos grupos. Aquí hay tres tipos (Urbana, Rural, Económica). Aplicar el t-test tres veces (Urbana vs. Rural, Urbana vs. Económica, Rural vs. Económica) inflaría la probabilidad de falsos positivos acumulativamente. ANOVA testea los tres grupos simultáneamente con un solo nivel de significancia.

**¿Por qué el encoding de `criterio` es manual?**
El LabelEncoder de scikit-learn ordena los valores alfabéticamente: Exclusion=0, Inclusion=1, Otro=2. Ese orden no refleja la jerarquía del programa (de más apta a más rechazada). El encoding manual (Inclusion=0, Otro=1, Exclusion=2) preserva ese significado, lo que hace que la correlación `criterio_enc` vs. `avance` sea interpretable en términos de negocio.

**¿Por qué el cap de los rubros activos en 97% y no 100%?**
Es una restricción técnica de la detección de etapa activa. El sistema identifica la etapa activa buscando el primer rubro con avance < 98%. Los rubros completados se registran como 98–100% (incluyendo pequeñas imprecisiones de registro de campo). Si el rubro activo llegara a 99% (que es < 100 pero ≥ 98), el detector lo marcaría como "completo" y miraría el siguiente rubro (con avance 0%), produciendo un diagnóstico incorrecto. El cap en 97% garantiza que el rubro activo siempre sea correctamente identificado.

---

## Glosario

| Término | Significado |
|---------|-------------|
| **AFO** | Avance Físico de Obra. Porcentaje de completitud de una vivienda, calculado como suma ponderada de los 15 rubros constructivos. |
| **Rubro** | Cada una de las 15 etapas de construcción que componen el AFO. Tienen pesos distintos y son estrictamente secuenciales. |
| **Etapa activa** | El rubro donde está actualmente detenida una obra — el primero de la secuencia que no llegó al 98%. |
| **Cuello de botella** | La etapa donde se concentra la mayor cantidad de obras activas simultáneamente. |
| **Criterio** | Macrocategoría del código de clasificación: Inclusión (apta), Exclusión (rechazada), Otro (caso especial). |
| **Clasificación** | Código de dos caracteres (1a, 2b, 5g, etc.) que describe el tipo de vivienda según el sistema VISOC. |
| **Nivel de riesgo** | Clasificación calculada por Python: alto (vencida >90 días y AFO <30%), medio (vencida >90 días y AFO 30–80%), bajo (resto). |
| **Discrepancia ONG vs. técnico** | Diferencia entre el avance que reporta la ONG y el que verifica el técnico en la visita. Positivo = ONG sobreestimó. |
| **Cobertura de visitas** | Porcentaje de obras asignadas a un técnico que recibieron al menos una visita presencial. |
| **ETL** | Extract, Transform, Load. El proceso de extraer datos de una fuente, transformarlos y cargarlos en la base de datos de análisis. |
| **ANOVA** | Analysis of Variance. Test estadístico que evalúa si las medias de más de dos grupos son significativamente distintas. |
| **MinMaxScaler** | Técnica de normalización que lleva todas las variables numéricas al rango [0,1] para que ninguna domine por su magnitud. |
| **encoding** | Conversión de variables categóricas (texto) a números para que los algoritmos de Machine Learning puedan procesarlas. |
| **ONG** | Organización No Gubernamental. En VIVSO, las ONGs son los ejecutores de las obras bajo contrato con el ministerio. |
| **VISOC** | Sistema legacy del ministerio que registraba las viviendas sociales antes de VIVSO. Define los 15 códigos de clasificación. |
