# Verificación fotográfica del AFO — documento de diseño
## Componente de Ciencia de Datos · PP3 · ITSE

**Creado:** 2026-08-28
**Estado:** propuesta de diseño — no implementado
**Encaja en:** PP3, etapas 6-Evaluación, 7-Insights y 8-Despliegue en pruebas
([roadmap-pp3.md](roadmap-pp3.md))

---

## 1. Qué es y qué no es

La propuesta es que, cuando una gestora reporta un avance de obra, las fotos que adjunta se
usen para **ponderar ese reporte**: decir si la evidencia visual lo respalda, lo contradice
o no alcanza para determinarlo.

> **Gestora** = quien solicita las viviendas y se hace cargo de la obra. Son de cuatro tipos
> —municipio, comisión municipal, ONG y cooperativa (`tipo_gestora`)— y eso importa acá: el
> respaldo fotográfico se calcula igual para todas, pero **la acción que habilita cambia
> según el tipo**. Ante una contradicción, a un municipio o comisión municipal se le gestiona
> institucionalmente; a una ONG o cooperativa se le reclama por convenio.

> **El sistema no aprueba nada.** El AFO lo sigue certificando el técnico, con su OK y sus
> observaciones. La certificación de avance tiene consecuencia de pago; automatizarla no
> está en discusión. Lo que se automatiza es el **triage**: a qué obra conviene ir primero.

Tres cosas que el sistema **no** hace, y conviene que estén escritas:

- No estima el AFO por su cuenta para reemplazar al técnico.
- No emite veredictos de calidad constructiva. Puede señalar una fisura o una humedad como
  *observación para el técnico*, nunca como rechazo.
- No sustituye la visita. La extiende: hoy el tope es de 2 visitas por obra y ~70% de las
  obras activas no recibió ninguna.

**El "As is → To be":** hoy el avance que reporta la gestora entra al sistema sin ningún
respaldo para el ~70% de obras sin visita. Con esto, cada reporte entra con un grado de
respaldo documental, y el técnico recibe una cola priorizada en lugar de una lista plana.

---

## 2. El reencuadre que hace viable la idea

La versión intuitiva — "una red neuronal mira la foto y devuelve el % de avance" — se
descarta por tres motivos: no es explicable ante una gestora, no se puede validar sin fotos
etiquetadas, y es **redundante**. El AFO ya es una función determinista: suma ponderada de
15 rubros estrictamente secuenciales, con los pesos ya definidos en `db/setup.py`
(`RUBROS_CATALOGO`).

El modelo no tiene que estimar el número. Tiene que estimar **la evidencia**:

```
FOTO ──► capa de percepción (modelo de visión)
           └─► evidencia física observable
               (¿hay muros? ¿a qué altura? ¿encadenado? ¿revoque? ¿aberturas?)

     ──► capa de decisión (Python determinista)
           └─► rubro alcanzado ──► AFO % (fórmula y pesos existentes)
               + secuencialidad + monotonía + contraste con lo declarado
```

La aritmética la hace el código que ya existe. Lo que ve el técnico es:

> *La foto muestra muros de block completos con encadenado visible y sin revoque exterior
> → rubro 5 completo → **AFO 33%**. La gestora reportó **60%**. Discrepancia de 27 puntos.*

Eso se defiende en una reunión. Un "62%" salido de una caja negra, no. Es el mismo criterio
que ya se sostuvo en Hito 3 para el modelo de riesgo: **regla transparente, no caja negra.**

---

## 3. Rúbrica de evidencia observable

El insumo central del diseño. Para cada rubro del catálogo oficial, qué se ve en una foto
cuando ese rubro está terminado.

| # | Rubro | Peso | Acum. | Evidencia observable | Toma |
|---|---|---|---|---|---|
| 1 | Terreno y limpieza | 3 | 3 | Terreno despejado, replanteo marcado, sin escombros | Exterior |
| 2 | Excavación e impermeabilización | 5 | 8 | Zanjas de cimiento abiertas; capa aisladora colocada **antes de tapar** | Exterior · ventana temporal |
| 3 | Mampostería hasta dintel | 10 | 18 | Muros de ladrillo hasta ~2,10 m, dinteles colocados sobre los vanos | Exterior |
| 4 | Mampostería cerámico/Block | 10 | 28 | Muros cerrados sobre dintel hasta altura final | Exterior |
| 5 | Encadenado | 5 | 33 | Viga de hormigón armado en la corona del muro, encofrado retirado | Exterior |
| 6 | Revoque interior | 10 | 43 | Paredes interiores con grueso y fino, ladrillo ya no visible | Interior |
| 7 | Revoque exterior | 8 | 51 | Fachada revocada, sin ladrillo a la vista | Exterior |
| 8 | Cielorraso con aislante térmico | 5 | 56 | Estructura de cielorraso montada; el aislante se ve **antes de cerrar** | Interior · ventana temporal |
| 9 | Construcción de cielorrasos | 4 | 60 | Cielorraso cerrado, terminado y pintado | Interior |
| 10 | Carpintería | 10 | 70 | Puertas y ventanas colocadas (vanos ya no vacíos), herrería puesta | Exterior + Interior |
| 11 | Instalación de agua | 7 | 77 | **Tanque colocado**, canillas y conexiones finales | Exterior (tanque) + Interior |
| 12 | Instalación eléctrica | 8 | 85 | **Tablero instalado**, llaves y tomacorrientes colocados, artefactos | Interior |
| 13 | Instalación sanitaria | 7 | 92 | **Artefactos colocados**: inodoro, lavatorio, ducha | Interior |
| 14 | Revestimiento exterior | 5 | 97 | Fachada terminada, revestimiento y pintura exterior | Exterior |
| 15 | Varios | 3 | 100 | Sin manifestación visible única | — |

### La regla que hace auditable al catálogo

Los rubros 11 y 12 parecen trabajo enterrado, pero no lo son. Confirmado con el equipo
(2026-08-28, a ratificar con el área):

> Tanto en agua como en electricidad, durante la mampostería se pasan **mangueras vacías**
> por las paredes y se tapan con el revoque. Ese trabajo queda absorbido en los rubros de
> mampostería y revoque — **no es un rubro propio**. Lo que certifican los rubros 11 y 12 es
> lo que viene después: el pasaje de cables, el tablero, las bocas, el tanque, las
> conexiones. Todo eso es superficie y se ve.

De ahí sale el principio general del diseño: **el AFO no mide trabajo enterrado, mide hitos
con manifestación visible.** El catálogo está construido, casi por diseño, sobre cosas que
se ven. Es lo que hace que la propuesta sea viable en vez de aspiracional.

### Cobertura fotográfica resultante

| Verificabilidad | Rubros | Peso AFO |
|---|---|---|
| **Alta** — evidencia visible en cualquier momento posterior | 1, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14 | **87%** |
| **Ventana temporal** — requiere foto en el momento, después queda tapado | 2 (capa aisladora), 8 (aislante térmico) | **10%** |
| **No verificable** | 15 (varios) | **3%** |

**87% del AFO es auditable con fotos oportunistas; 97% si el protocolo de carga obliga a
capturar las dos ventanas temporales.** Eso convierte al protocolo de carga (§7) en parte
del diseño y no en un detalle de implementación.

---

## 4. Arquitectura

### Capa de percepción

Modelo de visión con **salida estructurada** — checklist cerrado, nunca texto libre. El
esquema fuerza al modelo a responder solo sobre evidencia observable, y a poder abstenerse.

```python
EVIDENCIA_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["tipo_toma", "evidencia", "confianza", "observaciones"],
    "properties": {
        "tipo_toma": {"enum": ["fachada_completa", "interior", "detalle", "no_util"]},
        "evidencia": {
            "type": "object", "additionalProperties": False,
            "required": ["muros", "encadenado", "revoque_ext", "revoque_int",
                         "cielorraso", "aberturas", "tanque_agua",
                         "tablero_electrico", "artefactos_sanitarios",
                         "revestimiento_ext"],
            "properties": {
                "muros":       {"enum": ["ninguno", "fundacion", "hasta_dintel",
                                         "completo", "no_determinable"]},
                "encadenado":  {"enum": ["si", "no", "no_determinable"]},
                "revoque_ext": {"enum": ["ninguno", "grueso", "fino", "no_determinable"]},
                "revoque_int": {"enum": ["ninguno", "grueso", "fino", "no_determinable"]},
                "cielorraso":  {"enum": ["ninguno", "estructura", "terminado",
                                         "no_determinable"]},
                "aberturas":   {"enum": ["vanos_vacios", "parcial", "colocadas",
                                         "no_determinable"]},
                "tanque_agua": {"enum": ["si", "no", "no_determinable"]},
                "tablero_electrico":     {"enum": ["ninguno", "sin_bocas", "completo",
                                                   "no_determinable"]},
                "artefactos_sanitarios": {"enum": ["ninguno", "parcial", "completos",
                                                   "no_determinable"]},
                "revestimiento_ext":     {"enum": ["ninguno", "parcial", "terminado",
                                                   "no_determinable"]},
            }
        },
        "confianza":     {"enum": ["alta", "media", "baja"]},
        "observaciones": {"type": "string"},   # fisuras, humedad, ejecución dudosa
    }
}
```

Tres decisiones de diseño en ese esquema:

- **`no_determinable` en cada campo y `no_util` como tipo de toma.** Un sistema que siempre
  responde algo es un sistema en el que el técnico deja de confiar la tercera vez que se
  equivoca con una foto mala. La tasa de abstención es una métrica, no un fracaso.
- **`observaciones` es texto para el técnico, nunca un veredicto.** Es donde vive la lectura
  cualitativa sin que el sistema se atribuya una decisión que no le corresponde.
- **Un solo campo por evidencia física, no por rubro.** El mapeo evidencia → rubro lo hace
  la capa de decisión, no el modelo.

Llamada de referencia (Python, SDK `anthropic`):

```python
resp = client.messages.create(
    model="claude-opus-5",
    max_tokens=2000,
    thinking={"type": "adaptive"},
    cache_control={"type": "ephemeral"},   # la rúbrica es estable → se cachea
    system=RUBRICA,                        # §3 de este documento, como prompt
    output_config={"format": {"type": "json_schema", "schema": EVIDENCIA_SCHEMA}},
    messages=[{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                     "data": foto_b64}},
        {"type": "text", "text": f"Obra {obra_id}. Último rubro verificado: {rubro_prev}."},
    ]}],
)
```

### Capa de decisión (determinista)

```
rubro_alcanzado = máximo n tal que la evidencia confirma el rubro n
                  y todos los rubros anteriores son consistentes  ← secuencialidad
afo_estimado    = suma de pesos de los rubros 1..n                ← catálogo existente
```

Más dos chequeos que son información gratis y no hay que aprender:

- **Secuencialidad:** el rubro N exige el N-1 al 100%. Un salto sin explicación es señal,
  no resultado.
- **Monotonía:** una obra no retrocede. Contra el histórico de la misma obra, una evidencia
  que muestra menos que la verificación anterior es un error de lectura o una foto vieja.

Un clasificador apenas decente por imagen se vuelve un sistema utilizable cuando el previo
físico hace la mitad del trabajo.

### Dónde vive en el repo

```
vision/                     ← módulo nuevo (percepción + regla)
data/fotos/                 ← gold set local, no versionado
docs/vision-afo.md          ← este documento
dashboard/pages/            ← página nueva "Verificación por foto"
```

Los resultados van a una tabla **`cd_afo_foto`**, que encaja en la capa `cd_*` ya acordada
con Desarrollo — misma convención, mismo job de refresco idempotente.

---

## 5. La salida: grado de respaldo del reporte

La unidad de trabajo no es la foto: es el **reporte** (obra + fecha + % declarado + fotos
adjuntas). Lo que el sistema emite es un grado de respaldo documental.

| Grado | Cuándo | Efecto |
|---|---|---|
| **Respaldado** | Evidencia consistente con lo declarado (tolerancia ±1 rubro) | Suma normal al índice de confiabilidad |
| **Contradicho — sobre-reporte** | La foto muestra menos que lo declarado | Va al tope de la cola de visitas |
| **Contradicho — sub-reporte** | La foto muestra más que lo declarado | Señal distinta: reporte desactualizado, no deshonestidad |
| **Sin respaldo** | No hay foto, o no cumple el protocolo | El reporte pesa menos; no se penaliza como mentira |
| **No determinable** | Foto útil, pero el rubro declarado cae en zona no verificable | Neutro |

Las dos últimas filas son las que hacen honesto al sistema: distinguen *"la gestora está
sobre-reportando"* de *"no tengo cómo saberlo"*. Hoy el índice de confiabilidad no puede
separar esas dos cosas — y esa es exactamente la ponderación que falta.

---

## 6. Qué le suma a lo que ya existe

Esto es una extensión de los indicadores actuales, no un proyecto paralelo:

| Indicador existente | Qué gana |
|---|---|
| Score de priorización de visitas | Nueva señal de entrada: las obras con contradicción fotográfica encabezan la cola |
| Alerta de sobre-reporte | Deja de depender de las visitas, que cubren ~30% de las obras activas |
| Índice de confiabilidad de gestora (componente honestidad, 20%) | Pasa de proxy a evidencia documental |

### El efecto secundario que vale más que el sistema

Si el técnico siempre da el OK y deja observaciones, **cada decisión suya es una etiqueta**:
el sistema propone, el técnico confirma o corrige, y eso queda guardado. Sin campaña de
etiquetado y sin pedirle trabajo extra a nadie, en unos meses existe el dataset etiquetado
real que hoy no existe — que es justamente la condición que bloquea entrenar un modelo
propio (§9).

**Consecuencia de diseño:** `cd_afo_foto` debe incluir el campo de resolución del técnico
(confirma / corrige / descarta) desde el día uno, aunque en PP3 no se use para entrenar.

---

## 7. Protocolo de carga y antifraude

La gestora tiene incentivo económico en el avance que reporta, así que el protocolo es parte
del diseño y no un agregado:

- **Captura dentro de la app, no subida desde galería.** WhatsApp borra el EXIF, y sin EXIF
  no hay nada que verificar. La app debe distinguir foto capturada (metadatos confiables) de
  foto adjuntada (metadatos no confiables).
- **GPS de la foto contra las coordenadas de la vivienda** — la capa geo ya existe en el
  frontend — y timestamp contra la fecha del reporte.
- **Hash perceptual (pHash)** para detectar foto reutilizada entre obras, o repetida entre
  dos reportes de la misma obra.
- **Tomas obligatorias:** fachada frontal completa, lateral, interior principal, y detalle
  del rubro declarado. Mitiga parcialmente el sesgo obvio de que la gestora sube su mejor foto.
- **Ventanas temporales:** para los rubros 2 y 8 el protocolo debe pedir la foto en el
  momento, o esos 10 puntos de AFO quedan sin respaldo posible (§3).

> El desarrollo de la app de carga es del equipo de Desarrollo/frontend, no de CD. Lo que
> aporta este documento es **qué tiene que capturar** para que el análisis sea posible.

---

## 8. Plan de evaluación — etapa 6 de PP3

Sin esto es una demo, no un entregable.

**Gold set:** 100-150 fotos etiquetadas por el grupo y **validadas por un técnico del área**.
Fuente preferida: fotos que el área o las gestoras ya tengan (hoy circulan por WhatsApp).
Fuente de respaldo: imágenes públicas de construcción de vivienda social — peor validez
externa, pero permite avanzar.

**Métricas:**

| Métrica | Para qué |
|---|---|
| Acierto de rubro exacto y con tolerancia ±1 | Diagnóstico interno del modelo |
| MAE en puntos de AFO | Conecta con el indicador que ya existe |
| Precisión / recall de la alerta "contradice lo reportado" | La métrica operativa |
| Tasa de abstención | Salud del sistema: cuánto admite no saber |
| **Precision@K** | **La métrica que se presenta al área** |

**Precision@K es la que importa:** de las obras que el técnico terminó observando, cuántas
estaban en el top-K que el sistema le marcó. Responde la única pregunta que le interesa al
área — *"¿me hace ahorrar viajes o no?"*.

**Punto de operación:** como asistente, conviene privilegiar recall. El técnico revisa igual;
un falso positivo cuesta minutos, un falso negativo deja pasar sobre-reporte.

**Baseline a superar:** el estado actual es creerle a la gestora sin verificación. Es un baseline
bajo y honesto, y cualquier mejora sobre él es ganancia medible sin inflar nada.

---

## 9. Alcance para PP3

| Fase | Qué | Entregable |
|---|---|---|
| 0 | Rúbrica de evidencia (§3) + tabla de verificabilidad. Sin código. | Insumo para la reunión con el área |
| 1 | Gold set + baseline zero-shot + matriz de confusión | **Etapa 6 — Evaluación** |
| 2 | Capa de decisión (secuencialidad, monotonía, contraste) + integración con indicadores | **Etapa 7 — Insights** |
| 3 | Página en el dashboard + demo end-to-end con 3-4 casos | **Etapa 8** + presentación final |

Fase 0 **usa** la reunión con el área en lugar de esperarla: la rúbrica es material concreto
que un técnico valida en minutos.

### Fuera de alcance, explícitamente

- **La app de carga para gestoras** — es de Desarrollo/frontend. CD define qué capturar (§7).
- **Entrenar un modelo propio de visión.** 150 fotos son un test set, no un training set.
  Queda como línea futura con condición numérica explícita, y §6 explica cómo se llega ahí.
- **Cualquier aprobación automática del AFO.** Ver §1.
- **Veredicto automático de calidad constructiva.** Solo observación para el técnico.

### Por qué esto no repite el pipeline OCR dado de baja

El OCR (OpenCV + Tesseract) se retiró el 2026-07-09 porque el equipo tenía que **construir y
calibrar** un pipeline de visión propio sin dato con qué calibrarlo. Acá el modelo de visión
no se construye: se consume por API. Lo que construye el equipo es la rúbrica, la regla
determinista y la evaluación — que es trabajo de ciencia de datos, no de ingeniería de visión.

### Por qué destraba los bloqueantes de PP3

**El dato real de este componente no está en la base del Ministerio.** Está en los teléfonos
de los técnicos y en los WhatsApp de las gestoras. Pedirle al área 50-100 fotos es un pedido
mucho más chico que el acceso a `vivso3`, y no pasa por el equipo de Desarrollo. Es la
primera línea de trabajo del proyecto que no depende de ninguno de los dos bloqueantes de
`roadmap-pp3.md` §3.

---

## 10. Costo

Estimación de orden de magnitud, a medir con `count_tokens` antes de comprometerla:

| Escenario | Costo aprox. |
|---|---|
| Una foto (rúbrica cacheada) | ~US$ 0,02 |
| Gold set completo, 150 fotos — **lo que cuesta PP3** | **~US$ 3** |
| 1.500 obras × 4 fotos, sin optimizar | ~US$ 90 |
| Ídem con caching de rúbrica + Batch API (50%) | bastante menos |

Para el prototipo de PP3 el costo es irrelevante. Vale la pena decirlo en la presentación
porque va a ser la primera objeción.

---

## 11. Supuestos a confirmar y riesgos

Convención `[V#]`, análoga a los `[S#]` de [datos-a-confirmar.md](datos-a-confirmar.md).

| ID | Supuesto | Estado |
|---|---|---|
| [V1] | En agua y electricidad las mangueras van vacías y embutidas durante mampostería; los rubros 11 y 12 certifican cables/tablero y tanque/conexiones | Confirmado por el equipo 2026-08-28 · ratificar con el área |
| [V2] | El rubro 15 "Varios" no tiene manifestación visible propia | Sin confirmar |
| [V3] | El área o las gestoras conservan fotos de obras que puedan compartir | **Sin confirmar — condiciona la Fase 1** |
| [V4] | Las gestoras hoy envían fotos por WhatsApp como parte del reporte informal | Sin confirmar |
| [V5] | La tolerancia de ±1 rubro es aceptable para el criterio del área | Sin confirmar |

**Riesgos:**

- **[V3] es el riesgo real, y no es técnico.** Si el área no tiene fotos, el gold set sale de
  imágenes públicas y la validez externa cae. Conviene preguntarlo *antes* de la reunión,
  porque cambia la Fase 1 entera.
- **Sesgo de selección:** la gestora sube la foto que más le conviene. El protocolo de tomas
  obligatorias lo mitiga en parte, no lo elimina.
- **Foto ≠ obra:** hay un 3% no verificable y un 10% que depende de capturar la ventana
  temporal. Hay que decirlo desde el primer minuto o el área se decepciona después.
- **Dependencia de un proveedor externo** para la capa de percepción. La capa de decisión es
  propia y no se ve afectada; el modelo es reemplazable sin rediseñar el sistema.

---

## 12. Referencias

- Catálogo oficial de rubros y pesos: `db/setup.py` → `RUBROS_CATALOGO`
- Ruta de trabajo de PP3: [roadmap-pp3.md](roadmap-pp3.md)
- Checklist de validación con el área: [datos-a-confirmar.md](datos-a-confirmar.md)
- El porqué de cada análisis: [documentacion-analisis.md](documentacion-analisis.md)
- Guía de integración para Desarrollo: [para-desarrollo.md](para-desarrollo.md)
- Capturas del AFO en el sistema legacy: `docs/afo.jpeg`, `docs/tipos.jpeg`
