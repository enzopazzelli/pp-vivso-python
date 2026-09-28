"""Sube un export y lo procesa con el mismo camino que la línea de comandos (Plan 1)."""
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, UploadFile

router = APIRouter()

# ~20 MB: de sobra para un reporte VISOC (Lugones, un reporte real, pesa 40 KB). Sin este tope, un
# archivo enorme se leería entero en memoria antes de hacer nada más (encontrado en la revisión final).
TAMANO_MAXIMO_BYTES = 20 * 1024 * 1024


def _nombre_seguro(nombre: str | None) -> str:
    """El nombre que manda el cliente no es confiable: una ruta absoluta o con `..` uniría con `Path`
    fuera de la carpeta temporal (path traversal). Acá se queda solo con el nombre de archivo final,
    sin ningún componente de carpeta ni unidad — `PureWindowsPath` porque este proyecto corre en
    Windows y entiende tanto `/` como `\\` como separador, a diferencia de `PurePosixPath`."""
    from pathlib import PureWindowsPath
    base = PureWindowsPath(nombre or "").name
    return base if base not in ("", ".", "..") else "archivo"


def _sanear_advertencias(advertencias: list[str]) -> list[str]:
    """`importar_archivo` (Plan 1) puede meter el texto crudo de una excepción de SQLAlchemy (sentencia,
    parámetros) en una advertencia cuando falla el mapeo — pensado para la consola local, donde quien lo
    ve ya tiene acceso al código y a la base. Por HTTP no: se recorta a un mensaje genérico."""
    prefijo = "Falló al guardar en el modelo: "
    return ["Falló al guardar en el modelo (ver la consola del servidor para el detalle)."
           if a.startswith(prefijo) else a for a in advertencias]


@router.post("/importar")
def importar(archivo: UploadFile) -> dict:
    # `def`, no `async def`: `migrar()`, la lectura del PDF y las escrituras en SQLite son todas
    # operaciones bloqueantes (encontrado en la revisión final) — como ruta síncrona, FastAPI la corre
    # sola en un thread pool y no traba el resto de los pedidos mientras dura una importación.
    import tempfile
    from pathlib import Path

    from sqlalchemy.orm import Session

    from datos.anonimizador import Anonimizador
    from datos.config import ConfiguracionFaltante, anon_secret
    from datos.importar import importar_archivo
    from datos.sesion import crear_engine, migrar, sembrar_catalogos

    try:
        anonimizador = Anonimizador(anon_secret())
    except ConfiguracionFaltante as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    contenido = archivo.file.read()
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise HTTPException(status_code=413,
                            detail=f"El archivo supera el máximo permitido ({TAMANO_MAXIMO_BYTES} bytes).")

    migrar()
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / _nombre_seguro(archivo.filename)
        ruta.write_bytes(contenido)
        engine = crear_engine()
        try:
            with Session(engine) as sesion:
                # Mismo camino que la CLI (`datos/importar.py::main`): sin sembrar catálogos, un
                # `Organizacion` con FK a `tipo_solicitante` (Plan 2) falla con `IntegrityError`.
                sembrar_catalogos(sesion)
                resultado = importar_archivo(ruta, sesion, anonimizador)
        finally:
            engine.dispose()

    cuerpo = asdict(resultado)
    cuerpo["advertencias"] = _sanear_advertencias(cuerpo["advertencias"])
    return cuerpo
