"""El interruptor: elige la fuente de datos activa según la variable de entorno FUENTE."""
import os

from datos.fuentes.base import FuenteDeDatos

FUENTES_VALIDAS = ("propia", "simulada", "json_prueba")


def obtener_fuente(nombre: str | None = None) -> FuenteDeDatos:
    """La fuente pedida, o la de la variable de entorno FUENTE, o «propia» por defecto."""
    from dotenv import load_dotenv

    from datos.config import RAIZ
    from datos.fuentes.json_prueba import FuenteJSON
    from datos.fuentes.propia import FuentePropia
    from datos.fuentes.simulada import FuenteSimulada

    # No alcanza con que otro módulo ya haya cargado el .env antes en el proceso: si nadie lo hizo
    # todavía (por ejemplo, se llama a esto antes de abrir cualquier sesión), FUENTE nunca se vería.
    load_dotenv(RAIZ / ".env")

    elegida = (nombre or os.getenv("FUENTE") or "propia").strip().lower()
    if elegida not in FUENTES_VALIDAS:
        raise ValueError(f"Fuente desconocida: «{elegida}». Válidas: {', '.join(FUENTES_VALIDAS)}")
    if elegida == "simulada":
        return FuenteSimulada()
    if elegida == "json_prueba":
        return FuenteJSON()
    return FuentePropia()
