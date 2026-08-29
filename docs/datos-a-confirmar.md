# Datos a confirmar con el responsable del área

**Reunión:** validación del modelo con la Subsecretaría de Promoción Humana
**Fecha:** ______________  **Participantes:** ______________________________

> El dashboard y el análisis se construyeron sobre un **dataset sintético** (el backend real
> todavía no tiene datos cargados). Para que las conclusiones sean defendibles, necesitamos que
> el área confirme o corrija los **supuestos** con los que modelamos el programa.
>
> Este documento se completa en la reunión. Cada fila tiene un código **[S#]** que indica qué
> parámetro editar después en `synthetic/generate.py` (todos están centralizados en el bloque
> *"SUPUESTOS DEL PROGRAMA — A VALIDAR CON EL ÁREA"*). No hace falta tocar nada más: se cambia
> el valor, se regenera y todo el sistema se actualiza solo.

**Cómo completar:** marcar **✓** si el valor es correcto o **✗** si no, y en ese caso anotar el
valor real en *"Corregir a"*. Si no se sabe en el momento, marcar *"Averiguar"*.

> 💡 **En la demo:** cada indicador del dashboard tiene un desplegable **"ℹ️ Cómo se calcula /
> criterio"** que muestra el criterio usado y su etiqueta **[S#]**. Conviene abrirlo frente al
> responsable para que vea, indicador por indicador, qué se puede ajustar — y anotarlo acá.

---

## 1. Volumen y alcance del programa

Preguntas estructurales (no son parámetros sueltos: definen el tamaño del modelo).

| Pregunta | Lo que asumimos | ¿Correcto? | Valor real |
|---|---|:--:|---|
| ¿Cuántas viviendas tiene el programa activo hoy? | 1.500 | ☐ | __________ |
| ¿En cuántos departamentos hay obras? | 18 | ☐ | __________ |
| ¿Cuántas organizaciones gestoras hay, y de qué tipo? | 8: 2 municipios · 2 comisiones municipales · 2 ONGs · 2 cooperativas | ☐ | __________ |
| ¿Cuántos técnicos de campo hay? | 6 | ☐ | __________ |
| ¿Cuál es el máximo de visitas técnicas por obra? | 2 (primera y segunda) | ☐ | __________ |

---

## 2. Cómo se reparte el padrón de viviendas

| Cód | Supuesto | Valor que usamos | ¿Correcto? | Corregir a |
|---|---|---|:--:|---|
| **[S2]** | Distribución por **estado** | Iniciada 18% · Avanzada 17% · Finalizada 38% · Adjudicada 27% (terminadas 65%) | ☐ | __________ |
| **[S12]** | Distribución por **tipo** | Urbana 55% · Rural 38% · Económica 7% | ☐ | __________ |
| **[S12]** | **Dormitorios** | 2 dorm. 60% · 3 dorm. 25% · 1 dorm. 15% | ☐ | __________ |
| **[S13]** | **Clasificaciones** más frecuentes | 2a (Precaria) 24% · 1a (Rancho) 18% · 2b (derrumbe) 12% | ☐ | __________ |
| **[S15]** | Concentración **geográfica** | Capital 22% · Banda 16% · resto repartido | ☐ | __________ |
| **[S17]** | **Dispersión** dentro de cada departamento | ~5 km en Capital/Banda hasta ~16 km en los rurales de menor peso, antes de aplicar [S18] | ☐ | __________ |
| **[S18]** | Las obras de **riesgo alto** están más lejos de la cabecera ("monte adentro") que las de riesgo bajo | Riesgo alto ~3× más lejos que riesgo bajo (17,2 km vs. 5,5 km promedio) | ☐ | __________ |

> ¿Hay departamentos con muchas más obras de las que asumimos? ¿Alguna clasificación que
> domine y no estemos reflejando? ¿Las viviendas de un departamento rural se concentran
> cerca de la cabecera o realmente se reparten por el territorio? ¿Es cierto que las obras
> más atrasadas están más alejadas y de acceso más difícil? Anotar: _____________________

---

## 3. Plazos y tiempos de obra

| Cód | Supuesto | Valor que usamos | ¿Correcto? | Corregir a |
|---|---|---|:--:|---|
| **[S1]** | **Plazo contractual** de construcción | **90 días** | ☐ | __________ |
| **[S4]** | De las obras activas, cuántas están **dentro de plazo** | 35% (el 65% ya venció) | ☐ | __________ |
| **[S5]** | **Duración real** de una obra terminada | entre 60 y 300 días (media ~167) | ☐ | __________ |

> El hallazgo principal del informe es que **el 85% de las obras terminadas supera los 90 días**.
> ¿El área coincide con que el atraso es estructural, o es un efecto del dato sintético?
> Anotar: ______________________________________________________________________________

---

## 4. Modelo de riesgo

Definición que usamos: una obra **activa que pasó los 90 días** se marca en riesgo según su avance.

| Cód | Supuesto | Valor que usamos | ¿Correcto? | Corregir a |
|---|---|---|:--:|---|
| **[S6]** | Umbral de **riesgo medio** | vencida con avance **< 80%** | ☐ | __________ |
| **[S6]** | Umbral de **riesgo alto** | vencida con avance **< 30%** | ☐ | __________ |

> ¿La regla tiene sentido para el área? ¿Usarían otro corte (p. ej. alto si avance < 25%)?
> ¿Una obra vencida con 85% de avance debería seguir contando como "sin riesgo"?
> Anotar: ______________________________________________________________________________

---

## 5. Cuello de botella constructivo  ⭐ (el supuesto más importante a validar)

Modelamos que las obras en riesgo se **traban en las etapas estructurales** (mampostería). El
informe concluye que el cuello de botella está en *"Mampostería hasta dintel"* (184 obras). **Si
esto no es así en la realidad, es lo que más cambia el relato.**

| Cód | Supuesto | Etapas que usamos | ¿Correcto? | Corregir a |
|---|---|---|:--:|---|
| **[S7]** | Etapas **estructurales** (bloqueo típico de riesgo alto) | 3 Mamp. hasta dintel · 4 Mamp. Block · 5 Encadenado | ☐ | __________ |
| **[S7]** | Etapas de **terminaciones** | 6–7 Revoques · 8–9 Cielorrasos | ☐ | __________ |
| **[S7]** | Etapas de **instalaciones** (dependen de aprobación municipal) | 10 Carpintería · 11 Agua · 12 Eléctrica · 13 Sanitaria | ☐ | __________ |

> **Preguntas clave para el área:**
> - ¿En qué etapa se traban más seguido las obras en la realidad? __________________________
> - ¿Hay una etapa que dependa de un trámite externo (municipio, EPE) y frene todo? _________
> - Los **pesos de cada rubro** en el AFO (`[S14]`, catálogo en `db/setup.py`, ref. `docs/afo.jpeg`) — ¿siguen vigentes? ☐

---

## 6. Control técnico y gestión de las organizaciones gestoras

| Cód | Supuesto | Valor que usamos | ¿Correcto? | Corregir a |
|---|---|---|:--:|---|
| **[S8]** | **Sobre-reporte** de la gestora vs. lo que verifica el técnico | de −8 a +15 puntos (media +3) | ☐ | __________ |
| **[S16]** | **Distribución por tipo de gestora** | reparto parejo (~25% c/u) entre municipios, comisiones municipales, ONGs y cooperativas | ☐ | __________ |
| **[S10]** | Obras finalizadas con el **acta atascada** | 45% | ☐ | __________ |
| **[S11]** | **Cobertura de visitas** por técnico | entre 40% y 90% según el técnico | ☐ | __________ |

> **[S9] — REFUTADO (2026-08-28).** Asumíamos que un **20% de las obras no tenía gestora
> asignada**. Es imposible: la gestora (municipio, comisión municipal, ONG o cooperativa)
> es quien **solicita** las viviendas, no al revés, así que toda obra tiene una por
> construcción. Confirmado por el equipo, **a ratificar con el área**. El generador ya no
> produce obras sin gestora. Este supuesto estaba marcado como no confirmado desde el
> principio — el mecanismo funcionó como tenía que funcionar.

> **Además de los `[S#]`, hay reglas de dominio sin ratificar.** Los cuatro tipos de gestora,
> qué certifican los rubros 11 y 12, el ciclo de rechazo y el de actas están hoy escritos como
> hecho en el código y en el informe, pero vienen del conocimiento del equipo y no de una
> confirmación del área. Están listadas una por una en
> [supuestos-abiertos.md](supuestos-abiertos.md) §1.b — **si hay reunión, ratificarlas vale
> más que corregir cualquier `[S#]`**: un `[S#]` mal calibrado mueve un número, una regla de
> dominio equivocada invalida un análisis entero.

> - ¿Es real que las gestoras tienden a reportar de más? ¿Conocen casos? __________________
> - ¿Los cuatro tipos de gestora se comportan distinto (avance, actas, sobre-reporte)? ____
> - ¿El trámite del acta de finalización es igual para un municipio que para una ONG? _____
> - ¿El acta de finalización se demora tanto? ¿Quién la tramita? __________________________

---

## 7. Preguntas abiertas (no son parámetros, son del dominio)

1. **Palanca ante un cuello constructivo:** asumimos que el ministerio **reclama/sigue a la
   organización gestora** (no manda cuadrillas propias). ¿Es correcto? ____________________
2. **Acta de finalización:** ¿se destraba desde el ministerio? ¿Qué oficina interviene? ____
3. **Datos reales:** ¿existe un padrón/planilla que podamos usar para reemplazar el sintético?
   ¿En qué formato (Excel, sistema, papel)? __________________________________________
4. **Visitas:** ¿el técnico registra el avance verificado en algún lado hoy? ¿Dónde? ________
5. Otros comentarios del área: ____________________________________________________________

---

## Después de la reunión — cómo aplicar los cambios

1. Por cada fila corregida, editar el parámetro **[S#]** en `synthetic/generate.py` (bloque
   *"SUPUESTOS DEL PROGRAMA"*, al inicio del archivo).
2. Regenerar los datos: `python -m synthetic.generate`
3. Regenerar las figuras del informe: `python docs/generar_figuras.py`
4. Revisar en [informe-eda.md](informe-eda.md) los números citados en el texto (los que están en
   negrita) y actualizarlos si cambiaron.
5. Abrir el dashboard (`streamlit run dashboard/app.py`) para ver el resultado.

> Las preguntas estructurales de la sección 1 (cantidad de gestoras, técnicos, etc.) pueden requerir
> ajustes algo mayores en el generador; el resto son cambios de un solo valor.
