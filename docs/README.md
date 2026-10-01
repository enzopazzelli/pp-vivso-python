# Documentación

Índice de los documentos del componente de Ciencia de Datos de VIVSO. Cada carpeta reúne los
documentos de un mismo tema.

## Por dónde empezar

- **Si no conocés el proyecto:** el [README principal](../README.md) y después
  [analisis/documentacion-analisis.md](analisis/documentacion-analisis.md), que explica el porqué de
  cada análisis.
- **Si querés entender cómo trabaja hoy el programa:**
  [visoc/flujo-del-programa.md](visoc/flujo-del-programa.md).
- **Si sos del equipo de Desarrollo:** [para-desarrollo.md](para-desarrollo.md).

## Documentos

| Carpeta | Documento | Qué tiene |
| :--- | :--- | :--- |
| `docs/` | [para-desarrollo.md](para-desarrollo.md) | Guía de integración para el equipo de Desarrollo (Java): estado del backend, brechas del modelo de datos y pedidos pendientes |
| | [roadmap-pp3.md](roadmap-pp3.md) | Ruta de trabajo de PP3 y registro de las decisiones tomadas |
| `visoc/` | [flujo-del-programa.md](visoc/flujo-del-programa.md) | El flujo de trabajo del programa entre VISOC y GDE, graficado a partir del diagrama del área |
| | [modelo-de-datos.md](visoc/modelo-de-datos.md) | Qué guarda VISOC, según sus pantallas, y cómo lo ordenamos para analizarlo |
| | [datos-reales-visoc-pdf.md](visoc/datos-reales-visoc-pdf.md) | Qué traen los reportes en PDF de VISOC y qué adaptación necesita cada indicador |
| | `capturas/` | Capturas de VISOC usadas como evidencia, con los datos personales tapados |
| `capa-de-datos/` | [como-funciona-la-capa-de-datos.md](capa-de-datos/como-funciona-la-capa-de-datos.md) | Cómo funciona nuestra base de datos propia, explicado sin jerga |
| `analisis/` | [informe-eda.md](analisis/informe-eda.md) | Informe de análisis exploratorio de datos (entregable del Hito 3) |
| | [documentacion-analisis.md](analisis/documentacion-analisis.md) | El porqué de cada análisis y qué decisión habilita |
| | `figuras/` y `generar_figuras.py` | Las figuras del informe y el script que las vuelve a generar |
| `vision/` | [vision-afo.md](vision/vision-afo.md) | Diseño de la verificación del avance de obra con las fotos que adjunta la gestora |
| `pendientes/` | [datos-a-confirmar.md](pendientes/datos-a-confirmar.md) | Lista de supuestos para validar con el área |
| | [supuestos-abiertos.md](pendientes/supuestos-abiertos.md) | Todos los supuestos y consultas abiertas, ordenados, con cuáles se preguntan y cuáles no |
| `hito1/` | 3 diagramas | Proceso actual, integración con GEDO y arquitectura planteados en el Hito 1 |

## Carpetas del código

| Carpeta | Qué tiene |
| :--- | :--- |
| `dashboard/` | El tablero en Streamlit |
| `datos/` | La capa de datos propia: importadores, anonimizador, fuentes e indicadores. Su guía técnica está en [datos/README.md](../datos/README.md) |
| `db/` | El esquema de la base de datos y sus migraciones |
| `etl/` | La carga de datos desde la API de VIVSO o desde archivos CSV |
| `synthetic/` | El generador del conjunto de datos simulado |
| `data/` | Los CSV del conjunto de datos simulado |
| `datos_prueba/` | Un archivo mínimo para probar el sistema sin base de datos ni PDF |
| `colab/` | Los notebooks de análisis, pensados para Google Colab |
| `vision/` | La verificación por foto |
| `rutas/` | El armador de rutas para los viajes de los técnicos |
| `tests/` | Las pruebas automáticas |
