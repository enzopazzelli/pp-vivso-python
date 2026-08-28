# Informe de Análisis Exploratorio de Datos (EDA)
## Sistema VIVSO — Componente de Ciencia de Datos

**Práctica Profesionalizante PP2 · ITSE · Tecnicatura en Ciencia de Datos e IA**
**Equipo:** Pablo Castillo · Sara Lombardi · Valeria Martinetti · Santiago Gallardo · Enzo Pazzelli
**Entidad:** Subsecretaría de Promoción Humana — Ministerio de Desarrollo Social, Santiago del Estero
**Fecha:** junio 2026

> Este informe consolida el análisis exploratorio del programa de viviendas sociales: dataset,
> preprocesamiento, hallazgos univariados y bivariados con tablas de apoyo, modelo de riesgo e
> indicadores de gestión. Es un documento autocontenido: todas las cifras se calculan
> directamente sobre el dataset y pueden reproducirse con los pasos de la sección 8.

> **Cifras recalculadas el 2026-08-28** sobre el modelo de datos nuevo: las organizaciones
> gestoras pasaron de 3 a 8 y de un solo tipo a cuatro (municipio, comisión municipal, ONG,
> cooperativa), y se eliminó el 20% de obras "sin gestora" —el supuesto **[S9]**, que resultó
> imposible: la gestora es quien solicita las viviendas—. Todas las tablas y valores de las
> secciones 4 a 6 salen de ese dataset; las figuras de `docs/figuras/` se regeneraron en la
> misma pasada. Los hallazgos estructurales se mantienen; el único que cambió de lectura es
> el **5.1**, que ahora da significativo y se explica ahí por qué igual no es un hallazgo.

---

## 1. Introducción

### 1.1 Contexto y problema

La Subsecretaría de Promoción Humana gestiona un programa de viviendas sociales con obras
distribuidas en **18 departamentos** de la provincia, ejecutadas por **organizaciones
gestoras** —municipios, comisiones municipales, ONGs y cooperativas— bajo convenio, y
supervisadas por **técnicos** del ministerio. La gestora es quien **solicita** las viviendas
y se hace cargo de la obra: el ministerio no construye ni manda cuadrillas. El
programa está asociado al **Programa Chagas** (mejora habitacional para erradicar el vector).

Antes de VIVSO, la información vivía en tres sistemas legacy desconectados (App GPS, VISOC y
GEDO) y en planillas de papel. El problema central es de **visibilidad y control**:

- ¿Cuántas obras están en riesgo de no terminar a tiempo, y dónde?
- ¿Qué gestoras cumplen y cuáles necesitan seguimiento urgente?
- ¿En qué etapa constructiva se bloquean las obras?
- ¿El avance que reportan las gestoras coincide con lo que verifica el técnico?

### 1.2 Objetivos del análisis

1. Caracterizar el estado del programa con datos estructurados (no narrativos).
2. Construir un **modelo de riesgo transparente** que priorice qué obras atender primero.
3. Producir **indicadores de gestión accionables** (cada uno habilita una decisión concreta).
4. Entregar un **prototipo funcionando** (dashboard interactivo) que ponga el análisis frente a
   cada rol.

### 1.3 Encuadre metodológico

El proyecto combina dos tipos de solución de la cátedra:

| Tipo de solución | Componente en VIVSO |
|---|---|
| **Panel** (tablero de indicadores para dirección pública) | Dashboard con KPIs, mapa de riesgo y vistas por rol |
| **Pipeline** (ETL reproducible) | Extracción y generación sintética → base local → datasets procesados |

El análisis cubre las etapas **3 (Preprocesamiento), 4 (EDA) y 5 (Modelo)** del mapa de la
práctica.

---

## 2. El dataset

### 2.1 Origen y estrategia de datos

El backend Java del equipo de Programación está en desarrollo. Mientras no haya datos reales,
el componente Python genera un **dataset sintético** que reproduce las distribuciones
geográficas y las reglas de negocio reales del programa, sin exponer datos de beneficiarios.
Cuando el backend esté disponible, el pipeline cambia de fuente con una sola variable de
entorno (`API → MySQL → CSV sintético`) sin tocar una línea de análisis.

### 2.2 Composición

| Tabla | Registros | Descripción |
|---|---|---|
| `vivienda` | **1.500** | Una fila por expediente de obra |
| `organizacion` | 8 | Gestoras con sus datos institucionales: 2 municipios, 2 comisiones municipales, 2 ONGs, 2 cooperativas |
| `tecnico` | 6 | Técnicos con zona de cobertura |
| `asignacion` | 908 | Qué obras tiene asignadas cada técnico |
| `visita` | **1.057** | Cada visita de campo con avance verificado |
| `avance_rubro` | 22.500 | Avance de cada una de las 15 etapas por obra |

### 2.3 Variables clave de cada vivienda

`num_exp` (expediente) · `estado` (Iniciada/Avanzada/Finalizada/Adjudicada) ·
`avance_obra` (AFO 0–100%) · `dias_activa` (derivada) · `clasificacion` (15 códigos) ·
`criterio` (Inclusión/Exclusión/Otro) · `nivel_riesgo` (derivada) · `cuit_org` (gestora, sin nulos) ·
`lat`/`lng` (GPS) · `tipo_vivienda` (Urbana/Rural/Económica).

### 2.4 Dominio: clasificaciones y AFO

- **Clasificación:** código VISOC de dos caracteres (15 posibles) agrupado en `criterio`:
  **Inclusión** (apta), **Exclusión** (rechazada), **Otro** (caso especial).
- **AFO (Avance Físico de Obra):** porcentaje 0–100 calculado como **suma ponderada de 15
  rubros estrictamente secuenciales** — el rubro N solo arranca cuando el N-1 terminó. Esta
  restricción permite, dado un AFO, identificar **en qué etapa exacta está cada obra**.

---

## 3. Preprocesamiento (etapa 3)

El dataset crudo no es directamente analizable: fechas como texto, categóricas como strings y
escalas numéricas dispares. El preprocesamiento produce un dataset procesado nuevo (no modifica
el original) con estas transformaciones, cada una justificada:

| Transformación | Justificación técnica | Justificación de negocio |
|---|---|---|
| Fechas `texto → datetime` | No se puede restar texto | `dias_activa` requiere aritmética de fechas |
| `dias_activa` (derivada) | No está en el origen | Variable central del modelo de riesgo |
| `anio_inicio` (derivada) | Análisis temporal | Tendencia del programa año a año |
| Inconsistencias **marcadas, no borradas** | Trazabilidad | Informar a Programación qué corregir en el sistema |
| Encoding **manual** de `criterio` | Preserva orden Inclusión→Otro→Exclusión | El encoding alfabético rompería la jerarquía |
| `MinMaxScaler` a [0,1] | Escala uniforme | `dias_activa` (0–600) dominaría sobre `avance` (0–100) |

---

## 4. Análisis exploratorio univariado (etapa 4)

### 4.1 Estado del programa

De las 1.500 obras, **908 están en obra** (Iniciada + Avanzada) y **592 terminadas**
(Finalizada + Adjudicada) → **tasa de finalización del 39,5%**.

| Estado | Cantidad | % del total |
|---|---:|---:|
| Iniciada | 473 | 31,5% |
| Avanzada | 435 | 29,0% |
| Finalizada | 347 | 23,1% |
| Adjudicada | 245 | 16,3% |
| **Total** | **1.500** | **100,0%** |

### 4.2 Criterio de inclusión

Predomina **Inclusión** (894 obras, el caso típico de intervención), seguido de **Otro** (404)
y **Exclusión** (202). La presencia de obras con criterio Exclusión que muestran avance es una
señal a vigilar: puede indicar errores de selección de beneficiario en el origen.

| Criterio | Cantidad | % del total |
|---|---:|---:|
| Inclusión | 894 | 59,6% |
| Otro | 404 | 26,9% |
| Exclusión | 202 | 13,5% |

### 4.3 Distribución del AFO

El AFO promedio es del **60,6%** (desvío estándar 35,2 puntos; mediana 69%). La distribución no
es uniforme: hay una fuerte concentración de obras recién iniciadas (0–20% de avance) y una
concentración aún mayor de obras cercanas o iguales a 100% (las terminadas).

| Rango de AFO | Cantidad de obras | % del total |
|---|---:|---:|
| 0–20% | 317 | 21,1% |
| 20–40% | 193 | 12,9% |
| 40–60% | 153 | 10,2% |
| 60–80% | 199 | 13,3% |
| 80–100% | 638 | 42,5% |

### 4.4 Distribución geográfica

Las obras se concentran en los departamentos más poblados (Capital, Banda), pero hay presencia
en los 18 departamentos. Esta distribución es la que determina la logística de visitas técnicas.

| Departamento | Obras | % del total |
|---|---:|---:|
| Capital | 344 | 22,9% |
| Banda | 238 | 15,9% |
| Robles | 123 | 8,2% |
| Silípica | 86 | 5,7% |
| Jiménez | 83 | 5,5% |
| Choya | 82 | 5,5% |
| Moreno | 73 | 4,9% |
| Mitre | 62 | 4,1% |
| General Taboada | 59 | 3,9% |
| Figueroa | 58 | 3,9% |
| Salavina | 47 | 3,1% |
| Copo | 47 | 3,1% |
| Aguirre | 40 | 2,7% |
| Atamisqui | 36 | 2,4% |
| Rivadavia | 35 | 2,3% |
| Ojo de Agua | 33 | 2,2% |
| Guasayán | 28 | 1,9% |
| Pellegrini | 26 | 1,7% |

### 4.5 Nivel de riesgo (primer diagnóstico)

**306 obras (20,4%) están en riesgo alto** y 274 (18,3%) en riesgo medio. Algo más de seis de
cada diez están sin riesgo. El detalle del modelo que produce esta clasificación está en la
sección 6.

| Nivel de riesgo | Cantidad | % del total |
|---|---:|---:|
| Alto | 306 | 20,4% |
| Medio | 274 | 18,3% |
| Sin riesgo (bajo) | 920 | 61,3% |

---

## 5. Análisis bivariado e inferencial (etapa 4)

Esta sección parte de **hipótesis de negocio** y las contrasta con los datos. Se reportan
también los resultados **negativos**: un hallazgo "no hay diferencia" es información válida.

### 5.1 ¿El criterio de inclusión explica el avance? — **No de forma utilizable**

Hipótesis: las obras de criterio Exclusión avanzarían menos que las de Inclusión.

| Criterio | Obras | Avance medio | Riesgo alto |
|---|---:|---:|---:|
| Inclusión | 894 | 61,7% | 20,2% |
| Otro | 404 | 61,3% | 18,8% |
| Exclusión | 202 | 54,7% | 24,3% |

El ANOVA da **F = 3,35, p = 0,036**: con el umbral habitual del 5%, la diferencia de avance es
*estadísticamente* significativa. Pero eso no la vuelve un hallazgo, por tres razones:

1. **El efecto es chico** — 7 puntos de AFO sobre desvíos de ~35. Con n = 1.500 una diferencia
   así alcanza significancia sin tener relevancia práctica.
2. **El riesgo no acompaña** — la tasa de riesgo alto no difiere entre criterios
   (χ² = 2,49, **p = 0,29**). Si el criterio realmente frenara las obras, debería verse acá.
3. **El generador no codifica ninguna relación entre criterio y avance.** El avance se deriva
   del estado de la obra y la clasificación se sortea aparte. O sea: sabemos que la relación
   no existe en el proceso que produjo estos datos.

**Conclusión:** el criterio no es un predictor utilizable del avance; el atraso es transversal.
Y el caso sirve de advertencia metodológica sobre el propio dataset — **un p-valor significativo
sobre datos sintéticos no es un hallazgo del programa**, es una propiedad de la muestra. Zanjarlo
de verdad requiere datos reales.

### 5.2 ¿El tipo de vivienda explica la duración? — **No (ANOVA no significativo)**

Hipótesis: las viviendas rurales tardarían más por dificultad de acceso. Se aplicó **ANOVA**
(tres grupos: Urbana/Rural/Económica) en lugar de t-tests múltiples para no inflar el error
tipo I sobre las 592 obras terminadas (única población con duración real conocida).

| Tipo de vivienda | Obras terminadas | Duración media (días) |
|---|---:|---:|
| Urbana | 342 | 172,6 |
| Rural | 197 | 169,4 |
| Económica | 53 | 188,9 |

Resultado: **F = 1,80, p = 0,17** → no hay diferencia estadísticamente significativa (de hecho
las rurales promedian menos días que las urbanas).

**Implicancia metodológica:** confirmar o descartar esta relación de forma definitiva requiere
**datos reales** — el generador sintético no codificó esa diferencia. Queda como hipótesis a
revisar en PP3 cuando se integre la base del backend.

### 5.3 ¿Qué clasificaciones concentran el riesgo? — **Sí hay señal**

Las obras en riesgo alto se concentran en las clasificaciones más frecuentes del programa: **2a
(Precaria, 74 obras), 1a (Rancho, 59) y 2b (riesgo de derrumbe, 33)**. Esto permite al
ministerio priorizar la supervisión de esos códigos desde el inicio.

---

## 6. Modelo de riesgo e indicadores de gestión (etapa 5)

### 6.1 Modelo de riesgo (el hallazgo central)

**Definición (regla transparente, no caja negra):** una obra es de riesgo si está activa, ya
**superó el plazo contractual de 90 días** y todavía no está por terminar (avance < 80%).

- 🔴 **Riesgo alto:** vencida y avance < 30% (prácticamente paralizada).
- 🟡 **Riesgo medio:** vencida y avance 30–80% (avanza, pero atrasada).
- 🟢 **Sin riesgo:** el resto.

Se eligió una **regla y no un modelo de ML** a propósito: el ministerio debe poder **explicar
el número ante una gestora**. Los dos umbrales (90 días de plazo y 80% de avance) separan
limpiamente las tres bandas: por debajo de 90 días ninguna obra activa entra en riesgo;
superado ese plazo, el nivel de avance divide entre riesgo medio (≥30%) y riesgo alto (<30%).

**Hallazgo estructural:** el atraso no es la excepción sino la norma. El **85,5% de las obras
terminadas superó los 90 días** (duración media real **173 días**, casi el doble del plazo) y
el **63,9% de las obras activas ya está vencido**. Por eso el indicador no marca "las pocas que
se atrasan", sino "las que, además de vencidas, no están avanzando".

### 6.2 Cuello de botella constructivo

Aprovechando la secuencialidad de los rubros, para cada obra activa se identifica su **etapa
activa** (el primer rubro que no llegó al 98%). El cuello de botella del programa es claro:
**171 obras activas están trabadas en "Mampostería hasta dintel"** (rubro 3), la etapa
estructural más pesada. Sumado al rubro 4, la mampostería concentra **279 obras (30,7%)**.

| Rubro (etapa constructiva) | Obras activas | % de las 908 activas |
|---|---:|---:|
| 3 · Mampostería hasta dintel | 171 | 18,8% |
| 4 · Mampostería cerámico/Block | 108 | 11,9% |
| 10 · Carpintería | 93 | 10,2% |
| 2 · Excavación e impermeabilización | 84 | 9,3% |
| 6 · Revoque interior | 75 | 8,3% |
| 11 · Instalación de agua | 62 | 6,8% |
| 7 · Revoque exterior | 60 | 6,6% |
| 12 · Instalación eléctrica | 59 | 6,5% |
| 5 · Encadenado | 57 | 6,3% |
| 8 · Cielorraso con aislante térmico | 49 | 5,4% |
| 1 · Terreno y limpieza | 33 | 3,6% |
| 9 · Construcción de cielorrasos | 26 | 2,9% |
| 13 · Instalación sanitaria | 14 | 1,5% |
| 15 · Varios | 10 | 1,1% |
| 14 · Revestimiento exterior | 7 | 0,8% |

Como la construcción es responsabilidad de la **organización gestora** (el ministerio no manda
cuadrillas), este dato permite reclamar con **precisión de etapa** a cada gestora y focalizar
las visitas de verificación, en lugar de solo saber que "la obra no avanza".

### 6.3 Cuello de botella administrativo (actas)

El segundo cuello de botella del programa no es constructivo: una obra puede estar **100%
construida** y seguir sin entregarse. El estado `Finalizada` significa "la obra terminó"; para
pasar a `Adjudicada` (entregada a la familia) falta tramitar el **acta de finalización**, y ese
trámite se demora por falta de seguimiento.

De las **347 obras en estado Finalizada, 156 (45%) tienen el acta atascada** — más de 6 meses
esperando trámite, con una espera promedio de **~370 días** dentro de ese grupo (~212 días en
promedio si se cuentan todas las finalizadas, atascadas o no).

**Por qué importa distinguir los dos cuellos de botella:** se resuelven distinto. El
constructivo (sección 6.2) necesita materiales o cuadrillas de la gestora; el administrativo se
resuelve **destrabando papeles** — es la intervención más rápida y barata que tiene el
ministerio a mano, y hoy nadie la está midiendo.

### 6.4 Confiabilidad de las gestoras (sobre-reporte y cobertura)

Cruzando las visitas técnicas con el avance reportado por las gestoras surge la **discrepancia**
(`diferencia_ong` = reportado − verificado; el nombre de la columna quedó del modelo anterior).
El **62,8% de las visitas detecta sobre-reporte** (la gestora reporta más avance del verificado),
con una media de **+3,18 puntos** y picos de **+15**.

| Gestora | Tipo | Sobre-reporte medio (puntos de AFO) | Cobertura de verificación |
|---|---|---:|---:|
| Mutual Progreso Familiar | ONG | sin verificación | 0,0% |
| Coop. de Trabajo El Porvenir | Cooperativa | +3,98 | 41,7% |
| Municipalidad de La Banda | Municipio | +2,59 | 42,9% |
| Comisión Municipal de Tintina | Comisión Municipal | +4,14 | 44,1% |
| Municipalidad de Frías | Municipio | +3,21 | 45,0% |
| Comisión Municipal de Pinto | Comisión Municipal | +3,40 | 51,0% |
| Coop. de Trabajo San Antonio | Cooperativa | +3,37 | 69,0% |
| Asoc. Civil Construir Juntos | ONG | +2,26 | 72,5% |

El caso más crítico no es de sobre-reporte sino de **falta total de control**: la **Mutual
Progreso Familiar tiene 0% de sus obras verificadas** (0 de 171) — está en estado Finalizada y
su avance nunca pasó por una visita técnica. Y el resto tampoco está parejo: la cobertura va del
**41,7% al 72,5%**, una brecha de 30 puntos entre gestoras del mismo programa.

> La columna *Tipo* es descriptiva. **No se lee como comparación entre tipos de gestora**: la
> distribución de obras por tipo es hoy el supuesto **[S16]**, un reparto parejo puesto a mano
> mientras el área no confirme las proporciones reales. Segmentar los indicadores por tipo es
> trabajo de PP3, con dato validado.

### 6.5 Síntesis de indicadores

El programa se resume en siete KPIs operativos, cada uno pensado para habilitar una decisión
concreta (regla de diseño estricta: **un KPI que no habilita una decisión no entra**):

1. **Tasa de finalización** — % de obras completadas sobre el total. Habilita reportar avance
   al gobierno provincial con un número concreto en lugar de un relato.
2. **Obras en riesgo alto** — vencidas (>90 días) y avance <30%. Habilita priorizar visitas
   técnicas y activar el protocolo de seguimiento de la gestora responsable.
3. **Obras en riesgo medio** — vencidas y avance 30–80%. Habilita seguimiento preventivo antes
   de que la obra escale a riesgo alto.
4. **Tiempo promedio de ejecución** (solo obras terminadas, para no sesgar con obras en curso)
   — habilita comparar el desempeño de cada gestora contra el promedio del programa.
5. **Rendimiento por gestora** — avance, riesgo y días promedio por organización. Habilita
   decisiones de pago, frecuencia de visitas o revisión contractual.
6. **Cobertura geográfica activa** — obras en curso por departamento. Habilita la planificación
   de recorridos técnicos.
7. **Etapa cuello de botella** — rubro constructivo donde se acumulan más obras activas.
   Habilita el reclamo a la gestora con precisión de etapa.

Estos KPIs están materializados en un prototipo funcional (dashboard interactivo) con vistas
diferenciadas por rol: subsecretario, jefe de área técnica y técnico individual.

---

## 7. Conclusiones

### 7.1 As is → To be

| Dimensión | Antes (As is) | Ahora (To be) |
|---|---|---|
| **Visibilidad** | 3 sistemas desconectados + papel | Panel único: 1.500 obras y mapa de riesgo en un pantallazo |
| **Priorización de visitas** | El técnico elige por cercanía o criterio propio | Cola ordenada por riesgo; **74 obras en riesgo alto sin ninguna visita** quedan visibles |
| **Control de gestoras** | El avance reportado se acepta sin contraste | Se mide el sobre-reporte (**+3,18 pts, 63% de visitas**) y la cobertura (**una gestora al 0%**) |
| **Diagnóstico de obra** | "La obra no avanza" | "Está trabada en *Mampostería hasta dintel*" (171 obras) |
| **Entrega de vivienda terminada** | Nadie lo mide; se descubre cuando reclama la familia | **156 actas atascadas** (45% de las finalizadas) visibles con días de espera |
| **Reporte de gestión** | Narrativo y subjetivo | KPIs concretos: 39,5% finalización · 306 en riesgo alto · 173 días promedio |

### 7.2 Hallazgos principales

1. El **atraso es estructural**, no excepcional: 85% de las terminadas superó el plazo de 90 días.
2. Hay **dos cuellos de botella distintos, y se resuelven distinto**: el constructivo
   (mampostería, 171 obras) necesita materiales o cuadrillas de la gestora; el administrativo
   (156 actas atascadas, 45% de las finalizadas) se resuelve destrabando trámites.
3. Hay **sobre-reporte sistemático** de las gestoras y una organización **sin ningún control**.
4. El criterio de inclusión y el tipo de vivienda **no explican** el avance ni la duración en
   estos datos — el atraso es transversal (resultado honesto, a re-evaluar con datos reales).

### 7.3 Trabajo futuro (PP3)

- Integración con la base real y validación de los hallazgos contra datos reales.
- Materializar los indicadores en tablas de datos consumibles por cualquier front (sin depender
  de notebooks para su cálculo).

---

## 8. Reproducibilidad

Todas las cifras de este informe se calculan directamente sobre el dataset generado por el
pipeline sintético; no hay números editados a mano. Para reproducirlas de punta a punta:

```powershell
python -m db.setup              # crea las tablas y el catálogo de rubros
python -m synthetic.generate    # genera el dataset (1.500 viviendas + visitas + rubros)
jupyter nbconvert --to notebook --execute --inplace colab/01_exploracion.ipynb
jupyter nbconvert --to notebook --execute --inplace colab/02_normalizacion.ipynb
jupyter nbconvert --to notebook --execute --inplace colab/03_correlaciones.ipynb
jupyter nbconvert --to notebook --execute --inplace colab/04_indicadores.ipynb
jupyter nbconvert --to notebook --execute --inplace colab/05_tecnicos.ipynb
streamlit run dashboard/app.py  # levanta el prototipo interactivo
```

Requisitos: Python 3.13, entorno virtual con `pandas`, `numpy`, `scipy`, `scikit-learn`,
`jupyter` y `streamlit` instalados. La generación sintética es determinística por semilla, por
lo que dos ejecuciones producen el mismo dataset y, por lo tanto, las mismas cifras reportadas
aquí.

---

## 9. Glosario

| Término | Significado |
|---|---|
| **AFO** | Avance Físico de Obra. Porcentaje de completitud de una vivienda, calculado como suma ponderada de los 15 rubros constructivos. |
| **Rubro** | Cada una de las 15 etapas de construcción que componen el AFO. Tienen pesos distintos y son estrictamente secuenciales. |
| **Etapa activa** | El rubro donde está actualmente detenida una obra — el primero de la secuencia que no llegó al 98%. |
| **Cuello de botella** | La etapa donde se concentra la mayor cantidad de obras activas simultáneamente. |
| **Criterio** | Macrocategoría del código de clasificación: Inclusión (apta), Exclusión (rechazada), Otro (caso especial). |
| **Clasificación** | Código de dos caracteres (1a, 2b, 5g, etc.) que describe el tipo de vivienda según el sistema VISOC. |
| **Nivel de riesgo** | Clasificación calculada por el pipeline: alto (vencida >90 días y AFO <30%), medio (vencida >90 días y AFO 30–80%), bajo (resto). |
| **Organización gestora** | Quien solicita las viviendas y se hace cargo de la obra. Puede ser un **municipio**, una **comisión municipal**, una **ONG** o una **cooperativa** (`tipo_gestora`). El *ámbito* las agrupa en público y privado. |
| **Discrepancia gestora vs. técnico** | Diferencia entre el avance que reporta la gestora y el que verifica el técnico en la visita. Positivo = la gestora sobreestimó. |
| **Cobertura de visitas** | Porcentaje de obras asignadas (o de una gestora) que recibieron al menos una visita técnica. |
| **ANOVA** | Analysis of Variance. Test estadístico que evalúa si las medias de más de dos grupos son significativamente distintas. |
| **MinMaxScaler** | Técnica de normalización que lleva todas las variables numéricas al rango [0,1] para que ninguna domine por su magnitud. |
| **VISOC** | Sistema legacy del ministerio que registraba las viviendas sociales antes de VIVSO. Define los 15 códigos de clasificación. |
