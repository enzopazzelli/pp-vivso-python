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

---

## 1. Introducción

### 1.1 Contexto y problema

La Subsecretaría de Promoción Humana gestiona un programa de viviendas sociales con obras
distribuidas en **18 departamentos** de la provincia, ejecutadas por **Organizaciones No
Gubernamentales (ONGs)** bajo contrato y supervisadas por **técnicos** del ministerio. El
programa está asociado al **Programa Chagas** (mejora habitacional para erradicar el vector).

Antes de VIVSO, la información vivía en tres sistemas legacy desconectados (App GPS, VISOC y
GEDO) y en planillas de papel. El problema central es de **visibilidad y control**:

- ¿Cuántas obras están en riesgo de no terminar a tiempo, y dónde?
- ¿Qué ONGs cumplen y cuáles necesitan seguimiento urgente?
- ¿En qué etapa constructiva se bloquean las obras?
- ¿El avance que reportan las ONGs coincide con lo que verifica el técnico?

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
| `organizacion` | 3 | ONGs gestoras con sus datos institucionales |
| `tecnico` | 6 | Técnicos con zona de cobertura |
| `asignacion` | 901 | Qué obras tiene asignadas cada técnico |
| `visita` | **1.057** | Cada visita de campo con avance verificado |
| `avance_rubro` | 22.500 | Avance de cada una de las 15 etapas por obra |

### 2.3 Variables clave de cada vivienda

`num_exp` (expediente) · `estado` (Iniciada/Avanzada/Finalizada/Adjudicada) ·
`avance_obra` (AFO 0–100%) · `dias_activa` (derivada) · `clasificacion` (15 códigos) ·
`criterio` (Inclusión/Exclusión/Otro) · `nivel_riesgo` (derivada) · `cuit_org` (ONG, ~21% nulo) ·
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

De las 1.500 obras, **901 están en obra** (Iniciada + Avanzada) y **599 terminadas**
(Finalizada + Adjudicada) → **tasa de finalización del 39,9%**.

| Estado | Cantidad | % del total |
|---|---:|---:|
| Iniciada | 409 | 27,3% |
| Avanzada | 492 | 32,8% |
| Finalizada | 329 | 21,9% |
| Adjudicada | 270 | 18,0% |
| **Total** | **1.500** | **100,0%** |

### 4.2 Criterio de inclusión

Predomina **Inclusión** (871 obras, el caso típico de intervención), seguido de **Otro** (419)
y **Exclusión** (210). La presencia de obras con criterio Exclusión que muestran avance es una
señal a vigilar: puede indicar errores de selección de beneficiario en el origen.

| Criterio | Cantidad | % del total |
|---|---:|---:|
| Inclusión | 871 | 58,1% |
| Otro | 419 | 27,9% |
| Exclusión | 210 | 14,0% |

### 4.3 Distribución del AFO

El AFO promedio es del **64,9%** (desvío estándar 35,7 puntos; mediana 78%). La distribución no
es uniforme: hay una fuerte concentración de obras recién iniciadas (0–20% de avance) y una
concentración aún mayor de obras cercanas o iguales a 100% (las terminadas).

| Rango de AFO | Cantidad de obras | % del total |
|---|---:|---:|
| 0–20% | 325 | 21,7% |
| 20–40% | 123 | 8,2% |
| 40–60% | 136 | 9,1% |
| 60–80% | 190 | 12,7% |
| 80–100% | 726 | 48,4% |

### 4.4 Distribución geográfica

Las obras se concentran en los departamentos más poblados (Capital, Banda), pero hay presencia
en los 18 departamentos. Esta distribución es la que determina la logística de visitas técnicas.

| Departamento | Obras | % del total |
|---|---:|---:|
| Capital | 340 | 22,7% |
| Banda | 255 | 17,0% |
| Silípica | 106 | 7,1% |
| Robles | 105 | 7,0% |
| Choya | 81 | 5,4% |
| Jiménez | 75 | 5,0% |
| Moreno | 65 | 4,3% |
| Mitre | 56 | 3,7% |
| Figueroa | 55 | 3,7% |
| General Taboada | 52 | 3,5% |
| Aguirre | 45 | 3,0% |
| Guasayán | 43 | 2,9% |
| Ojo de Agua | 41 | 2,7% |
| Atamisqui | 41 | 2,7% |
| Copo | 38 | 2,5% |
| Rivadavia | 36 | 2,4% |
| Salavina | 35 | 2,3% |
| Pellegrini | 31 | 2,1% |

### 4.5 Nivel de riesgo (primer diagnóstico)

**316 obras (21,1%) están en riesgo alto** y 204 (13,6%) en riesgo medio. Casi dos tercios están
sin riesgo. El detalle del modelo que produce esta clasificación está en la sección 6.

| Nivel de riesgo | Cantidad | % del total |
|---|---:|---:|
| Alto | 316 | 21,1% |
| Medio | 204 | 13,6% |
| Sin riesgo (bajo) | 980 | 65,3% |

---

## 5. Análisis bivariado e inferencial (etapa 4)

Esta sección parte de **hipótesis de negocio** y las contrasta con los datos. Se reportan
también los resultados **negativos**: un hallazgo "no hay diferencia" es información válida.

### 5.1 ¿El criterio de inclusión explica el avance? — **No**

Hipótesis: las obras de criterio Exclusión avanzarían menos que las de Inclusión. Los datos
**no la sostienen**: el avance promedio es prácticamente igual entre las tres categorías
(Exclusión 63,9% · Inclusión 65,0% · Otro 65,3%), y la tasa de riesgo alto también es pareja
(20–22%). **Conclusión:** en este dataset el criterio no es un predictor del avance; el atraso
es transversal y no se concentra en un tipo de beneficiario.

### 5.2 ¿El tipo de vivienda explica la duración? — **No (ANOVA no significativo)**

Hipótesis: las viviendas rurales tardarían más por dificultad de acceso. Se aplicó **ANOVA**
(tres grupos: Urbana/Rural/Económica) en lugar de t-tests múltiples para no inflar el error
tipo I sobre las 599 obras terminadas (única población con duración real conocida).

| Tipo de vivienda | Obras terminadas | Duración media (días) |
|---|---:|---:|
| Urbana | 332 | 170,4 |
| Rural | 215 | 161,3 |
| Económica | 52 | 174,2 |

Resultado: **F = 1,57, p = 0,21** → no hay diferencia estadísticamente significativa (de hecho
las rurales promedian menos días que las urbanas).

**Implicancia metodológica:** confirmar o descartar esta relación de forma definitiva requiere
**datos reales** — el generador sintético no codificó esa diferencia. Queda como hipótesis a
revisar en PP3 cuando se integre la base del backend.

### 5.3 ¿Qué clasificaciones concentran el riesgo? — **Sí hay señal**

Las obras en riesgo alto se concentran en las clasificaciones más frecuentes del programa: **2a
(Precaria, 74 obras), 1a (Rancho, 61) y 2b (riesgo de derrumbe, 34)**. Esto permite al
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
el número ante una ONG**. Los dos umbrales (90 días de plazo y 80% de avance) separan
limpiamente las tres bandas: por debajo de 90 días ninguna obra activa entra en riesgo;
superado ese plazo, el nivel de avance divide entre riesgo medio (≥30%) y riesgo alto (<30%).

**Hallazgo estructural:** el atraso no es la excepción sino la norma. El **85,1% de las obras
terminadas superó los 90 días** (duración media real **167 días**, casi el doble del plazo) y
el **57,7% de las obras activas ya está vencido**. Por eso el indicador no marca "las pocas que
se atrasan", sino "las que, además de vencidas, no están avanzando".

### 6.2 Cuello de botella constructivo

Aprovechando la secuencialidad de los rubros, para cada obra activa se identifica su **etapa
activa** (el primer rubro que no llegó al 98%). El cuello de botella del programa es claro:
**184 obras activas están trabadas en "Mampostería hasta dintel"** (rubro 3), la etapa
estructural más pesada.

| Rubro (etapa constructiva) | Obras activas | % de las 901 activas |
|---|---:|---:|
| 3 · Mampostería hasta dintel | 184 | 20,4% |
| 2 · Excavación e impermeabilización | 95 | 10,5% |
| 10 · Carpintería | 93 | 10,3% |
| 6 · Revoque interior | 80 | 8,9% |
| 12 · Instalación eléctrica | 69 | 7,7% |
| 4 · Mampostería cerámico/Block | 69 | 7,7% |
| 11 · Instalación de agua | 58 | 6,4% |
| 7 · Revoque exterior | 49 | 5,4% |
| 13 · Instalación sanitaria | 48 | 5,3% |
| 8 · Cielorraso con aislante térmico | 33 | 3,7% |
| 9 · Construcción de cielorrasos | 33 | 3,7% |
| 14 · Revestimiento exterior | 31 | 3,4% |
| 5 · Encadenado | 27 | 3,0% |
| 15 · Varios | 18 | 2,0% |
| 1 · Terreno y limpieza | 14 | 1,6% |

Como la construcción es responsabilidad de la **organización gestora** (el ministerio no manda
cuadrillas), este dato permite reclamar con **precisión de etapa** a cada gestora y focalizar
las visitas de verificación, en lugar de solo saber que "la obra no avanza".

### 6.3 Cuello de botella administrativo (actas)

El segundo cuello de botella del programa no es constructivo: una obra puede estar **100%
construida** y seguir sin entregarse. El estado `Finalizada` significa "la obra terminó"; para
pasar a `Adjudicada` (entregada a la familia) falta tramitar el **acta de finalización**, y ese
trámite se demora por falta de seguimiento.

De las **329 obras en estado Finalizada, 148 (45%) tienen el acta atascada** — más de 6 meses
esperando trámite, con una espera promedio de **~365 días** dentro de ese grupo (~204 días en
promedio si se cuentan todas las finalizadas, atascadas o no).

**Por qué importa distinguir los dos cuellos de botella:** se resuelven distinto. El
constructivo (sección 6.2) necesita materiales o cuadrillas de la gestora; el administrativo se
resuelve **destrabando papeles** — es la intervención más rápida y barata que tiene el
ministerio a mano, y hoy nadie la está midiendo.

### 6.4 Confiabilidad de las ONGs (sobre-reporte y cobertura)

Cruzando las visitas técnicas con el avance reportado por las ONGs surge la **discrepancia**
(`diferencia_ong` = reportado − verificado). El **60,3% de las visitas detecta sobre-reporte**
(la ONG reporta más avance del verificado), con una media de **+3,12 puntos** y picos de **+15**.

| ONG | Sobre-reporte medio (puntos de AFO) | Cobertura de verificación |
|---|---:|---:|
| Coop. de Trabajo San Antonio | +3,24 | 70,2% |
| Asoc. Civil Construir Juntos | +3,07 | 72,3% |
| Mutual Progreso Familiar | sin verificación | 0,0% |

El caso más crítico no es de sobre-reporte sino de **falta total de control**: la **Mutual
Progreso Familiar tiene 0% de sus obras verificadas** (0 de 414) — está en estado Finalizada y
su avance nunca pasó por una visita técnica. Las otras dos ONGs rondan el 70% de cobertura.

### 6.5 Síntesis de indicadores

El programa se resume en siete KPIs operativos, cada uno pensado para habilitar una decisión
concreta (regla de diseño estricta: **un KPI que no habilita una decisión no entra**):

1. **Tasa de finalización** — % de obras completadas sobre el total. Habilita reportar avance
   al gobierno provincial con un número concreto en lugar de un relato.
2. **Obras en riesgo alto** — vencidas (>90 días) y avance <30%. Habilita priorizar visitas
   técnicas y activar el protocolo de seguimiento de la ONG responsable.
3. **Obras en riesgo medio** — vencidas y avance 30–80%. Habilita seguimiento preventivo antes
   de que la obra escale a riesgo alto.
4. **Tiempo promedio de ejecución** (solo obras terminadas, para no sesgar con obras en curso)
   — habilita comparar el desempeño de cada ONG contra el promedio del programa.
5. **Rendimiento por ONG** — avance, riesgo y días promedio por organización. Habilita
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
| **Priorización de visitas** | El técnico elige por cercanía o criterio propio | Cola ordenada por riesgo; **71 obras en riesgo alto sin ninguna visita** quedan visibles |
| **Control de ONGs** | El avance reportado se acepta sin contraste | Se mide el sobre-reporte (**+3,12 pts, 60% de visitas**) y la cobertura (**una ONG al 0%**) |
| **Diagnóstico de obra** | "La obra no avanza" | "Está trabada en *Mampostería hasta dintel*" (184 obras) |
| **Entrega de vivienda terminada** | Nadie lo mide; se descubre cuando reclama la familia | **148 actas atascadas** (45% de las finalizadas) visibles con días de espera |
| **Reporte de gestión** | Narrativo y subjetivo | KPIs concretos: 39,9% finalización · 316 en riesgo alto · 167 días promedio |

### 7.2 Hallazgos principales

1. El **atraso es estructural**, no excepcional: 85% de las terminadas superó el plazo de 90 días.
2. Hay **dos cuellos de botella distintos, y se resuelven distinto**: el constructivo
   (mampostería, 184 obras) necesita materiales o cuadrillas de la gestora; el administrativo
   (148 actas atascadas, 45% de las finalizadas) se resuelve destrabando trámites.
3. Hay **sobre-reporte sistemático** de las ONGs y una organización **sin ningún control**.
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
| **Discrepancia ONG vs. técnico** | Diferencia entre el avance que reporta la ONG y el que verifica el técnico en la visita. Positivo = ONG sobreestimó. |
| **Cobertura de visitas** | Porcentaje de obras asignadas (o de una ONG) que recibieron al menos una visita técnica. |
| **ANOVA** | Analysis of Variance. Test estadístico que evalúa si las medias de más de dos grupos son significativamente distintas. |
| **MinMaxScaler** | Técnica de normalización que lleva todas las variables numéricas al rango [0,1] para que ninguna domine por su magnitud. |
| **VISOC** | Sistema legacy del ministerio que registraba las viviendas sociales antes de VIVSO. Define los 15 códigos de clasificación. |
