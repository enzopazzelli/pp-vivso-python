# Supuestos abiertos — punto de entrada único
## Componente de Ciencia de Datos · PP3 · ITSE

**Creado:** 2026-08-28

> Los supuestos y las consultas del proyecto estaban repartidos en cuatro documentos.
> Este archivo **no los copia**: los ordena y dice **cuáles se preguntan y cuáles no**.
> El detalle vive donde siempre estuvo — [datos-a-confirmar.md](datos-a-confirmar.md),
> [vision-afo.md](vision-afo.md), [para-desarrollo.md](para-desarrollo.md).
>
> **Regla de higiene:** toda pregunta o supuesto nace con un ID en su documento de origen
> (`[S#]` dataset · `[V#]` verificación fotográfica · `pedido #` a Desarrollo). Acá se lo
> referencia, nunca se lo transcribe. Si este archivo empieza a tener textos propios,
> volvimos al problema que vino a resolver.

---

## 1. La postura: construir primero, refinar después

**El componente de verificación fotográfica no se consulta antes de construirlo.** Es una
decisión deliberada del equipo, no un descuido, y conviene que esté escrita porque va a
parecer una omisión:

- **La obligación de PP3 ya está cubierta** por el dashboard y el Informe EDA. El componente
  de visión es **excedente, no alcance comprometido** — no hay riesgo de entrega en construirlo
  sobre supuestos.
- **Preguntar antes de que exista no es levantar información, es pedir permiso.** Ante un
  *"¿les serviría que el sistema…?"* lo más probable es que nos definan ellos la forma de
  trabajar sobre algo que todavía no vieron, o que digan que no — que es la respuesta más
  barata de dar frente a una idea abstracta.
- **Un prototipo andando cambia la conversación.** Reaccionar a algo concreto es mucho más
  fácil que imaginarlo. La corrección que buscamos sale mejor de *"esto no es así"* mirando
  una pantalla que de una pregunta en el aire.
- Y el proyecto **sigue** después de la nota. Esto se hace para seguir construyendo.

**La condición que hace sostenible la postura:** si se construye sobre supuestos, los supuestos
tienen que ser **baratos de cambiar**. Ninguno se hunde en la lógica: todos viven como constante
nombrada arriba del archivo, igual que los `[S#]` en `synthetic/generate.py`. Refinar tiene que
ser cambiar un valor y regenerar, nunca reescribir. **Si un supuesto no se puede cambiar en un
renglón, está mal implementado.**

---

## 1.b De dónde viene lo que damos por sabido

El diseño se apoya en reglas de dominio que **no tienen todas la misma fuerza**. Están escritas
como hecho plano en el código y en el Informe EDA —hedgear cada oración haría los documentos
ilegibles— así que la procedencia se registra acá, una sola vez.

| Regla de dominio | Fuente | Firmeza |
|---|---|---|
| Los 15 rubros del AFO, sus pesos y su orden | Capturas del sistema legacy (`afo.jpeg`, `tipos.jpeg`) | **Evidencia documental** |
| Plazo contractual de construcción: 90 días | Confirmado por el área, 2026-06-10 | **Confirmado** |
| El ministerio no construye; ejecuta la gestora | Conocimiento del equipo, de larga data | Firme, no ratificado |
| **La gestora solicita las viviendas, no al revés** (refuta `[S9]`) | Conocimiento del equipo, 2026-08-28 | Sin ratificar |
| **Cuatro tipos de gestora** (municipio · comisión municipal · ONG · cooperativa) | Conocimiento del equipo, 2026-08-28 | Sin ratificar |
| **Rubros 11 y 12:** mangueras vacías embutidas; el rubro certifica cables/tanque (`[V1]`) | Conocimiento del equipo, 2026-08-28 | Sin ratificar — **es lo que conviene revisar con alguien de obra** (§3) |
| **Ciclo de rechazo:** el técnico rechaza y la gestora rehace | Conocimiento del equipo, 2026-08-28 | Sin ratificar |
| Ciclo de actas: `Finalizada` → acta → `Adjudicada` | Conocimiento del equipo | Sin ratificar |
| **La unidad de análisis es la solicitud** —el seguimiento de cómo se hacen las viviendas— y la gestora se sigue de ella. Ambas importan | Conocimiento del equipo, 2026-08-28 | Sin ratificar — **no modelado todavía** |
| Desarrollo trabaja en una **capa intermedia entre solicitud y aprobación**, donde quedan las no aprobadas | Conocimiento del equipo, 2026-08-28 | Sin ratificar |

> Todas las filas "sin ratificar" vienen de lo que el equipo conoce del área por trabajar con
> ella. Es buen conocimiento y probablemente sea correcto — pero **no es lo mismo que
> validado**, y la diferencia importa en la presentación: si algo enunciado como hecho recibe
> un *"no es así"*, arrastra la credibilidad del resto. Enunciado como entendimiento del
> equipo, la misma corrección es una refinación normal.

### Y una categoría que no es conocimiento

**Los dos canales de resolución (app / presencial) no describen cómo trabaja el área hoy:
describen cómo queremos que trabaje.** La app de carga no existe —está fuera de alcance en
[vision-afo.md](vision-afo.md) §9— y el registro de rechazos es el pedido 7 a Desarrollo.

Eso reencuadra `[V9]` y `[V10]`: no son preguntas sobre la práctica actual sino sobre **qué
aceptarían en un sistema que todavía no existe**. Nadie puede opinar sobre la validez formal
de una aprobación remota antes de haber visto una funcionando. Acá construir y mostrar no es
una táctica para evitar que nos condicionen — **es la única forma de obtener la respuesta.**

---

## 2. Supuestos de diseño del componente de visión — no se preguntan

Cada uno tiene un valor por defecto y un costo conocido si resulta falso. Detalle en
[vision-afo.md](vision-afo.md) §11.

| ID | Supuesto | Valor por defecto | Si resulta falso |
|---|---|---|---|
| `[V6]` | ¿El plazo de 90 días se extiende tras un rechazo? | **Sí se extiende** | Nada. El diseño ya está hecho para no depender de la respuesta (§4.4): la corrección que importa —separar `paralizada` de `rehaciendo`— sirve igual |
| `[V7]` | ¿El rechazo queda registrado hoy en algún lado? | **No existe registro** — lo modelamos nosotros en `cd_` | Si ya existe, mejor: se conecta en vez de crearse. Es menos trabajo, no más |
| `[V9]` | ¿El tope de 2 visitas aplica a las resoluciones por app? | **No aplica** (el tope es logística de campo) | El sistema vuelve a ser triage. **Mismo código, menos beneficio** — no se cae, se achica |
| `[V10]` | ¿Una aprobación remota certifica el AFO? | **Sí certifica** | Igual que `[V9]`. El demo puede mostrar los dos escenarios sin cambiar nada |
| `[V5]` | Tolerancia de ±1 rubro | **Aceptable** | Es un umbral: se cambia en un renglón |
| `[V2]` | El rubro 15 (Varios) no tiene evidencia visible propia | **No la tiene** | Sube la cobertura fotográfica del 87% al 90%. A favor nuestro |
| `[V8]` | Frecuencia de rechazo y rehacer | **Desconocida** — el ciclo se implementa igual | Si es marginal, es un caso borde bien resuelto. Si es frecuente, el indicador de calidad vale más de lo que creíamos |

> Ninguna de estas filas bloquea nada. El peor caso de toda la columna derecha es que el
> beneficio sea menor al esperado — **ninguna vuelve inútil el trabajo**.

### 2.b Supuestos del generador de rutas — mismo criterio

Detalle en `rutas/parametros.py`.

| ID | Supuesto | Valor por defecto | Si resulta falso |
|---|---|---|---|
| `[R1]` | Velocidad promedio de viaje | **55 km/h** (ruta provincial + tramos de tierra) | Es un factor de escala: cambia horas y "días completos", no la lógica de la ruta |
| `[R2]` | No hay red vial real — la distancia se aproxima con línea recta × un factor | **Factor 1,35** | Mismo caso: reescala km y horas, no cambia qué ruta se arma |
| `[R8]` | Base del técnico | **Confirmado 2026-08-29: siempre Santiago Capital**, sede del ministerio — no la cabecera de su zona de cobertura, que era el supuesto inicial | Ya no es un supuesto sin validar; corregido en `base_tecnico()` |

> Estos tres son parámetros de escala, no de diseño: si están mal calibrados, los viajes
> que arma el sistema siguen siendo los mismos, con horas y kilómetros distintos. Ninguno
> cambia CUÁLES obras entran en un viaje.

---

## 3. Lo único que sí conviene chequear del diseño

**No es con el área, y no es pedir permiso.**

**La rúbrica constructiva** ([vision-afo.md](vision-afo.md) §3): qué se ve en una foto de cada
uno de los 15 rubros, y en particular `[V1]` (las mangueras embutidas) y las dos ventanas
temporales. Equivocarse acá no es un supuesto discutible: es un **error de obra**, y hace que
el demo se caiga solo delante de cualquiera que haya pisado una construcción.

Lo puede validar cualquiera que sepa de construcción — un profesor, alguien del rubro, un
conocido, un técnico. **No hace falta que sea del área**, y por eso no le impone nada al
proyecto.

**Las fotos** (`[V3]`, `[V4]`) tampoco se piden como requisito. El gold set arranca con
imágenes públicas de construcción de vivienda social; si más adelante aparecen fotos reales,
el trabajo mejora. No es una condición de arranque.

---

## 4. Lo que sí es del ámbito de la práctica

Esto no es diseño del sistema, es gestión de la cursada. Acá preguntar no cuesta nada.

| A quién | Qué | Por qué sí |
|---|---|---|
| **Cátedra** | Fecha de la presentación final y si asiste alguien de la entidad | Ordena el cronograma de todo lo demás |
| **Cátedra** | ¿El componente de visión puede entrar como **prototipo evaluado** y no desplegado? | Define si la Fase 3 de §9 es obligatoria o línea futura |
| **Desarrollo** | **¿Siguen activos en el proyecto para PP3?** Una sola pregunta | Si la respuesta es no, se activa la contingencia de [roadmap-pp3.md](roadmap-pp3.md) §6 y no hay nada más que preguntarles |
| **Área** | El checklist `[S#]` de [datos-a-confirmar.md](datos-a-confirmar.md) | Son **parámetros del dataset**, no la forma de trabajar. Corregir un `[S#]` es editar una constante y regenerar |

> La distinción que ordena todo este documento: preguntar **parámetros** es levantar
> información; preguntar **si algo les serviría** es delegar la decisión de diseño.

---

## 5. Cómo se refina, después

1. Se construye el prototipo con los supuestos de §2 tal como están.
2. **Los supuestos se muestran en pantalla**, no se esconden — el dashboard ya lo hace con
   los `[S#]`, misma convención. Que se vea de qué se está partiendo es lo que habilita que
   alguien lo corrija.
3. Se demuestra funcionando. **El demo es la pregunta.**
4. Cada corrección que salga de esa reacción es cambiar un valor y regenerar.

Ese orden es también el mejor material para el entregable de PP3, que es una **presentación
profesional a la entidad**: convierte *"acá está el dashboard que ya vieron"* en *"y además,
miren esto"*.

---

## 6. Referencias

- Supuestos del dataset `[S#]`: [datos-a-confirmar.md](datos-a-confirmar.md)
- Supuestos de verificación fotográfica `[V#]`: [vision-afo.md](vision-afo.md) §11
- Pedidos a Desarrollo: [para-desarrollo.md](para-desarrollo.md) §4
- Bloqueantes y contingencia: [roadmap-pp3.md](roadmap-pp3.md) §3 y §6
