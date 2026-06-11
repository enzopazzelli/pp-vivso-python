# Prompt — Generación de presentación PPTX · Hito 2

Generá una presentación profesional en formato PowerPoint (.pptx) para la entrega del **Hito 2** de la Práctica Profesionalizante II del ITSE.

---

## Contexto del proyecto

**Institución cliente:** Subsecretaría de Promoción Humana — Ministerio de Desarrollo Social, Santiago del Estero
**Referente:** Arq. Ernesto Fernández, Subsecretario
**Carrera:** Ciencia de Datos — ITSE
**Equipo:** Pablo Castillo · Sara Lombardi · Valeria Martinetti · Santiago Gallardo · Enzo Pazzelli
**Grupo:** 8
**Footer de todas las diapositivas:** `PP2 · Hito 2 · Grupo 8`

El proyecto construye el sistema **VIVSO**, que reemplaza tres sistemas legacy desconectados (App GPS, VISOC y GEDO). El equipo de Ciencia de Datos es responsable del análisis de datos, visualización y el portal institucional. El equipo de Desarrollo de Software construye el backend Java.

---

## Lo que se planteó en el Hito 1

El Hito 1 cerró con estos objetivos para el Hito 2:
1. EDA completo sobre el dataset
2. Capa de transformación (procesamiento de datos)
3. Primeros KPIs operativos
4. Reunión de validación con el equipo VIVSO

---

> ⚠️ **Documento histórico (Hito 2, ya presentado).** Para futuras presentaciones, leer primero `docs/guia-presentaciones.md` — incorpora la devolución del profesor sobre esta presentación.

---

## Estilo de diseño

- **Tema claro y profesional** — fondo blanco (#FFFFFF) o gris muy claro (#F8FAFC), texto oscuro (#0F172A o #1E293B)
- Tipografía limpia y moderna (sans-serif — Calibri, Montserrat o equivalente)
- **Paleta estándar (la misma de los notebooks)** — base índigo + semáforo suave:
  - Base / primario: **índigo #4F46E5**
  - Positivo / bien: **esmeralda #10B981**
  - Medio / atención: **ámbar #F59E0B**
  - Alerta / crítico: **rosa #F43F5E**
  - Neutro / contexto: **slate #94A3B8**
- Los slides de **cabecera de sección** usan fondo índigo sólido (#4F46E5) con texto blanco — el resto es fondo claro con texto oscuro
- Datos y métricas destacados en tipografía grande (48–64 pt), en índigo
- Estilo consistente: sección marcada como `01 · NOMBRE`, numeración de slide abajo derecha
- Las tablas usan encabezado índigo con texto blanco; filas alternadas en gris muy claro (#F1F5F9)
- Los iconos de estado usan el semáforo suave: 🔴 rosa, 🟡 ámbar, 🟢 esmeralda
- Los diagramas de flujo van de izquierda a derecha con flechas →
- Bordes y separadores en gris claro (#E2E8F0)
- **Coherencia visual:** los gráficos de los notebooks usan exactamente esta paleta, así que las capturas insertadas combinan con el diseño de los slides

---

## Estructura de diapositivas

### Slide 1 — Portada
- Título principal: **"Hito 2 · PP2"**
- Subtítulo: **"Ciencia de datos aplicada a la gestión de vivienda social"**
- Franja inferior (fondo azul institucional, texto blanco): "Subsecretaría de Promoción Humana — Santiago del Estero"
- Equipo: "Pablo Castillo · Sara Lombardi · Valeria Martinetti · Santiago Gallardo · Enzo Pazzelli"
- Institución: "ITSE — Ciencia de Datos · Práctica Profesionalizante II"

---

### Slide 2 — Agenda
Título: **"Lo que vamos a contar"**
Subtítulo: "De lo planteado en el Hito 1 a lo logrado en el Hito 2"

Items numerados:
- **01** Lo que planteamos — logros del Hito 1
- **02** Arquitectura Python — el flujo ETL → BDD → Dashboard
- **03** Dataset y preprocesamiento — 15 clasificaciones, criterio y normalización
- **04** Cómo preparamos los datos — transformaciones y columnas clave (con código)
- **05** EDA — hallazgos clave de la exploración
- **06** Modelo de riesgo — identificar obras antes de que se paralicen
- **07** Los dos cuellos de botella — constructivo (rubros AFO) y administrativo (actas)
- **08** Cómo calculamos los indicadores — método y criterio (con código)
- **09** Indicadores de gestión — confiabilidad de ONGs y KPIs accionables
- **10** Equipo técnico — priorización de visitas y alerta de sobre-reporte
- **11** Dashboard Streamlit — demo de las 5 páginas
- **12** Portal ONGs — avances fotográficos en el frontend institucional

---

### Slide 3 — Sección 01: Logros del Hito 1
Cabecera de sección: `01 · LO QUE PLANTEAMOS` (fondo índigo, texto blanco)
Subtítulo: "Cuatro objetivos. Cuatro logrados."

Tabla con ✅:
| Objetivo Hito 1 | Estado |
|---|---|
| EDA completo sobre el dataset | ✅ 5 notebooks completados |
| Capa de transformación | ✅ ETL + normalización implementados |
| Primeros KPIs operativos | ✅ 7 indicadores con justificación |
| Reunión de validación con VIVSO | ✅ Contrato técnico validado |

Texto de apoyo: "Más allá de lo planteado, el equipo incorporó el análisis secuencial del Avance Físico de Obra por rubros de construcción, el modelo de riesgo, el análisis del equipo técnico y un dashboard interactivo completo."

---

### Slide 4 — Sección 02: Arquitectura Python
Cabecera de sección: `02 · ARQUITECTURA PYTHON` (fondo índigo, texto blanco)
Subtítulo: "El flujo que propuso el profesor: ETL → BDD → Dashboard"

Diagrama de flujo horizontal con 4 pasos:
1. **Fuentes** — API Java / Excel ONGs / datos sintéticos
2. **ETL Python** — extract.py (pandas, requests)
3. **Base de datos local** — SQLite con 9 tablas (independiente del MySQL de Programación)
4. **Análisis + Dashboard** — 5 notebooks EDA + Streamlit (5 páginas)

Nota al pie: "La DB local no interfiere con el trabajo del equipo de Programación. Se integran cuando el backend esté disponible cambiando una variable de entorno."

---

### Slide 5 — Sección 03: Dataset
Cabecera de sección: `03 · DATASET` (fondo índigo, texto blanco)
Subtítulo: "Datos reales escasos → dataset sintético representativo"

**Columna izquierda — El problema:**
- El backend Java es nuevo → pocos registros reales disponibles
- Solución: dataset sintético de 1.500 viviendas generado con Python (Faker + numpy)
- Distribución geográfica basada en los 18 departamentos reales de Santiago del Estero
- Proporciones de estados, clasificaciones y tipos coherentes con el programa real

**Columna derecha — Datos generados:**
- 1.500 viviendas · 3 ONGs · 6 técnicos
- ~870 asignaciones técnico↔vivienda · ~1.030 visitas con avance verificado
- **22.500 registros de rubros AFO** (15 etapas por obra)
- Perfiles diferenciados: ONG eficiente / ONG con problemas / técnico sobrecargado

**Dos sistemas del dominio modelados con realismo:**
- **15 clasificaciones VISOC** agrupadas en tres criterios — 🟢 Inclusión (aptas), 🔵 Otro (especiales), 🔴 Exclusión (rechazadas)
- **Ciclo de actas**: una porción de obras finalizadas queda con el acta de finalización atascada (limbo administrativo), reproduciendo un cuello de botella real del programa

---

### Slide 6 — Sección 04: Cómo preparamos los datos
Cabecera de sección: `04 · CÓMO PREPARAMOS LOS DATOS` (fondo índigo, texto blanco)
Subtítulo: "Antes de analizar hay que limpiar — cada transformación tiene un porqué"

Objetivo del slide: mostrar el trabajo de preprocesamiento (notebook 02) **sin abrir el notebook**. Layout de dos columnas: a la izquierda un fragmento de código real, a la derecha la justificación de cada decisión.

**Columna izquierda — Fragmento de código (caja monoespaciada, fondo gris muy claro #F1F5F9):**
```python
# Fechas de texto a datetime → habilita calcular duraciones
df['fecha_inic_dt'] = pd.to_datetime(df['fecha_inic'],
                                     format='%d-%m-%Y', errors='coerce')
df['dias_activa'] = (df['fecha_fin_dt'].fillna(hoy)
                     - df['fecha_inic_dt']).dt.days

# 'criterio' se codifica a mano para preservar el orden del programa
criterio_map = {'Inclusion': 0, 'Otro': 1, 'Exclusion': 2}
df['criterio_enc'] = df['criterio'].map(criterio_map)

# Normalización a [0,1]: que ninguna variable domine por su escala
scaler = MinMaxScaler()
df[cols_norm] = scaler.fit_transform(df[cols_num])
```

**Columna derecha — Decisiones y columnas clave:**

| Columna / paso | Por qué importa |
|---|---|
| `dias_activa` (derivada) | Es la base del modelo de riesgo y del cálculo de espera de actas |
| `observacion` | Campo de texto del técnico (obra paralizada, falta de materiales). Sparse pero es el **contexto cualitativo** detrás del número — futura fuente de minería de texto / OCR |
| `inconsistente` (flag) | Marca errores de carga (ej. Finalizada con avance < 80%) **sin borrarlos** — se reporta al equipo de Programación en vez de ocultarlos |
| `criterio_enc` (manual) | El encoding automático ordenaría alfabético; el manual conserva Inclusión < Otro < Exclusión |
| Columnas `_norm` | MinMax evita que `dias_activa` (0–600) aplaste a `avance_obra` (0–100) |

Nota al pie: "No se modifica el dato original: el preprocesamiento genera un dataset nuevo, trazable y reproducible."

---

### Slide 7 — Sección 05: EDA — Hallazgos clave
Cabecera de sección: `05 · EDA` (fondo índigo, texto blanco)
Subtítulo: "Cinco notebooks · Cada análisis parte de una pregunta del área"

Cuatro hallazgos en tarjetas con número grande:

1. **El plazo de obra es de 90 días, pero el ~85% de las viviendas terminadas lo superó** (promedio real ~167 días) y el ~58% de las obras activas ya está vencida
2. **~70%** de las obras activas no recibió ninguna visita técnica — el avance reportado por las ONGs no está verificado en terreno
3. **Mampostería**: la etapa estructural con mayor concentración de obras bloqueadas y la tasa de parálisis más alta de toda la cadena constructiva
4. **Discrepancia ONG vs. técnico**: en promedio las ONGs sobreestiman el avance — señal de alerta de reporte inflado

---

### Slide 8 — Sección 06: Modelo de riesgo
Cabecera de sección: `06 · MODELO DE RIESGO` (fondo índigo, texto blanco)
Subtítulo: "Detectar obras en riesgo antes de que se paralicen"

**Cómo se calcula (regla, no caja negra):**
```python
PLAZO = 90  # plazo contractual de construcción (días)
vencida = (df['estado'].isin(['Iniciada','Avanzada'])
           & (df['dias_activa'] > PLAZO))
# alto: vencida y casi sin avance · medio: vencida pero avanzando
```
> Obra activa que **superó el plazo de 90 días** y todavía no está por terminar = EN RIESGO
> *(El plazo de 90 días es el contractual de la etapa de construcción)*

**Tres niveles:**
- 🔴 **Riesgo alto**: pasó los 90 días, avance < 30%
- 🟡 **Riesgo medio**: pasó los 90 días, avance 30–80%
- 🟢 **Sin riesgo**: en plazo, terminada, o vencida pero casi lista (≥80%)

**Por qué una regla y no un modelo complejo:** el ministerio necesita poder *explicar y auditar* por qué una obra está marcada en riesgo. Una regla transparente es defendible ante una ONG; una caja negra no.

**Resultado sobre el dataset:** ~21% riesgo alto · ~14% riesgo medio · ~65% sin riesgo. Se concentran en Capital y Banda.

**Integración con el portal Next.js:** Python escribe `nivel_riesgo` en la base de datos → Java API lo expone → el ministerio lo ve en el dashboard institucional sin intervención adicional.

---

### Slide 9 — Sección 07: Los dos cuellos de botella
Cabecera de sección: `07 · LOS DOS CUELLOS DE BOTELLA` (fondo índigo, texto blanco)
Subtítulo: "Una obra no avanza por dos razones distintas — y se resuelven distinto"

Diseño de dos columnas, una por cuello de botella:

**Columna izquierda — Cuello CONSTRUCTIVO (rubros AFO):**
El AFO es la suma ponderada de **15 rubros secuenciales**: el rubro N solo arranca cuando el N-1 terminó.
`Terreno → Excavación → Mampostería → Revoques → Carpintería → Instalaciones → Terminaciones`
- **Etapa activa** = punto exacto de la cadena donde la obra está detenida
- Obras en riesgo alto → bloqueadas en **Mampostería** (falta de cuadrilla o materiales)
- *Solución: enviar materiales / cuadrillas a esa etapa*

**Columna derecha — Cuello ADMINISTRATIVO (actas):**
Una obra **100% construida** queda en estado `Finalizada` esperando el **acta de finalización** para pasar a `Adjudicada` (entregada). El trámite se demora por falta de seguimiento.
- **~45%** de las obras finalizadas tienen el acta **atascada** (>180 días esperando)
- Espera promedio: **~210 días** de viviendas terminadas sin entregar
- *Solución: destrabar papeles, no construcción — el arreglo más rápido del programa*

Highlight central: "El ministerio puede confundir ambos. Separarlos permite mandar al lugar correcto: la cuadrilla a la obra, o el técnico a hacer el acta."

---

### Slide 10 — Sección 08: Cómo calculamos los indicadores
Cabecera de sección: `08 · CÓMO CALCULAMOS LOS INDICADORES` (fondo índigo, texto blanco)
Subtítulo: "Sobre qué base se construye cada número — sin abrir el notebook"

Objetivo del slide: mostrar el **método** de los dos indicadores más ricos (notebook 04), no todo el código. Layout de dos bloques, cada uno con la fórmula/criterio + la decisión de diseño.

**Bloque 1 — Índice de Confiabilidad de ONG**
Caja monoespaciada con la fórmula:
```python
confiab = (0.50 * avance_promedio          # ¿entregan obra?
         + 0.30 * (100 - pct_en_riesgo)    # ¿se les paralizan?
         + 0.20 * (100 - sobreestimacion)) # ¿reportan honesto?
```
- **En base a qué:** se cruza cada visita técnica con la ONG gestora para medir cuánto sobreestima respecto de lo verificado en terreno.
- **Decisión:** el avance pesa más que la finalización porque una ONG eficiente con obras en curso sanas no debe penalizarse por no haber terminado todavía.

**Bloque 2 — Etapa activa y actas (los dos cuellos)**
```python
# Etapa activa: primer rubro de la secuencia que no llegó al 98%
etapa_activa = next(r for r in ORDEN if avance_rubro[r] < 98)

# Espera del acta: días desde que la obra terminó sin adjudicarse
dias_espera_acta = (hoy - fecha_fin)   # solo estado 'Finalizada'
```
- **En base a qué:** la restricción de que los rubros son secuenciales permite ubicar la traba exacta; el estado `Finalizada` sin pasar a `Adjudicada` revela la traba administrativa.
- **Decisión:** separar "no avanza por construcción" de "no cierra por trámite" — porque cada uno se resuelve de forma distinta.

Nota al pie: "Todos los indicadores son reglas transparentes y auditables, no modelos caja negra — el ministerio puede explicar cada número ante una ONG."

---

### Slide 11 — Sección 09: Indicadores de gestión
Cabecera de sección: `09 · INDICADORES DE GESTIÓN` (fondo índigo, texto blanco)
Subtítulo: "Cada indicador responde una pregunta concreta del área"

**Indicador destacado — Índice de Confiabilidad de ONG (tarjeta grande):**
Score 0-100 por ONG que combina avance promedio (50%) + ausencia de riesgo (30%) + honestidad del reporte (20%).
- 🟢 ≥70 confiable · 🟡 50-70 seguimiento · 🔴 <50 auditar
- Ejemplo del dataset: Mutual Progreso **100** · San Antonio **80** · Construir Juntos **37 (auditar)**
- Responde: *¿a quién audito, a quién acompaño, a quién dejo trabajar?*

**Tabla de KPIs operativos:**

| KPI | Valor aprox. | Decisión que habilita |
|---|---|---|
| Tasa de finalización | ~42% | Reportar avance al gobierno provincial |
| Obras en riesgo alto | ~21% | Identificar obras que necesitan visita urgente |
| Actas atascadas | ~158 obras | Destrabar entregas frenadas por trámite |
| Etapa cuello de botella | Mampostería | Priorizar asistencia técnica en esa etapa |
| Cobertura geográfica activa | 18 de 18 depts. | Optimizar recorridos de técnicos |

Nota: "El índice de confiabilidad y el indicador de actas son aportes nuevos del Hito 2, nacidos de problemáticas reales relevadas con el área."

---

### Slide 12 — Sección 10: Equipo técnico
Cabecera de sección: `10 · EQUIPO TÉCNICO` (fondo índigo, texto blanco)
Subtítulo: "El recurso más escaso del programa: la visita técnica"

**Columna izquierda — Score de priorización de visitas:**
Con **~70% de obras activas sin visitar**, el técnico no puede ir a todas. El score las ordena por:
- Nivel de riesgo + tiempo expuesto sin verificación + historial de la ONG gestora
- Produce un **Top de obras a visitar** listo para terreno, sin criterio subjetivo
- Responde: *¿a qué obra voy primero mañana?*

**Columna derecha — Alerta de sobre-reporte:**
Obras activas con **avance alto reportado pero cero visitas** — nadie confirmó ese avance.
- Se agrava si la ONG gestora tiene historial de sobreestimar
- Apunta al control y la transparencia: dónde el programa certifica sobre datos no validados
- Responde: *¿dónde puede haber sobre-reporte?*

Highlight: "Las ONGs sobreestiman el avance en promedio. El técnico Ibáñez (sobrecargado, 40% de cobertura) tiene el mayor volumen de obras sin verificación del equipo."

---

### Slide 13 — Sección 11: Dashboard Streamlit
Cabecera de sección: `11 · DASHBOARD STREAMLIT` (fondo índigo, texto blanco)
Subtítulo: "Cinco páginas interactivas — 100% Python"

Grid de 5 tarjetas, una por página:

| Página | Qué muestra |
|---|---|
| 🏘 Viviendas | Filtros por criterio/clasificación, mapa GPS coloreado por riesgo, distribuciones |
| 🤝 ONGs | Rendimiento comparativo, obras en riesgo por ONG, detalle por organización |
| 🔬 Minería | Modelo de riesgo interactivo, análisis de rubros AFO, tiempos de ejecución |
| 👷 Equipo técnico | Cobertura, discrepancias, alertas de obras sin visita (vista del jefe de área) |
| 🗂 Mis obras | Cola de prioridad, mapa de zona coloreado por estado de visita (vista del técnico) |

Nota: "El dashboard consume el mismo dataset que los notebooks. Para conectar con la API real: una variable de entorno en `.env`."

---

### Slide 14 — Sección 12: Portal ONGs (Frontend Next.js)
Cabecera de sección: `12 · PORTAL ONGs — FRONTEND INSTITUCIONAL` (fondo índigo, texto blanco)
Subtítulo: "Cierra la brecha entre las dos visitas técnicas"

**El problema que resuelve:**
> Los técnicos hacen máximo 2 visitas por obra. Sin evidencia intermedia, el programa va de 0% a 100% sin visibilidad.

**Solución implementada:**
- Portal separado con login propio para ONGs (verde esmeralda, diferenciado del ministerio)
- La ONG carga reportes de avance con fotos por etapa
- El ministerio ve los reportes en su dashboard con los datos completos de la ONG gestora

**En números:**
- 100 viviendas mock distribuidas en 18 departamentos
- 3 ONGs con perfiles diferenciados: eficiente, con problemas, finalizada
- Dashboard ministerio: 6 KPIs + 4 gráficos + tabla de todas las organizaciones

---

### Slide 15 — Cierre
- Título grande: **"HASTA ACÁ LLEGAMOS"**
- Subtítulo: "Gracias"
- Texto pequeño: "Estamos a disposición para profundizar en cualquier aspecto técnico, metodológico o de alcance del proyecto."
- Equipo: "Pablo Castillo · Sara Lombardi · Valeria Martinetti · Santiago Gallardo · Enzo Pazzelli"
- Pie: "Práctica Profesionalizante II · ITSE — Ciencia de Datos"

---

## Instrucciones de estilo adicionales

- El número de slide va abajo a la derecha en formato `X / 15`
- Los slides de cabecera de sección usan fondo índigo sólido (#4F46E5) con texto blanco — el resto del slide tiene fondo blanco/gris claro
- Los datos numéricos destacados van en tipografía grande (48–64 pt) en índigo (#4F46E5)
- Las tablas usan encabezado índigo (#4F46E5) con texto blanco; filas alternadas en #F8FAFC
- Los iconos de estado (semáforo suave): 🔴 rosa (#F43F5E), 🟡 ámbar (#F59E0B), 🟢 esmeralda (#10B981)
- Los diagramas de flujo van de izquierda a derecha con flechas → en índigo
- Las líneas divisoras entre secciones: color gris claro (#E2E8F0), 1pt
- Márgenes internos generosos (2–3 cm)

---

## Nota final

Esta presentación continúa directamente el Hito 1 (`PP2_Hito1_Grupo8_v2.pptx`).
El mismo equipo, el mismo proyecto, el mismo cliente. El tono es técnico pero accesible — el receptor es el profesor y el subsecretario del ministerio.
El diseño cambió a fondo claro para mejorar la legibilidad en proyecciones con luz ambiente.
