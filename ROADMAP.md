# Ruta de trabajo — Ciencia de Datos e IA · VIVSO
### Integración con el área de Desarrollo · Hito 3 · PP2 ITSE

**Equipo:** Pablo Castillo · Sara Lombardi · Valeria Martinetti · Santiago Gallardo · Enzo Pazzelli
**Última actualización:** 2026-06-10
**Prioridad rectora:** cumplir el **Hito 3** de la Práctica Profesionalizante.

> Este documento es la ruta de trabajo **y** el registro del proceso de principio a fin.
> Se actualiza a medida que se avanza: cada tarea cambia de estado y cada decisión queda asentada en la bitácora del final.
> Convención: `[ ]` pendiente · `[~]` en progreso · `[x]` hecho · `[!]` bloqueado (esperando a Desarrollo u otro externo).

---

## 1. Misión del equipo

El componente de Ciencia de Datos e IA existe para dos cosas, y todo lo que se planifique debe responder a una de ellas:

1. **Modernizar** la gestión del programa de viviendas sociales: reemplazar planillas, formularios en papel y seguimiento manual por datos estructurados y procesos digitales.
2. **Mejorar la toma de decisiones del área**: que el ministerio sepa qué obra visitar primero, qué ONG auditar, qué acta destrabar y dónde está el cuello de botella — con números defendibles, no con intuición.

**Modelo de operación acordado:** el análisis se hace **sobre la base de datos** (MySQL `vivso3`, la misma que usa el backend Java). Los resultados quedan **siempre disponibles** para que Desarrollo los consuma cuando los necesite — vía Streamlit, vía tablas/vistas que la API Java pueda exponer, o el front que se requiera. Ciencia de Datos no es un silo con su propia copia de los datos: es una capa analítica sobre la base común.

---

## 2. Estado real del backend Java (auditado 2026-06-10)

Para que el plan sea aplicable, está anclado a lo que **existe hoy** en `vivso/` (último commit: `Feature-1.6`, 2026-05-06). Resumen de lo relevante para nosotros:

### Lo que el backend YA tiene (y aprovechamos)

| Recurso | Estado | Relevancia para CD |
|---|---|---|
| API CRUD `/vivienda` (con filtros por estado, localidad, año) | ✅ Operativa | Fuente principal del ETL |
| API `/organizacion`, `/familia`, `/familiar`, `/solicitud` | ✅ Operativas | Fuentes secundarias |
| **`/documento`** — subida multipart, almacenamiento con UUID, workflow PENDIENTE→EN_REVISION→APROBADO/RECHAZADO, revisor auditado | ✅ Operativa | **Base de la capa ONG**: acá se enchufa el OCR |
| Enum `TipoDocumento` con los 12 requisitos (DNI, certificados, actas, alta AFIP, etc.) | ✅ Definido | El pipeline OCR debe clasificar contra esta lista |
| Entidad `Visita` (técnico, avance registrado, GPS, prioridad social) | ⚠️ **Entidad creada, sin API** | Nuestro análisis de técnicos la necesita |
| `Usuario` con campo `rol` | ⚠️ Rol como texto libre, sin enum | Las vistas por rol dependen de esto |
| `SecurityConfig` | ⚠️ Existe pero `permitAll()`, passwords en texto plano | Auth/roles **en desarrollo por Programación** |
| MySQL schema `vivso3`, `ddl-auto=update`, credenciales por variables de entorno | ✅ | Nuestro punto de conexión analítica |

### Brechas del modelo de datos (a coordinar con Desarrollo)

| Brecha | Detalle | Propuesta CD |
|---|---|---|
| Clasificaciones incompletas | Backend tiene 6 (`1a, 2a, 2b, 5f, DERRUMBE, OTRA`); el sistema VISOC real tiene **15 + criterio** (Inclusión/Exclusión/Otro). Además `DERRUMBE` en el legacy es `2b`, no un código aparte | Pasarles la tabla completa de 15 códigos (está en `docs/documentacion-analisis.md`); mientras tanto el ETL deriva `criterio` |
| Sin rubros AFO | `avanceObra` es un entero único; no existe `avance_rubro` ni catálogo de rubros | Los rubros viven en tablas analíticas nuestras; evaluar con ellos si pasan al modelo Java |
| Sin columnas calculadas | No hay `nivel_riesgo`, `dias_activa`, `etapa_activa`, `dias_espera_acta` | Las escribimos nosotros en tablas analíticas (ver WS2) — la API puede exponerlas con un join |
| `Visita` sin endpoints | Entidad lista, falta Controller/Service | **Pedido a Desarrollo** (o leemos directo de la tabla mientras tanto) |
| Plazo de obra | Confirmado por el área: **90 días** la etapa de construcción | Ya incorporado a todo nuestro pipeline (`PLAZO_CONSTRUCCION_DIAS = 90`) |

---

## 3. Decisión de arquitectura: cómo convivimos con la base

Para no pisarnos con Hibernate (`ddl-auto=update`) ni tocar el schema que mantiene Desarrollo:

- **Lectura:** Python lee las tablas operativas de `vivso3` directamente (o vía API cuando exista auth). El ETL ya soporta ambas vías con una variable de entorno.
- **Escritura:** Ciencia de Datos escribe **solo en tablas analíticas propias**, con prefijo `cd_` dentro del mismo schema (o schema aparte si Desarrollo lo prefiere — a acordar):
  - `cd_vivienda_indicadores` — por vivienda: `nivel_riesgo`, `dias_activa`, `etapa_activa`, `avance_en_etapa`, `dias_espera_acta`, `score_prioridad_visita`
  - `cd_ong_indicadores` — por ONG: índice de confiabilidad, sobreestimación, % en riesgo
  - `cd_rubro_obra` / `cd_avance_rubro` — catálogo y desglose AFO por etapa constructiva
  - `cd_indicadores_globales` — KPIs del programa (tasa de finalización, actas atascadas, cuello de botella)
- **Consumo:** cualquier front (Streamlit, Next.js, lo que pida Desarrollo) lee esas tablas; la API Java puede exponerlas con endpoints de solo lectura sin que nosotros toquemos su código.

Esto cumple el requisito: **el análisis vive en la BDD y está disponible siempre**, sin depender de que un notebook esté corriendo.

---

## 4. Workstreams (la ruta propiamente dicha)

Orden de ejecución: WS0 → WS1 → WS2 → WS3 en paralelo con WS4 → WS5. El WS5 (Hito 3) es la prioridad que ordena a los demás: si algo no contribuye al hito, se posterga.

---

### WS0 — Preparación y acuerdos (sin código, 1 reunión + documentación)

Objetivo: que nada de lo que sigue se construya sobre supuestos.

- [ ] **Reunión de contrato técnico con Desarrollo.** Llevar la tabla de brechas (sección 2) y salir con acuerdos escritos sobre: prefijo/ubicación de tablas `cd_`, acceso de lectura a `vivso3`, las 15 clasificaciones, y quién expone la API de `Visita`.
- [ ] **Acceso a la base:** usuario MySQL de solo-lectura sobre tablas operativas + permisos de escritura sobre las `cd_`. Variables `MYSQL*` compartidas para entorno de desarrollo.
- [ ] **Definir el mapa rol → vista** con Programación (su esquema de roles está en construcción; ver WS3). Proponer: `ADMIN` (todo), `TECNICO` (equipo técnico + mis obras), `ONG` (su portal de avances/documentación), `MINISTERIO/CONSULTA` (indicadores y mapas, solo lectura).
- [ ] **Congelar el alcance del Hito 3** (qué entra y qué no) y validarlo con el profesor. Registrarlo en la bitácora.
- [x] Resolver deuda mínima propia: `notebooks/` locales **deprecados y eliminados** (los `colab/` son los canónicos), `mining/` vacío eliminado, spec vieja eliminada, README reescrito como documento de traspaso (2026-06-11).

**Criterio de salida:** acta de acuerdos con Desarrollo asentada en la bitácora + acceso a la base funcionando.

---

### WS1 — Integración de datos real (ETL contra `vivso3`)

Objetivo: dejar de depender del dataset sintético como fuente; que el pipeline corra contra la base real y degrade a sintético solo si la base no está disponible.

- [ ] Adaptar `etl/extract.py` para leer MySQL directo (SQLAlchemy ya está en requirements) además de la vía API. Selección por variable de entorno: `API → MySQL → CSV sintético`.
- [ ] Mapear el modelo real: enums de Java (`INICIADA`/`Iniciada`...), `numExp`/`num_exp`, fechas `dd-MM-yyyy`, la columna `barrio` con espacio en el nombre (bug conocido del backend — avisarles).
- [ ] Derivar `criterio` desde `clasificacion` en el ETL mientras el backend tenga 6 códigos (los 9 restantes no existirán en datos reales hasta que amplíen el enum).
- [ ] Leer `visita` directo de la tabla (hasta que exista su API) para alimentar el análisis de técnicos.
- [ ] Probar el pipeline completo contra una base `vivso3` poblada con datos de prueba de Desarrollo. Documentar diferencias encontradas entre datos reales y sintéticos.

**Criterio de salida:** los 5 notebooks y el dashboard corren contra MySQL real sin tocar una línea de análisis. Solo cambia el origen.

---

### WS2 — Capa analítica en la base (el corazón del modelo de operación)

Objetivo: que los indicadores dejen de vivir en notebooks y queden **materializados en la BDD**, disponibles para cualquier consumidor en cualquier momento.

- [ ] Crear las tablas `cd_*` (schema acordado en WS0) con SQLAlchemy: `cd_vivienda_indicadores`, `cd_ong_indicadores`, `cd_rubro_obra`, `cd_avance_rubro`, `cd_indicadores_globales`.
- [ ] Empaquetar el cálculo de indicadores como **job ejecutable** (`python -m analytics.refresh`): lee operativas → calcula (riesgo con plazo 90, etapa activa, actas, confiabilidad, score de visitas) → escribe `cd_*`. Idempotente y re-ejecutable.
- [ ] Definir frecuencia de refresco (propuesta inicial: manual/diario; automatizar después si el área lo pide).
- [ ] Documentar el **diccionario de datos** de las tablas `cd_` (qué significa cada columna, cómo se calcula, con qué regla) para que Desarrollo pueda exponerlas sin consultarnos.
- [ ] Entregar a Desarrollo la especificación de endpoints de solo lectura sugeridos (`GET /indicadores/vivienda/{numExp}`, `GET /indicadores/ong/{cuit}`, `GET /indicadores/globales`) — la implementación es de ellos, el contrato es nuestro.

**Criterio de salida:** un `SELECT` a las tablas `cd_` devuelve los indicadores actualizados sin que ningún notebook esté abierto. El portal Next.js podría pintar el mapa de riesgo solo con eso.

---

### WS3 — Capa de visualización adaptada a roles

Objetivo: que el dashboard deje de ser una demo y pase a ser la herramienta que cada perfil del área usa, alineada al sistema de roles que Programación está construyendo.

- [ ] Reorganizar el dashboard Streamlit según el mapa rol → vista (de WS0):
  - **Ministerio/Admin:** indicadores globales, confiabilidad de ONGs, actas atascadas, mapa de riesgo.
  - **Jefe de área técnica:** cobertura de visitas, discrepancias, alertas de sobre-reporte.
  - **Técnico:** mis obras, cola de prioridad, score de visitas.
  - **ONG:** solo su propia información (sus obras, sus documentos, su estado).
- [ ] **Llevar la confiabilidad a la página de ONGs (`02_ongs.py`)** — mejora identificada el 2026-06-13. Hoy la página mide solo volumen (obras, avance, riesgo por organización); falta la tesis central del proyecto, que responde la pregunta de gestión *"¿a qué ONG audito?"*. Plan concreto, con datos ya disponibles (`visitas.csv` → join por `cuit_org`):
  - **Sección de sobre-reporte por ONG:** promedio y máximo de `diferencia_ong` (avance reportado por la ONG menos el verificado por el técnico). En el sintético actual: prom. ≈ +3 puntos, **picos de +15**.
  - **KPI de cobertura de verificación por ONG:** % de obras de la ONG con al menos una visita. Hallazgo a destacar: la **MUTUAL PROGRESO (FINALIZADA) tiene 0% verificada** (0/414) vs. ~70% de las otras dos.
  - **Scorecards por ONG** en lugar de barras de 3 (con solo 3 organizaciones, las barras lucen pobres en la demo): tarjeta con avance · riesgo · confiabilidad · cobertura.
  - Conecta directo con el guion **As is → To be** pedido en la devolución del Hito 2.
- [ ] Implementar el **gancho de autenticación**: mientras Programación termina auth, un selector de rol simulado (como hoy en "Mis obras") pero encapsulado en un módulo único (`dashboard/components/auth.py`) — cuando exista JWT/sesión real, se cambia ese módulo y nada más.
- [ ] Filtrado por identidad: una ONG logueada ve solo sus viviendas (filtro por `cuit`), un técnico solo sus asignaciones. La lógica de filtrado se escribe ya, aunque la identidad venga del selector simulado.
- [ ] Consumir las tablas `cd_` (no CSVs) como fuente del dashboard una vez que WS2 esté operativo.
- [ ] Validar las vistas con el referente del área (qué le sirve, qué sobra, qué falta) y registrar el feedback.

**Criterio de salida:** demo navegable por rol; cambiar de "selector simulado" a "auth real" es un cambio de un solo módulo.

---

### WS4 — Capa ONG: avances y documentación (con pipeline OCR)

Objetivo: soportar el circuito que está planeando el equipo — que las organizaciones gestoras carguen avances de obra y presenten la documentación/requisitos para gestionar nuevas viviendas — reduciendo la carga manual con OCR.

El backend **ya tiene la mitad del circuito**: `/documento` (subida + workflow de revisión + tipos de requisito) y `/solicitud` (GDE, estados Pendiente/Aprobada/Rechazada). Nuestro aporte es la **inteligencia** sobre ese circuito:

**4a — Pipeline OCR (prototipo primero, integración después):**
- [ ] Conseguir 3–5 **formularios reales** del área (planilla de relevamiento, nota de solicitud, acta) — sin esto no se puede calibrar nada. *Pedido al referente.*
- [ ] Prototipo en notebook: OpenCV (enderezado, binarización) + Tesseract (extracción) sobre esos formularios. Medir tasa de acierto campo por campo.
- [ ] Definir el contrato de salida del OCR: JSON con campos extraídos + nivel de confianza por campo (`{"dni": {"valor": "33222111", "confianza": 0.93}}`).
- [ ] Regla de oro del diseño: el OCR **prellena, nunca decide**. Todo pasa por validación humana (el workflow de revisión que ya existe en `/documento`).

**4b — Integración al circuito de documentos:**
- [ ] Acordar con Desarrollo el punto de enganche: cuando se sube un `Documento`, ¿quién invoca el OCR? Propuesta: servicio Python pequeño (FastAPI o script batch sobre `uploads/documentos/`) que procesa pendientes y devuelve el JSON de prellenado.
- [ ] Clasificación automática del tipo de documento contra el enum `TipoDocumento` (los 12 requisitos) como ayuda al revisor.
- [ ] Tablero de revisión documental en Streamlit (vista ADMIN/Ministerio): cola de documentos PENDIENTE/EN_REVISION, con campos extraídos y nivel de confianza a la vista.

**4c — Avances de obra de la ONG:**
- [ ] Cruzar lo que la ONG reporta (vía el portal que construye Desarrollo) contra nuestros indicadores: si una ONG con historial de sobreestimación carga un avance alto, marcarlo para verificación prioritaria (la **alerta de sobre-reporte** ya existe; acá se conecta al circuito real).
- [ ] Definir con Desarrollo dónde persiste el avance reportado por ONG (¿`Visita`? ¿tabla nueva `avance_reportado`?) para poder calcular la discrepancia ONG vs. técnico con datos reales.

**Criterio de salida 4a:** prototipo OCR con tasa de acierto medida y documentada sobre formularios reales.
**Criterio de salida 4b/4c:** flujo demo de punta a punta: ONG sube documento → OCR prellena → revisor ve y aprueba → indicadores se actualizan.

---

### WS5 — Hito 3: cierre de PP2 (LA PRIORIDAD)

Según el mapa oficial de la práctica (`Mapa_Practicas_Profesionalizantes.pdf`): PP2 cubre las etapas **3-Preprocesamiento, 4-EDA y 5-Modelo**, y su entregable de cierre es **"Informe EDA + prototipo funcionando"** en entorno local. Despliegue, evaluación, monitoreo y presentación profesional a la entidad son **PP3** (próximo cuatrimestre).

Inventario contra el requisito: Preproc ✅ · EDA ✅ · Modelo ⚠️ defendible · Prototipo ✅ casi listo · **Informe EDA ❌ falta como documento único** — la brecha real del hito es documental, no técnica.

- [x] **Informe EDA** (la tarea principal): consolidado en `docs/informe-eda.md` — dataset, preprocesamiento justificado, EDA univariado/bivariado con figuras, modelo de riesgo, indicadores y conclusiones As is → To be. Figuras generadas desde el dataset con `docs/generar_figuras.py` (9 PNG en `docs/figuras/`). Encuadre en los tipos de solución de la cátedra (Panel + Pipeline + CV). Reporta también los **resultados negativos** con honestidad (criterio y tipo no explican avance/duración; ANOVA p=0,21). (2026-06-13)
- [~] **Prototipo pulido para demo**: el dashboard + ETL + BDD local ya funcionan; el inicio se rehízo como resumen ejecutivo y se sumó la página de Evolución (2026-06-13). Falta ensayar el flujo completo de la demo.
- [ ] **Etapa 5 "Modelo" defendida**: presentar el modelo de riesgo (regla calibrada al plazo de 90 días) y los scores compuestos (confiabilidad ONG, priorización de visitas) como modelos de decisión, con la defensa documentada de por qué reglas transparentes y no caja negra. Si los formularios reales llegan a tiempo, sumar el prototipo OCR (WS4a) como componente de IA/CV.
- [ ] Presentación Hito 3 + guion **siguiendo `docs/guia-presentaciones.md`** (devolución del Hito 2): As is → To be con números de ganancia, tablas de ejemplo, código casi cero; guion como mapa de defensa con protocolo de preparación — nadie memoriza, nadie lee.
- [ ] Validar este alcance con el profesor (cierra el punto de WS0).

**Reordenamiento de prioridades:** WS1/WS2 (integración MySQL real, tablas `cd_`) apuntan a "despliegue en pruebas" = **PP3**. Siguen siendo la dirección correcta y se avanzan como preparación del próximo cuatrimestre, pero **no bloquean el Hito 3**: para cerrar PP2 alcanza el prototipo local, que es lo que existe.

**Criterio de salida:** Informe EDA entregado + prototipo demostrado + Hito 3 aprobado. La bitácora cuenta la historia completa del proceso.

---

## 5. Pedidos concretos al equipo de Desarrollo

Tabla de coordinación — esto es lo que necesitamos de ellos, para llevar a la reunión de WS0:

| # | Pedido | Para qué | Urgencia |
|---|---|---|---|
| 1 | Usuario MySQL de lectura sobre `vivso3` + escritura sobre tablas `cd_` | WS1/WS2 — todo el modelo de operación | 🔴 Bloqueante |
| 2 | API de `Visita` (entidad ya existe, faltan endpoints) — o aval para leer la tabla directo | Análisis de técnicos con datos reales | 🟡 Alta |
| 3 | Ampliar `ClasificacionVivienda` a los 15 códigos + campo `criterio` (les pasamos la tabla) | Fidelidad con el sistema VISOC real | 🟡 Alta |
| 4 | Definición del esquema de roles (enum/valores) apenas lo cierren | WS3 — mapa rol → vista | 🟡 Alta |
| 5 | Punto de enganche del OCR en el flujo de `/documento` | WS4b | 🟢 Media |
| 6 | Dónde persiste el avance reportado por la ONG | WS4c — discrepancia con datos reales | 🟢 Media |
| 7 | Avisos: columna `" barrio "` con espacios en `Vivienda`; passwords en texto plano | Calidad / seguridad | 🟢 Informativo |

---

## 6. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Auth de Programación se demora | WS3 no puede usar identidad real | El gancho de auth simulada está diseñado para eso: el resto avanza igual |
| No conseguimos formularios reales para el OCR | WS4a no se puede calibrar | Pedirlos YA en WS0; plan B: generar formularios de práctica con el formato del área |
| La base real tiene pocos datos cargados | Los indicadores reales quedan flacos para la demo | El generador sintético puede poblar `vivso3` con datos de prueba (mismo schema) — acordarlo con Desarrollo |
| Cambios de schema del lado Java rompen el ETL | Pipeline caído | Las tablas `cd_` nos aíslan en escritura; en lectura, tests de contrato simples sobre las columnas que consumimos |
| Alcance del Hito 3 más chico/distinto de lo asumido | Esfuerzo mal asignado | Congelar alcance con el profesor en WS0, antes de codificar |

---

## 7. Bitácora del proceso

Registro cronológico de hechos y decisiones. Se agrega una fila por evento relevante — esto es lo que documenta el proceso de principio a fin.

| Fecha | Evento / Decisión | Detalle |
|---|---|---|
| 2026-06-04 | Cierre del análisis Hito 2 | 15 clasificaciones VISOC + criterio; rubros AFO secuenciales; modelado del ciclo de actas; dataset 1.500 |
| 2026-06-09 | Indicadores de gestión definidos | Índice de confiabilidad ONG, dos cuellos de botella (constructivo/actas), score de priorización de visitas, alerta de sobre-reporte, cohortes |
| 2026-06-10 | **Corrección de regla de negocio: plazo = 90 días** (era 365) | Fuente confiable del área. Modelo de riesgo recalibrado (Opción A: vencida + <30% = alto, 30–80% = medio). Centralizado en `PLAZO_CONSTRUCCION_DIAS`. Hallazgo: ~85% de las obras terminadas supera el plazo |
| 2026-06-10 | Auditoría del backend Java | Estado real relevado (sección 2): `/documento` con workflow completo, `Visita` sin API, auth en `permitAll()`, rol texto libre, 6 clasificaciones |
| 2026-06-10 | Ruta de trabajo reorganizada hacia integración con Desarrollo | Este documento. Arquitectura acordada internamente: tablas `cd_*` como capa analítica en la BDD |
| 2026-06-11 | **Hito 3 clarificado con el mapa oficial de la práctica** | PP2 = etapas 3-4-5, entregable "Informe EDA + prototipo funcionando" en local. Brecha real: el Informe EDA como documento único. La integración MySQL (WS1/WS2) se reclasifica como preparación de PP3 — no bloquea el hito. WS5 reescrito |
| 2026-06-11 | **Limpieza del repo para traspaso** | Eliminados: `notebooks/` locales (desactualizados, superados por `colab/`), `mining/` vacío, `docs/especificacion.md` (superada), caches. Capturas del legacy movidas a `docs/`. README reescrito como documento de traspaso con onboarding para el equipo |
| 2026-06-11 | **Devolución del profesor sobre la presentación Hito 2** | Demasiado técnica: faltaron tablas de ejemplo, KPIs accionables y contrastes **As is → To be** con número de ganancia de eficiencia. El guion se usó mal (memorizado/leído en vez de entendido). Se creó `docs/guia-presentaciones.md` con reglas obligatorias para futuras presentaciones, guiones y código (comentado con propósito/porqué). Convención de "código minimalista" reemplazada por "sencillo, claro y comentado" |
| 2026-06-11 | **Corrección de dominio: el ministerio no manda cuadrillas** | La construcción es responsabilidad de la **organización gestora** (que suele tercerizar y materializa el beneficio). Ante un cuello constructivo, la palanca del ministerio es reclamar/seguir a la gestora — no logística propia. El acta sí se destraba desde el ministerio. Corregidos: `guia-presentaciones.md`, `documentacion-analisis.md` (KPI 7), colab 04 (markdown actas). Docs Hito 2 quedan como históricos |
| 2026-06-11 | **Repo publicado para traspaso al equipo** | `github.com/enzopazzelli/vivso-python` — commit inicial `4d96e46` (31 archivos). Datos, base y `.env` excluidos: quien clona regenera todo con `db.setup` + `synthetic.generate` según el README |
| 2026-06-13 | **Rediseño del dashboard para impacto de demo** | Inicio rehecho como **resumen ejecutivo** (`app.py`): 6 KPIs globales, banner de alerta (316 en riesgo alto / 71 sin visita), donut de estado, inicios por mes, mapa provincial y tarjetas de navegación a las 6 secciones (antes linkeaba 3 de 5). Nueva página **Evolución** (`06_evolucion.py`): inicios vs. finalizaciones mensuales, backlog acumulado, tasa de finalización trimestral. `cargar_visitas()` agregado a `data_loader`. Quitada la mención de "clustering" (columna `cluster` vacía, sin respaldo visual). Verificado con `streamlit.testing` (las 7 páginas renderizan sin excepción) |
| 2026-06-13 | **Informe EDA redactado (entregable principal del Hito 3)** | `docs/informe-eda.md`: documento formal único (introducción, dataset, preprocesamiento, EDA univariado/bivariado, modelo de riesgo, indicadores, conclusiones As is → To be, reproducibilidad). 9 figuras generadas desde el dataset con `docs/generar_figuras.py` (sin imágenes editadas a mano). Cifras del dataset actualizadas en la documentación (1.000 → 1.500). **Hallazgos honestos:** se reportan resultados negativos — criterio y tipo de vivienda no explican avance ni duración (ANOVA F=1,57, p=0,21); el hallazgo fuerte es el atraso estructural (85% supera el plazo de 90 días), el cuello de botella en mampostería (184 obras) y el sobre-reporte de ONGs (+3,15 pts, 61% de visitas; una ONG con 0% de verificación). Falta validar alcance con el profesor y armar la presentación |
| 2026-06-13 | **Preparación para validar el modelo con el área** | Centralizados todos los supuestos del generador en un bloque etiquetado `[S1]–[S15]` al inicio de `synthetic/generate.py` (estados, avance por estado, plazo, etapas del cuello de botella, umbrales de riesgo, sobre-reporte, cobertura, actas, geografía, clasificaciones). Antes estaban enterrados en funciones; ahora se editan en un solo lugar y se regenera. Refactor **value-preserving**: datos byte-idénticos (316 alto / 204 medio / cuello en mampostería 184), el informe no se desfasa. Creado `docs/datos-a-confirmar.md`: checklist para completar en la reunión con el responsable del área, cada fila mapeada a su `[S#]`. Pendiente: la reunión y aplicar las correcciones |
| 2026-06-13 | **Dashboard deployado en Streamlit Cloud** | El deploy fallaba con `FileNotFoundError`: Streamlit Cloud clona el repo y no corre `synthetic.generate`, así que faltaban los CSV. Se **versionó el dataset base** (6 CSV, ~1,1 MB) ajustando el `.gitignore` con negaciones; los derivados de notebooks (procesadas, indicadores) siguen ignorados. `requirements.txt` aligerado: comentadas `opencv-python`/`pytesseract`/`Pillow` (OCR de WS4 — rompen el build en Cloud por `libGL`, el dashboard no las usa) y `jupyter`/`ipykernel` (los notebooks corren en Colab). Nota: Cloud usa Python 3.14; si aparecen fallos de build, fijar versión con `runtime.txt` |
| | | *(próxima entrada: acuerdos de la reunión con el área + WS0 con Desarrollo)* |

---

## 8. Referencias

- Estado y análisis del componente CD: `docs/documentacion-analisis.md`
- Backend Java: `../vivso/` (README propio del equipo de Desarrollo)
- Presentación y guion Hito 2: `docs/prompt-pptx-hito2.md`, `docs/guion-presentacion-hito2.md`
- Constante del plazo contractual: `synthetic/generate.py` → `PLAZO_CONSTRUCCION_DIAS`
