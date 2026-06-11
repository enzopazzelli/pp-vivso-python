# Guía para presentaciones, guiones y código
### Lecciones de la devolución del Hito 2 — de cumplimiento obligatorio en adelante

**Para:** todo el equipo (Pablo · Sara · Valeria · Santiago · Enzo)
**Aplica a:** Hito 3 y cualquier presentación, guion o código futuro del proyecto.

---

## Por qué existe este documento

La devolución del profesor sobre el Hito 2 marcó tres problemas que no se pueden repetir:

1. **La presentación fue demasiado técnica.** Mostramos métodos, recursos y código cuando había que mostrar tablas de ejemplo, KPIs accionables y contrastes de antes/después. El profesor insistió en el recurso **"As is → To be"** y en cuantificar la ganancia de eficiencia de lo que implementamos.
2. **El guion se usó mal.** En lugar de servir para aprender a defender el trabajo, algunos lo estudiaron casi de memoria — y uno lo leyó como una computadora, sin lograr siquiera parecer enterado. El problema no fue el contenido del guion: fue tratarlo como libreto en vez de como mapa.
3. **Paso firme.** Tenemos que dar la impresión (verdadera) de que sabemos siempre lo que hacemos y por qué. Eso se logra entendiendo, no recitando.

---

## 1. Reglas para presentaciones

Estas reglas tienen prioridad sobre cualquier preferencia estética o técnica:

### 1.1 As is → To be en cada solución
Todo indicador o funcionalidad se presenta como **contraste**: cómo se hace HOY en el área (*as is*) vs. cómo queda con nuestra implementación (*to be*). Dos columnas o tabla con flecha. El método de cálculo va en una línea al pie o en slide de respaldo — **nunca en el cuerpo del mensaje**.

**Ejemplo del formato** (con nuestros propios indicadores — usar como modelo):

| Proceso del área | AS IS (hoy) | TO BE (con VIVSO) | Ganancia |
|---|---|---|---|
| Decidir qué obra visitar | El técnico elige entre cientos de expedientes a criterio propio | Lista priorizada por riesgo + tiempo + historial de la ONG, lista para terreno | De horas de revisión a minutos, sin sesgo |
| Detectar viviendas terminadas sin entregar | Nadie lo mide; se descubre cuando reclama la familia | Actas atascadas detectadas al instante, con días de espera visibles | Revisar ~1.500 expedientes a mano (~30 hs estimadas) → consulta de segundos |
| Evaluar a una ONG | Impresión subjetiva en reuniones | Índice 0–100 con semáforo: auditar / seguir / confiar | Decisión de auditoría defendible con datos |
| Leer el avance de una obra | "35% de avance" (número opaco) | "Trabada en mampostería, al 15% de esa etapa" | El ministerio sabe qué reclamarle a la gestora (la construcción es responsabilidad de la ONG) o qué trámite destrabar internamente |

### 1.2 Resultados antes que métodos
Mostrar **tablas de ejemplo con filas reales** (top 5 obras a visitar, ranking de ONGs, actas más atrasadas) y **KPIs con la decisión que habilitan**. Test rápido: si una slide responde "cómo lo hicimos" en vez de "qué cambia para el área", está mal enfocada.

### 1.3 Cuantificar la ganancia
Siempre que se pueda, **un número de eficiencia**: horas evitadas, casos detectados automáticamente, días de demora visibilizados. Si es una estimación, se aclara ("estimación ilustrativa") — pero el número tiene que estar. Un "ahora es más eficiente" sin número no dice nada.

### 1.4 Ser gráficos, no complicar
Un contraste visual simple vale más que un diagrama denso. **Un mensaje por slide.** Si hay que explicar la slide, la slide está mal.

### 1.5 Código casi cero
Máximo **una** slide con código en toda la presentación, y solo si la regla ES el mensaje (ej.: "el modelo de riesgo es una regla transparente, no una caja negra"). Todo lo demás en lenguaje natural. Fórmulas y métodos → slides de respaldo después del cierre, solo para responder preguntas.

---

## 2. Reglas para guiones

**El guion NO es un texto para recitar. Es un mapa para entender.** Quien lo memoriza o lo lee fracasa dos veces: pierde la naturalidad y demuestra que no se apropió del contenido.

### Cómo se escribe un guion a partir de ahora
- Cada bloque da la **idea fuerza** (una línea) y el **porqué** (2-3 puntos). Las palabras las pone cada uno en el momento.
- Las frases sugeridas que aparezcan entre comillas son **ejemplos de tono, no líneas de libreto**. Se reformulan siempre con palabras propias.
- El guion incluye las **preguntas probables con la lógica de la respuesta** (no la respuesta textual).

### Protocolo de preparación (esto reemplaza a "estudiar el guion")
1. Leé tu bloque **una vez**. Cerrá el documento.
2. **Explicale tu bloque a un compañero** como si fuera un amigo que no vio el proyecto. Sin mirar nada.
3. El compañero te hace 2-3 preguntas incómodas (las del guion u otras). Si te trabás, releé el *porqué* — no la frase.
4. Repetir hasta que salga natural. **El guion no viaja a la presentación.**

### La prueba de fuego
> ¿Podés explicar tu bloque en un bar, sin papeles, y responder "¿y por qué lo hicieron así?" sin recitar?

Si la respuesta es no, el problema no se arregla memorizando más — se arregla entendiendo mejor. Pedir ayuda al equipo está bien; leer en la presentación, no.

### Anti-patrones (lo que pasó en el Hito 2)
- ❌ Estudiar el guion de memoria → suena robótico y se nota.
- ❌ Leer el guion durante la presentación → peor todavía: parece que no estás enterado de tu propio trabajo.
- ❌ Llevar el guion impreso "por las dudas" → la tentación gana siempre.
- ✅ Entender el porqué de tu bloque y hablar mirando a la audiencia, con tus palabras.

---

## 3. Regla para el código (aplica a TODO el código del proyecto)

- **Sencillo y claro, no austero.** El código minimalista extremo ahorra líneas pero esconde intención. Preferimos algunas líneas más si el flujo se entiende solo.
- **Toda función o paso no obvio lleva un comentario que explique su propósito y/o porqué** — no qué hace línea por línea (eso se lee en el código), sino para qué existe y por qué se decidió así.
- Las interpretaciones y análisis van en celdas markdown (notebooks); los comentarios de código son para decisiones técnicas.
- Regla práctica: si un compañero abre el archivo en frío, tiene que poder seguir el hilo sin preguntarle a nadie. **Pasos firmes: siempre sabemos (y podemos mostrar) lo que hacemos.**

---

## Checklist antes de cualquier presentación futura

- [ ] ¿Cada solución tiene su As is → To be con número de ganancia?
- [ ] ¿Hay tablas de ejemplo con datos visibles (no solo fórmulas/diagramas)?
- [ ] ¿Hay como máximo 1 slide con código, y está justificada?
- [ ] ¿Cada presentador pasó el protocolo de preparación (explicó su bloque sin mirar)?
- [ ] ¿Nadie lleva el guion impreso?
- [ ] ¿Las slides de respaldo (fórmulas, métodos) están después del cierre?
