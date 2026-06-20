# VIVSO — Componente de Ciencia de Datos e IA

**Práctica Profesionalizante PP2 · ITSE · Tecnicatura en Ciencia de Datos e IA**
**Equipo:** Pablo Castillo · Sara Lombardi · Valeria Martinetti · Santiago Gallardo · Enzo Pazzelli
**Entidad:** Subsecretaría de Promoción Humana — Ministerio de Desarrollo Social, Santiago del Estero

> Este README es el documento de traspaso del proyecto: explica qué hay, cómo se corre y qué sigue.
> La planificación detallada está en [ROADMAP.md](ROADMAP.md). El **Informe EDA** (entregable del Hito 3) está en [docs/informe-eda.md](docs/informe-eda.md); la explicación del *por qué* de cada análisis y decisión, en [docs/documentacion-analisis.md](docs/documentacion-analisis.md).

---

## 1. Qué es este proyecto

El sistema **VIVSO** reemplaza tres sistemas legacy desconectados (App GPS, VISOC y GEDO) del programa de viviendas sociales. Lo construyen dos equipos:

| Equipo | Stack | Repo |
|---|---|---|
| **Desarrollo** | Java Spring Boot + MySQL (schema `vivso3`) | `vivso/` |
| **Ciencia de Datos** (este repo) | Python: ETL, análisis, indicadores, dashboard | `vivso-python/` |

La misión de este componente: **modernizar la gestión** (de papel y planillas a datos estructurados) y **mejorar la toma de decisiones del área** — que el ministerio sepa qué obra visitar primero, qué ONG auditar, qué acta destrabar y dónde está el cuello de botella, con números defendibles.

```
API Java / MySQL ─┐
Datos sintéticos ─┼─► ETL Python ─► SQLite local ─► Notebooks (colab/) ─► Dashboard Streamlit
                  ┘                                  indicadores            inicio + 6 vistas
```

Mientras el backend Java no tenga datos cargados, el sistema genera un **dataset sintético de 1.500 viviendas** con distribución geográfica y reglas de negocio realistas. Cuando la API esté disponible, se cambia una variable de entorno y todo corre igual con datos reales.

---

## 2. Conceptos de dominio (leer antes de tocar nada)

Sin esto, el código no se entiende. Son las reglas del programa real:

- **AFO (Avance Físico de Obra):** % de avance 0–100, calculado como suma ponderada de **15 rubros de construcción estrictamente secuenciales** (el rubro N solo arranca cuando el N-1 terminó). La secuencia y pesos salen del sistema legacy VISOC ([docs/afo.jpeg](docs/afo.jpeg)).
- **Clasificaciones:** el sistema real tiene **15 códigos** (no 6 como el backend actual) agrupados por **criterio**: Inclusión (apta), Exclusión (rechazada), Otro (caso especial). Fuente: [docs/tipos.jpeg](docs/tipos.jpeg).
- **Plazo contractual de construcción: 90 días** (confirmado por el área). Es la constante `PLAZO_CONSTRUCCION_DIAS` en `synthetic/generate.py` — única fuente de verdad. Hallazgo clave: ~85% de las obras terminadas lo supera.
- **Modelo de riesgo (regla transparente, no caja negra):** obra activa que superó los 90 días → 🔴 alto si avance < 30% · 🟡 medio si 30–80% · 🟢 bajo el resto. Es una regla y no ML a propósito: el ministerio debe poder explicar el número ante una ONG.
- **Los dos cuellos de botella:** el **constructivo** (la obra se traba en una etapa, típicamente mampostería) y el **administrativo** (obra 100% construida en estado `Finalizada` esperando el **acta de finalización** para pasar a `Adjudicada` — se demora por falta de seguimiento).
- **Regla de visitas:** máximo 2 visitas técnicas por obra. ~70% de las obras activas no tiene ninguna → el avance reportado por las ONGs está mayormente sin verificar. De ahí salen el score de priorización de visitas y la alerta de sobre-reporte.

---

## 3. Estructura del repo

```
vivso-python/
├── etl/extract.py         # Carga desde API Java o CSV local (fallback automático)
├── synthetic/generate.py  # Genera el dataset sintético completo y puebla la DB
│                          #   ← acá viven PLAZO_CONSTRUCCION_DIAS, las 15 clasificaciones,
│                          #     los rubros AFO y el modelo de riesgo (recalcular_derivados)
├── db/
│   ├── models.py          # Schema SQLAlchemy (9 tablas, incl. rubro_obra y avance_rubro)
│   └── setup.py           # Crea tablas + siembra el catálogo de 15 rubros
├── colab/                 # LOS NOTEBOOKS CANÓNICOS (5) — pensados para Google Colab + Drive
│   ├── 01_exploracion     # EDA: estados, prioridad (2b/3a), verificación técnica, riesgo
│   ├── 02_normalizacion   # Limpieza justificada → viviendas_procesadas.csv
│   ├── 03_correlaciones   # Criterio×tipo, ANOVA, cohortes por año, riesgo por clasificación
│   ├── 04_indicadores     # KPIs + confiabilidad ONG + actas + etapa activa + cronograma
│   └── 05_tecnicos        # Cobertura, discrepancias, score de visitas, alerta sobre-reporte
├── dashboard/             # Streamlit — inicio (resumen ejecutivo) + 6 páginas
│                          #   viviendas, ONGs, minería, evolución, técnicos, mis obras
│                          #   components/data_loader.py centraliza la carga de CSVs
├── data/                  # CSVs: el dataset base se versiona (para el deploy en Streamlit
│                          #   Cloud); los derivados de notebooks quedan gitignored. Regenerable.
├── docs/
│   ├── informe-eda.md               # INFORME EDA (entregable Hito 3) — documento formal único
│   ├── datos-a-confirmar.md         # checklist de supuestos para validar con el área (reunión)
│   ├── generar_figuras.py           # regenera las figuras del informe desde el dataset
│   ├── figuras/                     # PNGs del informe (regenerables)
│   ├── documentacion-analisis.md    # POR QUÉ de cada análisis — para entender y explicar
│   ├── para-desarrollo.md           # Guía de integración para el equipo de Programación (Java)
│   └── afo.jpeg / tipos.jpeg        # Capturas del sistema legacy (evidencia de dominio)
├── ROADMAP.md             # Ruta de trabajo + bitácora del proceso (documento vivo)
└── README.md              # Este archivo
```

**Convenciones:** paleta estándar en todos los gráficos (índigo `#4f46e5` base + esmeralda/ámbar/rosa como semáforo); celdas markdown para interpretaciones; **código sencillo y claro (no austero) — toda función o paso no obvio lleva un comentario con su propósito o porqué**.

---

## 4. Cómo correr todo

### Setup (una vez)

```powershell
cd vivso-python
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # completar VIVSO_API_URL solo si el backend está corriendo
```

### Generar datos y base local

```powershell
python -m db.setup              # crea tablas + catálogo de rubros
python -m synthetic.generate    # 1.500 viviendas + ONGs + técnicos + visitas + rubros AFO
```

### Notebooks (en Colab)

1. Subir los CSVs de `data/` a una carpeta `PP2` en Google Drive.
2. Subir los `.ipynb` de `colab/` y abrirlos con Google Colaboratory.
3. Ejecutar **en orden** (01 → 05): el 02 genera `viviendas_procesadas.csv` que usan los siguientes.

### Dashboard

```powershell
streamlit run dashboard/app.py   # abre en http://localhost:8501
```

Funciona aun sin correr los notebooks: si falta `viviendas_procesadas.csv`, cae automáticamente al dataset sintético.

---

## 5. Estado actual (qué está hecho)

Cerrado en Hito 2 y posteriores:

- ✅ ETL con fallback API → CSV; generador sintético con reglas de negocio reales (15 clasificaciones + criterio, rubros AFO secuenciales, ciclo de actas, plazo 90)
- ✅ 5 notebooks de análisis con hallazgos accionables (70% sin verificación, cuellos de botella, cohortes)
- ✅ Indicadores de gestión: **índice de confiabilidad de ONG**, **score de priorización de visitas**, **alerta de sobre-reporte**, **actas atascadas**, **etapa activa / cuello de botella constructivo**
- ✅ Dashboard Streamlit con **inicio de resumen ejecutivo** (KPIs globales, alerta de obras en riesgo sin visita, mapa provincial, navegación) + 6 páginas con mapa de riesgo
- ✅ Página **Evolución**: series de tiempo del programa (inicios vs. finalizaciones por mes, backlog acumulado, tasa de finalización por trimestre)
- ✅ Modelo de riesgo recalibrado al plazo real de 90 días (2026-06-10)
- ✅ Documentación completa del análisis y guion de presentación

## 6. Qué se planea hacer (resumen — el detalle está en ROADMAP.md)

La prioridad inmediata es el **cierre de PP2 (Hito 3)**: entregable oficial = *"Informe EDA + prototipo funcionando"*. El prototipo ya funciona y el **Informe EDA está redactado** ([docs/informe-eda.md](docs/informe-eda.md), con figuras generadas desde el dataset). Queda **validar el alcance con el profesor** y preparar la presentación.

Después (preparación de PP3, en coordinación con el equipo de Desarrollo):

1. **WS1 — Integración real:** ETL contra MySQL `vivso3` (la base del backend Java).
2. **WS2 — Capa analítica en la BDD:** materializar los indicadores en tablas `cd_*` para que cualquier front los consuma sin notebooks de por medio.
3. **WS3 — Dashboard por roles:** vistas según el esquema de roles/auth que está construyendo Programación (gancho de auth simulada ya diseñado).
4. **WS4 — Capa ONG + OCR:** las organizaciones cargan avances y documentación; un pipeline OCR (OpenCV + Tesseract) prellena los formularios y un humano valida — se engancha al workflow de `/documento` que el backend ya tiene.

Los **pedidos pendientes al equipo de Desarrollo** (acceso a la base, API de Visita, ampliar clasificaciones a 15, esquema de roles) están en la sección 5 del ROADMAP.

---

## 7. Para quien continúe este proyecto

Ruta de onboarding sugerida (en este orden):

1. Leer la sección 2 de este README (conceptos de dominio) — 10 minutos.
2. Leer [docs/documentacion-analisis.md](docs/documentacion-analisis.md) — explica cada análisis, por qué se eligió y qué decisión habilita. Escrito para que lo entienda un estudiante, un profesor o alguien del área.
3. Correr el setup (sección 4) y abrir el dashboard — ver el producto antes que el código.
4. Abrir los colabs en orden y leer las celdas markdown (las interpretaciones están ahí).
5. Revisar [ROADMAP.md](ROADMAP.md): la sección 2 tiene el estado auditado del backend Java, la 4 los workstreams pendientes y la 7 la **bitácora** con la historia y las decisiones del proceso.

Reglas para mantener la coherencia del proyecto:

- Los **supuestos del programa** (plazo, distribuciones, etapas del cuello de botella, umbrales de riesgo, etc.) están centralizados y etiquetados `[S#]` en el bloque *"SUPUESTOS DEL PROGRAMA"* al inicio de `synthetic/generate.py`. Para ajustarlos a la realidad: se edita el valor ahí y se regenera — nada de números escondidos en funciones. Cada `[S#]` se corresponde con una fila de [docs/datos-a-confirmar.md](docs/datos-a-confirmar.md), la checklist que se completa con el área.
- Las columnas derivadas (`dias_activa`, `nivel_riesgo`) se calculan **solo** en `recalcular_derivados()` a partir de las fechas — no asignarlas a mano en otro lado.
- Todo indicador nuevo debe responder una pregunta de gestión concreta ("¿a quién audito?", "¿a dónde mando al técnico?") — si no habilita una decisión, no entra.
- Registrar las decisiones importantes en la bitácora del ROADMAP: este proyecto documenta su proceso de principio a fin.
