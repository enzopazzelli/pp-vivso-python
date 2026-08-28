# Prompt — Presentación PPTX · Verificación fotográfica del AFO (PP3)

Generá una presentación profesional en formato PowerPoint (.pptx) para presentar el
componente de **verificación fotográfica del avance de obra** del sistema VIVSO.

> Este prompt aplica las reglas obligatorias de [guia-presentaciones.md](guia-presentaciones.md)
> (devolución del profesor sobre el Hito 2): **As is → To be en cada indicador, resultados
> antes que métodos, ganancia cuantificada, un mensaje por slide, código casi cero (máximo
> 1 slide)**. Si algo de acá entra en conflicto con esa guía, gana la guía.

No fija una plantilla rígida de slides. Lo no negociable es el **orden de las ideas**, el
**tono** (una propuesta en construcción, no una victoria) y los **datos** citados, todos
verificados contra el dataset y el prototipo (ver §Datos verificados al final).

---

## Contexto

**Institución cliente:** Subsecretaría de Promoción Humana — Ministerio de Desarrollo Social, Santiago del Estero
**Carrera:** Ciencia de Datos — ITSE · **Grupo:** 8
**Equipo:** Pablo Castillo · Sara Lombardi · Valeria Martinetti · Santiago Gallardo · Enzo Pazzelli
**Footer de todas las diapositivas:** `PP3 · Grupo 8`

Este componente **no es la obligación de PP3**: el dashboard y el Informe EDA ya la cubren.
Es trabajo adicional, hecho para seguir construyendo. Eso hay que decirlo, porque cambia
cómo se recibe: no se está pidiendo aprobación de un requisito, se está mostrando una
propuesta funcionando.

---

## Tono (leer antes de escribir cualquier slide)

- **Es una propuesta con prototipo, no un sistema entregado.** La capa de percepción está
  **simulada**: no hay fotos ni modelo de visión conectado. Decirlo temprano y sin rodeos
  — esconderlo y que lo descubran en la ronda de preguntas es mucho peor.
- **Nada de "logramos" ni "validamos".** Se describe qué se construyó y qué se midió.
- El registro es de **trabajo con rigor**, no de trofeos.
- La honestidad sobre los límites es parte del argumento: un sistema que dice "no sé" es
  más creíble que uno que siempre responde.

---

## Narrativa

### Bloque 1 — El problema, en una imagen

La gestora reporta que la obra va al 60%. Nadie lo verifica.

Datos: el tope es de **2 visitas técnicas por obra**, y **213 de 908 obras activas (23,5%)
no recibió ninguna**. Para esas obras, el avance que figura en el sistema es exactamente lo
que declaró quien cobra por ese avance. No es una sospecha de mala fe: es una ausencia de
contraste.

*Un mensaje por slide: hoy el avance no tiene respaldo.*

### Bloque 2 — La idea, y lo que NO es

La gestora ya adjunta fotos. Usarlas para **ponderar su reporte**.

Tres cosas que el sistema **no** hace, y conviene ponerlas en la misma slide porque
adelantan las tres objeciones obvias:

- **No aprueba nada.** El AFO lo sigue certificando el técnico.
- **No reemplaza la visita.** La extiende a las obras que hoy nunca reciben una.
- **No juzga la calidad constructiva.** Puede señalar una fisura como observación para el
  técnico, nunca como rechazo.

### Bloque 3 — Por qué funciona: el modelo no estima el porcentaje

**Esta es la slide central de la presentación.** La idea intuitiva sería "una red neuronal
mira la foto y dice el porcentaje". Se descartó a propósito.

El AFO ya es una fórmula: suma ponderada de **15 rubros estrictamente secuenciales**, con
pesos que ya existen en el sistema. Entonces el modelo no tiene que estimar el número —
tiene que estimar **la evidencia**:

```
FOTO → evidencia física observable  →  regla determinista  →  rubro → AFO
      (¿hay muros? ¿encadenado?         (el catálogo de
       ¿revoque? ¿aberturas?)            pesos que ya existe)
```

Y lo que ve el técnico no es un número, es un motivo:

> *La foto muestra muros de block completos con encadenado visible y sin revoque exterior
> → rubro 5 completo → **AFO 33%**. La gestora reportó **60%**.*

**Eso se puede discutir con una gestora. Un "62%" salido de una caja negra, no.** Es el
mismo criterio con el que ya se defendió el modelo de riesgo: regla transparente.

*Esta es la única slide donde puede aparecer algo parecido a código o fórmula, y solo si
la regla ES el mensaje.*

### Bloque 4 — As is → To be (la slide que pidió el profesor)

| Proceso del área | AS IS (hoy) | TO BE (con verificación por foto) | Ganancia |
|---|---|---|---|
| Verificar lo que reporta la gestora | Solo con visita presencial, tope de 2 por obra | Cada foto adjunta le pone un grado de respaldo al reporte | **213 obras activas sin ninguna verificación** pasan a tener respaldo documental |
| Elegir a qué obra ir | Por cercanía o criterio propio | Cola ordenada por contradicción entre lo declarado y lo que muestra la foto | **82% de acierto en las primeras 50** vs. 23,6% eligiendo al azar → **3,5× mejor** |
| Discutir un avance con la gestora | "El sistema dice que va al 60%" | "La foto muestra rubro 5 terminado, eso es 33%" | De un número opaco a un motivo verificable |
| Detectar sobre-reporte | Solo donde hubo visita; una gestora está al **0% de cobertura** | Sobre cualquier obra que adjunte foto | El control deja de depender de la logística de campo |

### Bloque 5 — Qué se puede ver en una foto, y qué no

Slide de credibilidad. **No prometer de más.**

- **87% del AFO es auditable** con fotos oportunistas.
- **97%** si el protocolo de carga obliga a capturar dos momentos puntuales (la capa
  aisladora antes de tapar el cimiento, y el aislante antes de cerrar el cielorraso).
- **3% no es verificable** (el rubro "Varios").

El hallazgo que lo hace posible: **el AFO no mide trabajo enterrado, mide hitos con
manifestación visible.** Las mangueras de agua y electricidad van embutidas durante la
mampostería —ese trabajo está absorbido en otros rubros—; los rubros 11 y 12 certifican lo
posterior y visible: tanque y conexiones, tablero y bocas.

### Bloque 6 — El resultado que se midió, sin tener una sola foto

Slide fuerte y honesta. Explicar la idea en una línea: como el sistema ya sabe en qué rubro
está cada obra, se puede **simular** lo que un modelo vería, degradarlo con un error
controlado y medir cómo se comporta el sistema completo.

Eso contesta una pregunta de diseño que normalmente se responde tarde y cara: **¿cuán bueno
tiene que ser el modelo de visión para que esto sirva?**

| Error del modelo | Acierto en las primeras 50 | Se abstiene |
|---|---|---|
| 0% (modelo perfecto) | 96% | 0% |
| 10% | **82%** | 34% |
| 20% | **76%** | 55% |
| 50% (modelo casi inservible) | 40% | 87% |

**La propiedad que importa no es el número, es la forma de la curva:** a medida que el
modelo empeora, el sistema **no se vuelve confiadamente incorrecto — se abstiene más**. Lo
que llega al tope de la cola sigue siendo confiable; lo que no puede leer lo devuelve
pidiendo otra foto.

Un sistema que al empeorar empezara a inventar contradicciones sería peor que no tener
nada: haría perder viajes y confianza al mismo tiempo. Incluso con un modelo que se
equivoca en la mitad de los campos, lo que llega al tope sigue siendo **1,7× mejor que el
azar** — simplemente llega mucho menos.

### Bloque 7 — Lo que falta y qué costaría

Sin adornos:

- **No hay fotos todavía.** El próximo paso es un conjunto de prueba de 100-150 imágenes.
- **La capa de percepción está simulada.** El adaptador al modelo real está escrito y sin
  ejercitar.
- **Costo:** ~US$0,02 por foto. El conjunto de prueba completo sale unos **US$3**.
- Los supuestos del componente están **escritos y numerados** (`[V1]`–`[V10]`), cada uno con
  su costo si resulta falso. El peor caso de toda esa lista es que el beneficio sea menor:
  ninguno invalida el trabajo.

### Bloque 8 — Cierre

Lo que se está proponiendo no es un sistema que decida por el técnico. Es **extender la
verificación técnica a las obras que hoy nunca reciben una visita**, y que cada decisión que
tome el técnico —aprobar, observar o rechazar— quede registrada.

Y un efecto de segundo orden que conviene mencionar al final: **cada decisión del técnico es
una etiqueta**. Sin pedirle trabajo extra a nadie, en unos meses existe el conjunto de datos
etiquetado que hoy no existe.

---

## Slides de respaldo (después del cierre, solo para preguntas)

- La rúbrica completa de los 15 rubros con su evidencia observable.
- Los grados de respaldo: respaldado / sobre-reporte / sub-reporte / avance rechazado /
  retroceso sin explicación / sin respaldo / no determinable.
- El ciclo de rechazo y rehacer, y por qué obliga a que la monotonía sea condicional.
- La tabla de supuestos `[V#]` con el costo de cada uno.

---

## Datos verificados

Todos los números de arriba salen del dataset y del prototipo al **2026-08-28**. Antes de
generar la presentación, si el dataset se regeneró, volver a correr `python -m vision.demo`
y `python docs/generar_figuras.py` y actualizar las cifras.

| Dato | Valor | Fuente |
|---|---|---|
| Obras activas | 908 | `data/viviendas_sinteticas.csv` |
| Activas sin ninguna visita | 213 (23,5%) | cruce con `visitas.csv` |
| Tope de visitas por obra | 2 | regla del programa |
| Sobre-reporte en la población (baseline) | 23,6% | `vision.simulacion` |
| Acierto en las primeras 50, error 10% | 82% | `python -m vision.demo` |
| Cobertura fotográfica del AFO | 87% · 97% con protocolo | `docs/vision-afo.md` §3 |
| Costo por foto | ~US$0,02 | `docs/vision-afo.md` §10 |

> **Aviso obligatorio para quien genere el .pptx:** no inventar cifras ni redondear a
> números "más lindos". Si un dato no está en esta tabla, no va en la presentación.

---

## Referencias

- Diseño completo del componente: [vision-afo.md](vision-afo.md)
- Supuestos y postura: [supuestos-abiertos.md](supuestos-abiertos.md)
- Reglas de presentación: [guia-presentaciones.md](guia-presentaciones.md)
- Código: `vision/` · demo reproducible: `python -m vision.demo`
