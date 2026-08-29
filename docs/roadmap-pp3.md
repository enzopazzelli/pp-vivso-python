# Ruta de trabajo — PP3 · VIVSO
### Cierre y comunicación · 4° cuatrimestre ITSE

**Equipo:** Pablo Castillo · Sara Lombardi · Valeria Martinetti · Santiago Gallardo · Enzo Pazzelli
**Creado:** 2026-08-20
**Prioridad rectora:** cumplir el entregable oficial de PP3.

> Este documento planifica **PP3** exclusivamente. El histórico de PP2 (Hito 2 y 3, auditoría
> original del backend, bitácora completa del cuatrimestre anterior) queda en
> [ROADMAP.md](../ROADMAP.md) — no se reescribe, se referencia.
> Misma convención: `[ ]` pendiente · `[~]` en progreso · `[x]` hecho · `[!]` bloqueado.

---

## 1. Encuadre oficial

Según `Mapa_Practicas_Profesionalizantes.pdf`, PP3 cubre las etapas **6-Evaluación,
7-Insights, 8-Despliegue en pruebas y 9-Monitoreo**, con entregable de cierre:
**"Presentación profesional a la entidad"**.

Rol de la entidad (Subsecretaría de Promoción Humana) en esta etapa:

- **Aporta:** acceso a datos reales (anonimizados), contexto del problema, validación del análisis.
- **Recibe:** diagnóstico técnico, prototipo funcional y recomendaciones.

Esto tiene una consecuencia directa sobre el orden de trabajo: **sin datos reales ni la
validación del área, no hay evaluación real, ni insights defendibles, ni despliegue en pruebas
con sentido** — todo lo demás depende de destrabar esto primero.

---

## 2. Punto de partida (heredado de PP2, verificado 2026-08-20)

- **`vivso-python`:** Hito 3 cerrado — Informe EDA (`docs/informe-eda.md`), dashboard
  deployado en Streamlit Cloud ([pp-vivso-python.streamlit.app](https://pp-vivso-python.streamlit.app/)),
  pipeline OCR dado de baja del alcance (2026-07-09). Es la base técnica sobre la que se
  construye PP3.
- **Repo migrado (2026-08-20):** de `github.com/enzopazzelli/vivso-python` a
  `github.com/enzopazzelli/pp-vivso-python` — mismo contenido, historial reescrito para que
  Claude no figure como contributor. El deploy anterior de Streamlit Cloud se eliminó y se
  recreó apuntando al repo nuevo, en la URL de arriba.
- **`vivso` (backend Java):** **sin cambios desde `Feature-1.6` (2026-05-06)**. Verificado
  directo en el código: `SecurityConfig` sigue en `permitAll()`, `Visita` sigue siendo solo una
  entidad (`Model/Visita.java`) sin Controller/Service/Repository. Ninguno de los 6 pedidos a
  Desarrollo (ROADMAP.md §5) se resolvió todavía.
- **Reunión de validación con el área:** `docs/datos-a-confirmar.md` está armado y listo para
  usar, pero **la reunión todavía no se hizo** — es la entrada de datos reales que pide el mapa
  oficial de PP3, y hoy es el bloqueante más antiguo del proyecto (pendiente desde Hito 3, junio).

**Lectura:** el trabajo de PP2 dejó todo preparado (documento de validación, arquitectura `cd_*`
acordada internamente, pedidos redactados) pero la etapa de coordinación externa —con el área y
con Desarrollo— no avanzó. PP3 arranca por ahí, no por más código propio.

---

## 3. Bloqueantes críticos (resolver antes de repartir tareas técnicas)

### Bloqueante 1 — Reunión con el área 🔴

Sin esto no hay "datos reales" ni "validación del análisis" (los dos aportes que el mapa oficial
espera de la entidad), y la Evaluación/Insights de PP3 seguirían apoyadas en el dataset
sintético — lo que en la presentación final se nota.

- [ ] Agendar la reunión con el responsable de la Subsecretaría (llevar `datos-a-confirmar.md`
      impreso o en pantalla, y el dashboard corriendo como apoyo visual).
- [ ] Completar el checklist en la reunión (supuestos `[S1]`–`[S15]`, preguntas abiertas de
      dominio, y en particular la pregunta 3: **¿existe un padrón/planilla real que puedan
      compartir?** — es la que determina si hay dato real para trabajar en PP3 o se sigue con
      sintético justificado).
- [ ] Aplicar las correcciones: editar `synthetic/generate.py`, regenerar datos y figuras,
      actualizar `informe-eda.md` (pasos ya documentados al final de `datos-a-confirmar.md`).
- [ ] Si el área entrega datos reales (aunque sea una muestra/Excel): planificar un ETL puntual
      para esa fuente, en paralelo a la integración con `vivso3` (bloqueante 2) — no hace falta
      esperar al backend si el área puede pasar un archivo.

### Bloqueante 2 — Coordinación con Desarrollo (equipo `vivso`) 🔴

El backend lleva **más de tres meses sin commits**. Antes de planificar WS técnicos de
integración hay que saber si ese equipo sigue activo y con qué capacidad.

- [ ] Reunión de contrato técnico con Desarrollo (la que quedó pendiente en el WS0 de PP2):
      llevar la tabla de pedidos de `docs/para-desarrollo.md` §4 y salir con fechas concretas,
      no solo acuerdos generales.
- [ ] Confirmar si el equipo de Desarrollo sigue trabajando en el proyecto para PP3, o si
      quedó descontinuado — esto cambia todo el plan de abajo (ver §6, plan de contingencia).
- [ ] Si sigue activo: priorizar de los 6 pedidos solo los que bloquean PP3 —
      **acceso de lectura a `vivso3`** y **API de `Visita`** son los únicos realmente bloqueantes;
      las 15 clasificaciones y el esquema de roles pueden aproximarse desde el lado de CD si
      Desarrollo no llega a tiempo.

---

## 4. Workstreams por etapa oficial de PP3

Los WS1-WS4 que ya estaban esbozados en `ROADMAP.md` §4 cubrían básicamente la etapa 8
(Despliegue). Acá se completan las etapas 6, 7 y 9 que PP3 pide explícitamente, y se reordenan
según dependencia real de los bloqueantes de arriba.

### Etapa 6 — Evaluación

Objetivo: que el modelo de riesgo y los indicadores dejen de evaluarse "porque tienen sentido
en el sintético" y pasen a evaluarse con criterio y, si es posible, con dato real.

- [ ] Con los supuestos corregidos por el área (bloqueante 1): volver a correr el modelo de
      riesgo y los indicadores, y comparar contra las cifras actuales del Informe EDA — documentar
      qué cambió y por qué (es material directo para la presentación final: "esto decíamos con el
      sintético, esto dice con el dato validado").
- [ ] Métrica de calidad del propio pipeline: cobertura del ETL sobre el dato real (¿qué % de
      registros del área entra sin fricción?, ¿qué columnas no matchean?) — es una evaluación del
      prototipo en sí, no solo del modelo de negocio.
- [ ] Revisar si el modelo de riesgo (regla fija, calibrada a 90 días) sigue siendo defendible
      con los datos reales, o si el corte necesita recalibrarse — sin abandonar el criterio de
      "regla transparente, no caja negra" que ya se defendió en Hito 3.
- [ ] **Separar el motivo del riesgo: `paralizada` vs. `rehaciendo`.** El modelo lee "vencida +
      poco avance = paralizada", y una obra **rechazada por el técnico y en proceso de
      rehacerse** cae exactamente ahí. El problema no es la clasificación (esa obra sí va a
      llegar tarde) sino el **diagnóstico**: llamarla paralizada dispara reclamar por
      inactividad, cuando lo que corresponde es verificar la calidad de la corrección. Esta
      corrección sirve conteste lo que conteste el área. Detalle en
      [vision-afo.md](vision-afo.md) §4.4.
- [ ] Recién después, y solo si el área confirma `[V6]` (que el plazo **se extiende** tras un
      rechazo — supuesto de trabajo actual): agregar `plazo_efectivo = 90 + extensiones`. La
      regla de riesgo sigue sin ramas nuevas. Depende de `[V7]`: que el rechazo quede
      registrado en algún lado, hoy pedido 7 en [para-desarrollo.md](para-desarrollo.md).

### Etapa 7 — Insights

Objetivo: convertir los hallazgos técnicos en recomendaciones accionables para la entidad —
esto es lo que "recibe" la entidad según el mapa oficial, además del prototipo.

- [ ] Consolidar en un documento único (`docs/insights-pp3.md` o sección nueva del informe) los
      hallazgos ya validados con el área: cuello de botella constructivo real (si coincide con
      mampostería o no), sobre-reporte de ONGs, actas atascadas, cobertura de visitas.
- [ ] Por cada hallazgo, una recomendación operativa concreta (a quién visitar, a qué ONG
      auditar, qué trámite destrabar) — mismo criterio "As is → To be con número de ganancia" que
      pidió el profesor en la devolución de Hito 2.
- [ ] Priorizar 3-4 insights fuertes para la presentación final, no listar todos los indicadores
      del dashboard — la lección de esa misma devolución fue justamente no sobrecargar de técnica.

### Etapa 8 — Despliegue en pruebas

Esto es lo que ya estaba planificado como WS1/WS2/WS3/WS4 en `ROADMAP.md` §4. Se mantiene el
mismo diseño de arquitectura (tablas `cd_*`, ETL con fallback `API → MySQL → CSV sintético`,
dashboard por rol) — acá solo se resume el orden de ejecución para PP3:

- [ ] **WS1 — ETL real:** conectar contra `vivso3` (o contra el archivo del área si llegó por el
      bloqueante 1) en vez de depender solo del sintético. Detalle completo en `ROADMAP.md` §4-WS1.
- [ ] **WS2 — Capa analítica `cd_*`:** materializar los indicadores en la base, job
      `analytics.refresh` idempotente. Detalle en `ROADMAP.md` §4-WS2.
- [ ] **WS3 — Dashboard por roles:** vistas Ministerio/Técnico/ONG con el gancho de auth simulada
      ya diseñado. Incluye la mejora de confiabilidad en la página de ONGs ya identificada.
      Detalle en `ROADMAP.md` §4-WS3.
- [ ] **WS4 — Avances reportados por ONG:** cruzar reporte ONG vs. verificación técnica con datos
      reales una vez que Desarrollo defina dónde persiste el avance reportado. Detalle en
      `ROADMAP.md` §4-WS4.
- [ ] "Despliegue en pruebas" (no producción): definir qué significa concretamente para la
      entrega — ¿el dashboard corriendo en Streamlit Cloud contra `vivso3` real ya cumple, o el
      área espera algo alojado en su propia infraestructura? Aclarar esto en la reunión del
      bloqueante 1 para no sobre-construir.

### Etapa 9 — Monitoreo

Objetivo: que el sistema no sea una demo de un día — que la entidad pueda seguir viéndolo
actualizado después de que termine la práctica.

- [ ] Definir la frecuencia de refresco de `cd_*` (el job de WS2 ya es idempotente y
      re-ejecutable; falta decidir manual/diario/automático — propuesta inicial: manual mientras
      dure PP3, con instrucciones claras para que el área lo corra o lo pida).
- [ ] Definir qué pasa con el proyecto después del cierre de PP3: ¿alguien del área o de
      Desarrollo queda a cargo de correr el refresco?, ¿el equipo de CD deja de tener acceso? —
      dejarlo explícito en la documentación de traspaso final.
- [ ] Alertas mínimas de monitoreo (no de infraestructura, de negocio): que el propio dashboard
      señale cuándo los indicadores no se refrescan hace tiempo (dato ya desactualizado), para que
      no se use información vieja sin saberlo.

---

## 5. Entregable final: presentación profesional a la entidad

- [ ] Formato objetivo: presentación real a la Subsecretaría (no solo al profesor) — más
      formal que la de Hito 2/3, con foco en decisiones de gestión, no en el pipeline.
- [ ] Estructura sugerida (aplicando las lecciones de la devolución de Hito 2, ver
      `ROADMAP.md`/histórico y [[feedback-presentaciones-codigo]] en memoria): diagnóstico (As is)
      → qué se construyó → insights priorizados (§4-Etapa 7) → recomendaciones → qué sigue
      (monitoreo, quién queda a cargo).
- [ ] Guion como mapa de defensa, no libreto — mismo protocolo que ya funcionó: leer una vez,
      explicar sin mirar, preguntas cruzadas.
- [ ] Confirmar fecha de la presentación con el profesor y, si es posible, con el referente del
      área, apenas se resuelva el bloqueante 1.

---

## 6. Plan de contingencia — si Desarrollo no avanza

Dado que el backend lleva 3+ meses congelado, vale la pena tener un plan B explícito en vez de
descubrirlo tarde:

- Si para [fecha límite a definir con el profesor] Desarrollo no dio acceso a `vivso3` ni movió
  la API de `Visita`: el despliegue en pruebas (etapa 8) se sostiene igual con el dato real que
  haya entregado el área directamente (Excel/CSV, bloqueante 1), sin depender del backend Java.
- El diseño de las tablas `cd_*` y el ETL con fallback ya están pensados para no bloquearse por
  esto — es cuestión de decisión, no de rediseño.
- Documentar el intento de coordinación (fechas, pedidos, respuestas) igual que se documentó
  todo en PP2: si Desarrollo no responde, es un hallazgo válido para la presentación final
  ("brecha de coordinación entre equipos"), no un fracaso a ocultar.

---

## 7. Bitácora (PP3)

| Fecha | Evento / Decisión | Detalle |
|---|---|---|
| 2026-08-29 | **Mapa fijado a la provincia y dispersión geográfica realista** | El mapa recalculaba el centro a partir de lo que estuviera filtrado y usaba zoom fijo 6 (a ese zoom, ~800px muestran ~17,6° de longitud — casi 5x el ancho real de la provincia, ~3,2°): con cualquier filtro chico el mapa "saltaba" a otra zona y no se leía como Santiago del Estero. Se fija centro (centroide ponderado por población, `dashboard/components/mapa.py`) y zoom (6,7) en los dos mapas provinciales (`app.py`, `01_viviendas.py`); el mapa de zona del técnico (`05_mis_obras.py`) se deja con auto-centrado, que ahí es lo correcto. Además, el ruido de coordenadas pasó de un radio fijo (~2 km para todos los departamentos) a `[S17]`: `DISPERSION_BASE / sqrt(peso)`, entre ~5 km en Capital/Banda (denso) y ~16 km en los rurales de peso bajo — en vez de apilar todo sobre el centro exacto de cada cabecera |
| 2026-08-29 | **Dataset ampliado a 5.000 viviendas y finalización subida a 65%** | Decisión del equipo para la demo (no dato del área): tamaño `--n 1500 → 5000` y `[S2]` ajustado (terminadas ~40% → ~65%). Al regenerar apareció un bug real en `garantizar_casos()`: el perfil "eficiente" (COOP SAN ANTONIO) nunca llegaba a `Finalizada` por un límite superior exclusivo en `rng.integers` — con el 40% de finalización general pasaba desapercibido; con 65% la referencia positiva terminaba *menos* que el promedio, y eso sí se nota. Corregido con asignación explícita de estado; terminación por gestora quedó COOP SAN ANTONIO 74,9% (por encima del promedio, coherente con "eficiente") · CONSTRUIR JUNTOS 16,0% (por debajo, coherente con "problemática") · MUTUAL PROGRESO 100% · programa general 64,2%. **El Informe EDA vuelve a quedar con cifras pendientes de recálculo** (banner actualizado) |
| 2026-08-28 | **Componente de visión implementado con percepción simulada** | Módulo `vision/` completo y corriendo **sin API y sin fotos**: rúbrica con los supuestos `[V#]` como constantes, esquema de salida estructurada, capa de decisión determinista, harness de evaluación y página «Verificación por foto» en el dashboard. Guía de presentación en [prompt-pptx-vision.md](prompt-pptx-vision.md). Construir destapó dos correcciones que el diseño en papel no había visto: **la evidencia tiene restricciones de coherencia física** (no hay encadenado sin muros — sin ese chequeo, los errores catastróficos de lectura encabezaban la cola y desplazaban a los sobre-reportes reales), y **la secuencialidad se aplica en los dos sentidos** (la capa aisladora queda enterrada, así que confirmar un rubro tiene que implicar los anteriores). Resultado medible hoy: con un modelo que se equivoca en el 10% de los campos, **82% de acierto en las primeras 50 obras de la cola contra 23,6% al azar** — y el sistema degrada abstiéndose, no inventando |
| 2026-08-28 | **La unidad de análisis es la solicitud** | La gestora solicita las viviendas, así que hay una etapa anterior al expediente que hoy no se modela: el dataset arranca **después de la aprobación**. Consecuencias: sesgo de supervivencia (solo se ven solicitudes aprobadas), posible **tercer cuello de botella en la entrada** —y sería del propio ministerio, como el de las actas— y la solicitud como unidad de análisis por encima de la gestora. Desarrollo ya trabaja en una capa intermedia donde quedan las no aprobadas. **No modelado todavía**: es el próximo frente estructural, después del componente de visión |
| 2026-08-28 | **Las gestoras no son solo ONGs — y [S9] refutado** | El programa se ejecuta a través de **cuatro tipos** de gestora: municipio, comisión municipal, ONG y cooperativa. Se agregó `tipo_gestora` (`db/models.py`) y el catálogo `TIPOS_GESTORA` con el **ámbito** derivado Público/Privado (`db/setup.py`), que es donde se parte la palanca del ministerio: al municipio se le gestiona institucionalmente, a la ONG se le reclama por convenio. El dataset pasó de 3 a **8 gestoras** (2 por tipo) con reparto parejo — nuevo supuesto **[S16]**, sin confirmar. Y se refutó **[S9]**: modelaba un 20% de obras "sin gestora asignada", que es imposible porque **la gestora es quien solicita las viviendas, no al revés**. Consecuencia: hay que **recalcular las cifras del Informe EDA** (secciones 4-6) y regenerar las figuras |
| 2026-08-28 | **Propuesta: verificación fotográfica del AFO** | Diseño en [vision-afo.md](vision-afo.md). Un modelo de visión lee las fotos que adjunta la ONG y devuelve **evidencia física observable**; la conversión a rubro y a % de AFO la hace una regla determinista con el catálogo existente. Salida: un **grado de respaldo documental** del reporte de la ONG — no una aprobación automática; el AFO lo sigue certificando el técnico. Confirmado con el equipo que en agua y electricidad las mangueras van vacías y embutidas durante la mampostería, y que los rubros 11 y 12 certifican tanque/conexiones y cables/tablero: eso deja **87% del AFO auditable por foto** (97% con protocolo de captura). Motivo estratégico: es la primera línea de trabajo que no depende de ninguno de los dos bloqueantes de §3 — el dato son fotos del área, no acceso a `vivso3` |
| 2026-08-20 | **Ruta de trabajo de PP3 creada** | Este documento. Verificado contra el código: backend `vivso` sin cambios desde `Feature-1.6` (2026-05-06, `permitAll()` y `Visita` sin API); reunión con el área todavía sin realizar. Encuadre oficial confirmado con `Mapa_Practicas_Profesionalizantes.pdf`: PP3 = etapas 6-9, entregable "Presentación profesional a la entidad". Los dos bloqueantes críticos identificados: reunión con el área y coordinación con Desarrollo — ambos pendientes desde Hito 3. |

---

## 8. Referencias

- **Supuestos abiertos y qué se pregunta (punto de entrada único): [supuestos-abiertos.md](supuestos-abiertos.md)**
- Verificación fotográfica del AFO (diseño): [vision-afo.md](vision-afo.md)
- Ruta y bitácora completa de PP2: `ROADMAP.md`
- Guía de integración para Desarrollo (pedidos, brechas): `docs/para-desarrollo.md`
- Checklist de validación con el área: `docs/datos-a-confirmar.md`
- Informe EDA (Hito 3): `docs/informe-eda.md`
- Mapa oficial de la práctica: `../Mapa_Practicas_Profesionalizantes.pdf`
