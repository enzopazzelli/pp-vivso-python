# Páginas ocultas del dashboard

Estas dos páginas **no se borraron, se movieron acá** para que Streamlit deje de listarlas en el
menú (Streamlit arma el menú escaneando todo lo que hay en `dashboard/pages/`, así que alcanza con
que el archivo no esté ahí — no hace falta borrar código).

| Página | Por qué se ocultó |
| :--- | :--- |
| `07_verificacion_foto.py` | Verificación por foto (percepción simulada, `vision/`) |
| `08_rutas.py` | Generador de rutas para técnicos — ya venía marcado como "componente extra, fuera de la obligación de PP3" |

Para volver a mostrar cualquiera de las dos, se la mueve de nuevo a `dashboard/pages/` (no hace
falta tocar el archivo: el código no cambió, solo la carpeta donde vive).
