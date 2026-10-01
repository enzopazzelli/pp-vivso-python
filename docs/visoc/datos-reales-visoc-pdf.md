# Datos reales de VISOC en PDF: qué implica para PP3
### Componente de Ciencia de Datos · PP3 · ITSE

**Creado:** 2026-09-23
**Para qué sirve:** dejar por escrito qué datos reales recibimos, en qué se diferencian de los
simulados que usamos en PP2, qué adaptaciones haría falta hacer según lo que exporta el sistema, y
qué caminos tenemos para leer los datos, incluido Power BI. Alimenta la Etapa 6 (Evaluación) y sobre
todo la Etapa 8 (Despliegue), que pide registrar las limitaciones de implementación.

---

## 1. La situación en pocas líneas

En PP2 trabajamos con archivos CSV simulados (semillas), armados con la estructura del reporte de
VISOC que vimos en PP1. Era una decisión razonable mientras no había datos reales.

Cuando el área nos compartió datos reales apareció otra realidad:

- **VISOC no exporta datos: exporta reportes en PDF**, con un formato de tabla distinto según la
  consulta.
- **Llegar a la base de datos de VISOC es complicado**, así que hoy los PDF son el camino práctico.
- Los exports que recibimos son **específicos, preparados por el área para el informe que nos pidió**.
  Son agregados por organización (VISOC) o por expediente (GDE), no por vivienda.

El prototipo de PP2 se pensó para datos por vivienda. Eso **no lo invalida**: pide **adaptarlo** al
nivel de detalle que da cada export, o pedir el export que le falta. La sección 4 detalla, indicador
por indicador, qué adaptación permite el export actual y qué export adicional lo habilitaría.

## 2. Qué recibimos exactamente

| Fuente | Formato | Una fila es... | Qué trae | Qué no incluye este export |
| :--- | :--- | :--- | :--- | :--- |
| GDE: solicitudes de inclusión | Excel | un expediente | Número, fecha, estado, "Motivo" y "Motivo Pase" en texto libre | Tipo de solicitante, organización, departamento y tipo de vivienda como columnas: se deducen del texto. El texto mezcla nombres y DNI de familias |
| GDE: reclamos | Excel | un reclamo | Igual que el anterior | Número de expediente en común con las solicitudes |
| Listado de Orden de Pago | Excel | un expediente | Los expedientes con OP confirmada por el área | — |
| VISOC: "Por Solicitante" (3 reportes) | **PDF**, 12 páginas cada uno | una **organización** | Cuatro números: Solicitudes, Beneficiarios, Activadas, Fin Obras. Al pie, 4 categorías y un total | Fechas, expedientes, viviendas, avance de obra, ubicación |
| Precios (2 archivos) | **PDF**, 4 páginas | una ficha de precio | Precio por tipo de vivienda y quién la pide | No es una tabla: son bloques "concepto / monto" |

Detalle importante de los reportes de VISOC: los tres tienen el mismo diseño, pero **son tres
consultas independientes**, cada una con su propio período y criterio. No son un único export con
filtros. En la primera página, la lectura automática no detecta ninguna tabla con bordes: el diseño
es texto alineado en columnas.

## 3. Lo simulado (PP2) frente a lo real

| | PP2 (simulado) | Exports que tenemos (reales) |
| :--- | :--- | :--- |
| Unidad | La **vivienda** (1.500 a 5.000) | El expediente (GDE) o la **organización** (VISOC) |
| Formato | CSV limpios, generados por nosotros | Excel con texto libre y PDF |
| Avance de obra (AFO) | Sí, por rubro (15 rubros por obra) | No incluido |
| Fechas de inicio y fin | Sí, por vivienda | La fecha del expediente en GDE |
| Visitas de técnicos | Sí | No incluido |
| Ubicación | Coordenadas y departamento | Departamento deducido del texto (708 de 1.003 con dato) |
| Tipo de solicitante | Un campo | Se deduce del texto o del pie de VISOC |
| Datos personales | Ninguno | Sí, dentro del texto libre de GDE |

## 4. Qué se hizo, y qué más se podría hacer

### Lo que se hizo: el informe OG/ONG

Es un trabajo **a pedido del área, con exports específicos que ella preparó** (carpeta
`informe_ong_og_2026/`). Con esos exports se pudo:

- contar las solicitudes de inclusión por tipo de solicitante (gobiernos locales y ONG);
- seguirlas por estado de pago: con Orden de Pago, en Economía, en trámite;
- comparar contra lo que informa VISOC (solicitadas, activadas, finalizadas);
- estimar montos con los precios vigentes, antes y después del cambio del 1/8/2026;
- ver reclamos por institución y las solicitudes marcadas como primera vivienda.

Y con **más exports** se podría hacer **mucho más**. El flujo (leer, limpiar, validar y publicar)
ya está armado: cada export nuevo necesita su propio lector, pero se suma sin rehacer lo anterior.

### Adaptaciones del prototipo de PP2 según el export

El prototipo de PP2 calcula sus indicadores por vivienda. Esto es lo que habría que adaptar, o qué
export lo habilitaría tal cual está:

| Indicador de PP2 | Qué necesita | Adaptación posible con los exports actuales | Export adicional que lo habilita |
| :--- | :--- | :--- | :--- |
| Riesgo por plazo (obra activa con más de 90 días y poco avance) | Fecha de inicio y avance por vivienda | A nivel expediente: antigüedad desde la fecha del expediente en GDE, por estado de pago | Pases de GDE con fecha (desde cuándo tiene Orden de Pago) y avance de obra por vivienda |
| Cuello de botella constructivo (etapa activa por rubro) | Avance en cada uno de los 15 rubros del AFO | No hay equivalente a nivel organización | Historial por vivienda de VISOC con avance por rubro |
| Actas atascadas (obra terminada sin acta) | Fecha de fin de obra y de acta por vivienda | Aproximar por organización, comparando Activadas y Fin Obras (con la salvedad del punto 26 de `DECISIONES.md`) | VISOC con fecha de fin de obra y de acta por vivienda |
| Confiabilidad de gestoras (avance, riesgo, sobre-reporte) | Avance informado por la gestora contra el verificado por el técnico | Reemplazar el componente de sobre-reporte por indicadores por organización: tasa de activación, tasa de finalización, reclamos. Es una propuesta a validar con el área | Visitas técnicas con avance verificado, y el avance que reporta cada gestora |
| Priorización de visitas y rutas | Ubicación y estado de cada vivienda, técnico asignado | A nivel departamento (deducido del texto) | Tabla de códigos de zona, coordenadas de AppGPS, asignación de técnicos |
| Mapa provincial | Coordenadas por vivienda | Mapa por departamento | Coordenadas de AppGPS |

**Ya se pueden calcular hoy**, con los exports actuales, **indicadores por organización**: tasa de
activación y de finalización, beneficiarios por solicitud, reclamos por organización y peso de cada
tipo de solicitante. Sirven para decidir a qué organizaciones hacer seguimiento.

Un caso que el área ya se ofreció a intentar: filtrar los **pases de cada expediente en GDE, con
fecha**. Con ese export se armaría el embudo real con tiempos (solicitud, Orden de Pago,
activación, acta), un análisis que los exports actuales no incluyen y que ese habilitaría.

## 5. Qué tan bien se leen hoy los PDF de VISOC

Se midió con `informe_ong_og_2026/validar_pdf_visoc.py`, que compara lo que se lee fila por fila
con lo que el propio PDF imprime al pie.

| Reporte | Filas de organización leídas | Solicitudes | Beneficiarios | Activadas | Fin Obras | Cierra con el pie |
| :--- | ---: | ---: | ---: | ---: | ---: | :---: |
| Solicitadas | 715 | 1.109 | 3.461 | 162 | 140 | Sí |
| Activadas | 704 | 1.097 | 3.454 | 1.097 | 886 | Sí |
| Finalizadas | 685 | 1.011 | 3.338 | 1.011 | 1.011 | Sí |

- **Cobertura de la lectura: 100 %** en las cuatro columnas de los tres reportes; ninguna línea
  quedó sin clasificar.
- La regla que deduce si una organización es OG u ONG difiere de la categoría oficial de VISOC en
  **4 solicitudes por reporte** (menos del 0,4 %).

Estas cifras son la **vara de comparación para cualquier camino**: si se prueba otro lector, tiene
que reproducir exactamente estos números.

Lo que esta medición no dice: que los números signifiquen lo que creemos. Los pies de VISOC tienen
inconsistencias sin explicar (punto 26 de `informe_ong_og_2026/DECISIONES.md`). Y vale para este
diseño de PDF; otro reporte necesitaría su propio lector, que se puede armar con el mismo patrón
(leer, validar contra el pie o el total, dejar tablas planas).

## 6. Los caminos posibles

### Camino A: lector propio en Python (el que existe hoy)

`pdfplumber` extrae el texto, una regla lo convierte en filas, y los datos limpios quedan en tablas
planas (CSV, Excel o las tablas `cd_*` planeadas). Las reglas de negocio (OG/ONG, exclusiones,
baldes, montos) viven en un solo lugar, versionadas.

- **A favor:** ya funciona y está medido. Reproducible: el mismo PDF da siempre el mismo resultado.
  Las reglas están documentadas fecha por fecha en `DECISIONES.md`.
- **A tener en cuenta:** cada formato nuevo de PDF necesita su propio lector, y un cambio de diseño
  de VISOC obliga a ajustarlo. Alguien tiene que saber Python para mantenerlo y correrlo.

### Camino B: Power BI leyendo los PDF directamente

Power BI Desktop tiene un conector de PDF (Obtener datos → Archivo → PDF; en Power Query es la
función `Pdf.Tables`) que detecta tablas por página. La idea es que el área no dependa de código.

- **A favor:** herramienta conocida en el ámbito de gestión, sin código para leer. Visuales
  interactivos y actualización sin pasar por Python.
- **A tener en cuenta:** ver la sección 7. Además, las reglas de negocio que hoy están en Python
  (clasificar solicitante, baldes, exclusiones) habría que **reescribirlas en Power Query o DAX**,
  con el riesgo de que las dos versiones se separen con el tiempo.

### Camino C: híbrido

Python (o Power Query) deja los datos limpios en tablas planas y **Power BI solo las visualiza**.
Las reglas quedan en un solo lugar y el área tiene su tablero. Es el que mejor combina los dos, a
costa de tener dos herramientas en juego.

## 7. Power BI: qué sabemos y qué falta comprobar

Se deja el camino disponible. **No lo probamos**: no tenemos Power BI en esta máquina. Lo que sigue
son hipótesis a validar, no afirmaciones.

**Lo que probablemente funcione:** los PDF de VISOC tienen texto seleccionable (no son imágenes
escaneadas), que es la condición para que el conector pueda leerlos.

**Lo que hay que comprobar con nuestros archivos:**

1. Si el conector reconoce como tabla un diseño sin bordes, como el de los reportes "Por
   Solicitante".
2. Si las filas del pie (COOPERATIVA, ASOCIACION/ONG, COMISIONADO, INTENDENCIA, TOTAL GRAL) y la
   línea "Pagina:12" llegan mezcladas con las organizaciones.
3. Si las 12 páginas se unen solas o hay que juntarlas a mano.
4. Si los nombres con paréntesis, puntos o números (por ejemplo "(M.N.72458)") llegan enteros.
5. Cómo se actualiza cuando llegue un PDF nuevo: si hay que repetir pasos a mano cada vez.
6. Qué hace falta para compartirlo con el área (licencias, dónde se aloja, quién lo mantiene). Para
   actualizar en el servicio con archivos locales suele hacer falta un componente intermedio o
   alojar los archivos en la nube; hay que confirmarlo con la licencia real que tengan.

### Prueba de concepto (una hora, aproximadamente)

1. Abrir Power BI Desktop → Obtener datos → PDF → `visoc_finalizadas_por_solicitante.pdf`.
2. Mirar qué ofrece el navegador: cuántas tablas detecta y cómo se llaman.
3. Cargar y, si hace falta, juntar las páginas. Anotar cuántos pasos manuales requirió.
4. Comparar contra la vara de la sección 5, una vez sacadas las filas del pie: **685 filas de
   organización**, con **1.011** en Solicitudes y **3.338** en Beneficiarios.
5. Repetir con los reportes de Solicitadas y Activadas.
6. Repetir con un PDF de precios para ver cómo trata un diseño que no es una tabla.

**Cómo decidir:** si Power BI reproduce las cifras de control **sin pasos manuales por página**,
sirve como lector y el Camino B o C es viable. Si no, se sigue con el Camino A y Power BI queda
para visualizar (Camino C).

**Precaución:** hacer la prueba **solo con los PDF de VISOC**, que son agregados por organización.
No usar los Excel de GDE, que traen DNI y nombres de familias, salvo que estén anonimizados. Un
archivo de Power BI (`.pbix`) guarda una copia de los datos que carga.

## 8. Cómo decidir y qué proponemos

Criterios: que las reglas queden en un solo lugar; que un cambio de formato se detecte solo (por
eso existe el control contra el pie); que el área pueda mantenerlo sin nosotros; y que se cuiden
los datos personales.

**Propuesta de trabajo:**

1. Mantener el **Camino A** como base, porque está medido y documentado.
2. Hacer la **prueba de concepto de Power BI** para no descartarlo sin evidencia.
3. Tener el **Camino C** como forma probable de entrega si el área quiere un tablero propio.
4. Que la decisión final se tome en la Etapa 8, con lo que el área tenga realmente (licencias,
   equipos, quién lo va a correr).

## 9. Preguntas para el área sobre acceso a los datos

1. ¿VISOC puede exportar a Excel o CSV desde alguna pantalla? Hoy todo sale en PDF.
2. ¿Qué haría falta para tener acceso de solo lectura a la base de VISOC? ¿Por qué es complicado:
   permisos, el motor de base de datos, un tercero que lo administra?
3. ¿Quién genera los reportes, con qué frecuencia, y se puede acordar un nombre y un período fijos?
4. ¿Existe algún reporte por vivienda (con fechas y avance de obra)? El intento del 02/09 se trabó.
5. ¿Se pueden exportar los pases de cada expediente en GDE con fecha?
6. ¿Tienen licencias de Power BI, o trabajan con Excel?
7. ¿Pueden entregarnos los datos anonimizados desde el origen?

## 10. Riesgos de este enfoque

| Riesgo | Efecto | Qué lo mitiga |
| :--- | :--- | :--- |
| VISOC cambia el diseño del reporte | La lectura falla o, peor, lee mal | El control contra el pie lo detecta: si no cierra, se frena |
| Los reportes significan otra cosa de lo que suponemos | Conclusiones equivocadas | Registrar las dudas (punto 26) y confirmarlas con el área |
| Actualización manual cada mes | El dato queda viejo | Definir en la Etapa 8 quién corre el proceso y cada cuánto |
| Datos personales en el texto de GDE | Riesgo de exposición | `.gitignore`, copia pública depurada, y anonimización desde el origen (pendiente) |
