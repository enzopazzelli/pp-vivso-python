# Capa de datos propia

Importa los reportes que exporta VISOC (en PDF) a una base de datos propia del equipo, sin nombres de
personas, y controla cada reporte contra los totales que él mismo trae. Es la primera parte del pipeline:
**extraer, transformar (anonimizar y validar) y cargar**.

## Antes de empezar

1. Instalar las dependencias: `pip install -r requirements-datos.txt`.
2. Poner una clave de anonimización en el archivo `.env` (no se sube a git):
   `ANON_SECRET=` seguido de una clave larga. Sirve para que la misma persona reciba siempre el mismo
   nombre inventado. Si se cambia la clave, los nombres inventados cambian.

## Importar un reporte

Desde la carpeta `vivso-python/`:

    python -m datos.importar ruta/al/reporte.pdf

Reconoce solo qué reporte es. Los formatos que sabe leer hoy:

| Reporte | Qué trae |
| :--- | :--- |
| VISOC · Por Solicitante | Totales por organización: solicitudes, beneficiarios, activadas y fin de obra |
| VISOC · Viviendas Según Solicitante | Una fila por vivienda de un solicitante |

En «Por Solicitante» las tres consultas (solicitadas, activadas y finalizadas) se ven idénticas; el sistema
infiere cuál es por los datos. Si querés indicarlo: `--consulta activadas`.

## Qué significa cada estado de una importación

| Estado | Significado |
| :--- | :--- |
| `ok` | Se leyó, cerró con los totales del reporte y se guardó |
| `con_advertencias` | Se guardó, pero hay algo para revisar (por ejemplo, el total general que imprime VISOC no coincide, o hay números de expediente repetidos) |
| `rechazada` | Los totales no cierran. **No se guardó nada en el modelo**, pero las filas leídas quedan registradas |
| `sin_importador` | No se reconoció el formato. Se guarda solo su forma (sin texto) para poder escribir un importador |
| `duplicada` | Ese mismo archivo ya se había importado. Con `--forzar` se importa de nuevo |

## Estados de las viviendas

| Estado | Qué significa en los reportes de VISOC |
| :--- | :--- |
| Iniciada | Solicitada y todavía sin activar |
| Avanzada | Activada pero sin acta de finalización: el técnico certificó la obra y el área activó el expediente para que pueda emitir el acta (según lo explicó el área) |
| Finalizada | Avance de obra al 100 |
| Desaprobada | Marcada como DES en el reporte |

## Dónde quedan los datos

En `db/datos_reales.db`, un archivo aparte de los datos simulados. **No se sube a git.** Cada importación
queda registrada (archivo, fecha del reporte, resultado de la validación), y cada vivienda guarda un
historial: un reporte más viejo no pisa el estado que muestra uno más nuevo.

**Clave de las viviendas.** En los reportes reales algunos números de expediente aparecen en más de una fila,
así que el expediente solo no alcanza para identificar una vivienda. La clave (`num_exp`) es el expediente más
una huella del titular ya anonimizado (`2128915-2022#a1b2c3`); el número de expediente puro queda en la
columna `expediente`. Cuando se repite, el reporte se importa igual pero queda como `con_advertencias`.

## Datos personales

Los nombres de titulares se reemplazan por un nombre inventado **antes de guardar cualquier cosa**. Los
números de DNI no se guardan. Los nombres de organizaciones no son datos personales y se guardan reales.
El seudónimo conserva la identidad entre reportes (la misma persona, el mismo nombre inventado), así se
puede seguir un caso y modelar relaciones sin saber quién es.

- Si una falla de lectura ocurre, se guarda y se muestra solo el tipo de error, nunca su mensaje, porque
  podría traer texto del archivo con un nombre real.
- El **nombre del archivo** se guarda tal cual solo cuando el formato se reconoce (son exports del sistema).
  Si no se reconoce, se guarda únicamente la extensión. Igual conviene no ponerle nombres de personas a los
  archivos.

## Para confirmar con el área

- Un número de expediente **no debería repetirse**; en el ejemplo de Lugones 64 de 107 filas lo comparten
  (66 expedientes distintos). Puede ser un dato todavía sin registrar.
- Qué significa la marca `DES` de las viviendas desaprobadas.
- Si «Viviendas Según Solicitante» se puede pedir para todos los solicitantes y no solo uno.

## Indicadores

`datos/indicadores/` calcula, sobre cualquier `FuenteDeDatos`, los indicadores que hoy se pueden armar
con los reportes de VISOC:

| Indicador | Sale de |
| :--- | :--- |
| Viviendas por clasificación, tipo y dormitorios | «Viviendas Según Solicitante» |
| Terminadas y sin terminar, y por año | «Viviendas Según Solicitante» |
| Antigüedad de las solicitudes sin terminar | «Viviendas Según Solicitante» |
| Tasa de activación y de finalización por organización | «Por Solicitante» (parcial: solo para las organizaciones con datos en las 3 consultas) |
| Peso de cada tipo de solicitante | El pie de «Por Solicitante» (agregado, no por organización) |
| Tiempos del proceso (solicitud→activación, activación→fin de obra) | «Viviendas Según Solicitante» |

```python
from datos.fuentes.registro import obtener_fuente
from datos.indicadores.registro import calcular_todos

for indicador in calcular_todos(obtener_fuente()):
    print(indicador.codigo, indicador.capacidad, indicador.valor)
```

Cada indicador trae su `explicacion` y su `como_leerlo` en lenguaje llano, y su `capacidad`
("disponible", "parcial" o "no_disponible") con la fuente que se usó para calcularlo. Faltan por armar
los que dependen de GDE (reclamos, estado de pago) y de precios: esperan a los importadores del Plan 4.

## Fuentes intercambiables

El código de arriba (indicadores, interfaz, API) no lee la base directamente: pide datos a través de
`datos.fuentes.registro.obtener_fuente()`, que devuelve una de estas tres, siempre con la misma
estructura (`datos/fuentes/estructura.py`):

| Fuente | De dónde lee | Cuándo usarla |
| :--- | :--- | :--- |
| `propia` (por defecto) | `db/datos_reales.db` | Con los reportes ya importados |
| `simulada` | los CSV de PP2 (`data/`) | Para el tablero público, sin datos reales |
| `json_prueba` | `datos_prueba/ejemplo.json` | Para probar el sistema sin PDF ni base |

Se elige con la variable de entorno `FUENTE` (`propia`/`simulada`/`json_prueba`), o pasándole el nombre
directamente a `obtener_fuente("simulada")`.

Un dato que la fuente activa no tiene queda en `None`, no falta la columna. `fuente.capacidades()` dice
qué colecciones y qué campos están poblados, para que la interfaz explique qué falta en vez de mostrar
un espacio vacío sin explicación.

**Las páginas del tablero (`dashboard/`) y `etl/extract.py` todavía no leen de acá:** siguen con su
`data_loader.py` propio. Migrarlas es un plan aparte, porque es trabajo de integración por pantalla
(mejor verificado corriendo la app) y no de la capa de datos en sí.

## Migraciones del esquema

La línea de comandos aplica las migraciones sola (`alembic upgrade head`), así la base queda con su versión
registrada. Cuando el esquema cambie, se agrega una migración en `db/migraciones/versions/` con
`alembic revision --autogenerate -m "descripción"`. Una prueba avisa si los modelos y las migraciones se
desalinean.

## Pruebas

    python -m pytest

Las pruebas usan datos inventados. Las que usan los archivos reales del área se saltan solas si esos
archivos no están en la máquina.
