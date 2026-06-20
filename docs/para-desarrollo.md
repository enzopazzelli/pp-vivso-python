# Componente de Ciencia de Datos — guía para el equipo de Desarrollo

Documento de entrada para el equipo de **Programación (Java / Spring Boot)**: qué hace
este componente, cómo se integra con el backend y qué necesitamos coordinar. El detalle
vive en [ROADMAP.md](../ROADMAP.md) (planificación e integración) y en
[documentacion-analisis.md](documentacion-analisis.md) (el porqué de cada análisis).

---

## 1. Qué es este componente

Ciencia de Datos (`vivso-python`) es la **capa analítica** del sistema VIVSO: un pipeline
Python que toma los datos operativos del programa de viviendas, calcula indicadores de
gestión (riesgo, cuellos de botella, confiabilidad de ONGs, cobertura técnica) y los expone
en un dashboard. **No es un silo con su propia copia de los datos**: la idea es que el
análisis viva sobre la base común y esté siempre disponible para que ustedes lo consuman.

```
Backend Java / MySQL (vivso3) ──► ETL Python ──► indicadores ──► tablas cd_* + dashboard
```

> Mientras la integración real no esté lista, todo corre sobre un **dataset sintético** de
> 1.500 viviendas que reproduce las reglas del programa. Cambiar a datos reales es cambiar
> una variable de entorno, sin tocar el análisis.

---

## 2. Cómo nos integramos con el backend (sin pisarnos)

Para no chocar con Hibernate (`ddl-auto=update`) ni tocar el schema que ustedes mantienen:

- **Lectura:** Python lee las tablas operativas de `vivso3` (o vía API cuando exista auth).
  El ETL ya soporta ambas vías por variable de entorno (`API → MySQL → CSV sintético`).
- **Escritura:** escribimos **solo en tablas propias con prefijo `cd_`** (en el mismo schema
  o uno aparte, a acordar). Nunca modificamos sus tablas.
  - `cd_vivienda_indicadores` — `nivel_riesgo`, `dias_activa`, `etapa_activa`, `dias_espera_acta`, `score_prioridad_visita`
  - `cd_ong_indicadores` — confiabilidad, sobre-reporte, % en riesgo por ONG
  - `cd_rubro_obra` / `cd_avance_rubro` — desglose del AFO por etapa constructiva
  - `cd_indicadores_globales` — KPIs del programa
- **Consumo:** cualquier front (Streamlit, Next.js) lee esas tablas; **su API puede exponerlas
  con endpoints de solo lectura** sin que toquemos su código.

Detalle completo en [ROADMAP.md](../ROADMAP.md) §3 (arquitectura) y §4 (WS1/WS2).

---

## 3. Qué del backend aprovechamos, y las brechas

Basado en la auditoría del backend (último commit `Feature-1.6`, ver [ROADMAP.md](../ROADMAP.md) §2):

**Ya lo aprovechamos:** API `/vivienda` (fuente principal del ETL), `/organizacion`,
`/familia`, `/solicitud`, y sobre todo **`/documento`** con su workflow de revisión (es donde
se enchufará el OCR).

**Brechas a coordinar:**

| Brecha | Detalle | Qué proponemos |
|---|---|---|
| Clasificaciones | El backend tiene 6 códigos; el sistema VISOC real tiene **15 + criterio** (Inclusión/Exclusión/Otro). `DERRUMBE` en realidad es `2b` | Les pasamos la tabla de 15 (está en [documentacion-analisis.md](documentacion-analisis.md)); mientras tanto el ETL deriva `criterio` |
| Columnas calculadas | No existen `nivel_riesgo`, `dias_activa`, `etapa_activa` | Las escribimos nosotros en las tablas `cd_`; su API las expone con un join |
| Rubros AFO | `avanceObra` es un entero único; no hay desglose por etapa | Viven en nuestras tablas analíticas; evaluamos juntos si pasan al modelo Java |
| `Visita` | Entidad creada, **sin endpoints** | Pedido (ver abajo) o leemos la tabla directo mientras tanto |

---

## 4. Lo que necesitamos de ustedes

| # | Pedido | Para qué | Urgencia |
|---|---|---|---|
| 1 | Usuario MySQL de lectura sobre `vivso3` + escritura sobre tablas `cd_` | Todo el modelo de operación | 🔴 Bloqueante |
| 2 | API de `Visita` (la entidad ya existe) — o aval para leer la tabla directo | Análisis de técnicos con datos reales | 🟡 Alta |
| 3 | Ampliar `ClasificacionVivienda` a 15 códigos + campo `criterio` | Fidelidad con el sistema VISOC | 🟡 Alta |
| 4 | Definición del esquema de roles (enum/valores) | Vistas por rol del dashboard | 🟡 Alta |
| 5 | Punto de enganche del OCR en el flujo de `/documento` | Pipeline de documentos (PP3) | 🟢 Media |
| 6 | Dónde persiste el avance reportado por la ONG | Comparar reporte ONG vs. verificación técnica | 🟢 Media |
| 7 | Avisos: columna `" barrio "` con espacios en `Vivienda`; passwords en texto plano | Calidad / seguridad | 🟢 Informativo |

---

## 5. El modelo de riesgo (lo que exponemos)

Es una **regla transparente, no una caja negra** (a propósito: el ministerio debe poder
explicar el número ante una ONG):

- **Plazo contractual de construcción: 90 días.**
- 🔴 **Riesgo alto:** obra activa vencida (>90 días) con avance < 30%.
- 🟡 **Riesgo medio:** obra activa vencida con avance 30–80%.
- 🟢 **Sin riesgo:** el resto.

El detalle del AFO, los rubros y todos los indicadores está en
[documentacion-analisis.md](documentacion-analisis.md); el análisis completo, en
[informe-eda.md](informe-eda.md).

---

## 6. Estado actual

- Pipeline, indicadores y dashboard **funcionando** sobre datos sintéticos.
- Dashboard desplegado en Streamlit Cloud (lee los CSV versionados en `data/`).
- Los **supuestos del modelo** (plazo, distribuciones, etapas del cuello de botella, umbrales)
  están centralizados y etiquetados `[S#]` en `synthetic/generate.py`, y se validan con el
  área en [datos-a-confirmar.md](datos-a-confirmar.md).
- **Pendiente de coordinación con ustedes:** la integración real (pedidos de la sección 4).

---

## Dónde está cada cosa

| Necesito… | Ir a |
|---|---|
| Cómo correr el proyecto, estructura, conceptos de dominio | [README.md](../README.md) |
| Plan, auditoría del backend, arquitectura `cd_`, pedidos | [ROADMAP.md](../ROADMAP.md) |
| Por qué de cada análisis, AFO, clasificaciones, glosario | [documentacion-analisis.md](documentacion-analisis.md) |
| Informe EDA (hallazgos con figuras) | [informe-eda.md](informe-eda.md) |
