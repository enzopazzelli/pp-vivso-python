"""Elegir el importador que corresponde a un archivo y describir los archivos desconocidos."""
import re
from pathlib import Path

from datos.importadores.base import Importador
from datos.importadores.pdf import leer_lineas_texto


def importadores_disponibles() -> list[Importador]:
    """Un importador por formato conocido. Los imports son perezosos para evitar ciclos."""
    from datos.importadores.visoc_por_solicitante import VisocPorSolicitante
    from datos.importadores.visoc_viviendas import VisocViviendasSegunSolicitante
    return [VisocPorSolicitante(), VisocViviendasSegunSolicitante()]


def elegir(ruta: Path, candidatos: list[Importador] | None = None, minimo: float = 0.6) -> Importador | None:
    """El importador con más confianza, siempre que llegue al mínimo. None si ninguno reconoce el archivo."""
    candidatos = importadores_disponibles() if candidatos is None else candidatos
    mejor, mejor_confianza = None, 0.0
    for importador in candidatos:
        confianza = importador.reconoce(Path(ruta))
        if confianza > mejor_confianza:
            mejor, mejor_confianza = importador, confianza
    return mejor if mejor_confianza >= minimo else None


def _forma(linea: str) -> str:
    """La estructura de una línea sin su contenido: letras → x, cifras → 9."""
    return re.sub(r"\d", "9", re.sub(r"[^\W\d_]", "x", linea))


def sonda(ruta: Path, max_lineas: int = 12) -> dict:
    """Describe un archivo desconocido mostrando solo su FORMA, nunca su texto, para no filtrar
    datos personales. Sirve para escribir después un importador nuevo."""
    ruta = Path(ruta)
    formato = ruta.suffix.lower()
    if formato == ".pdf":
        try:
            lineas = leer_lineas_texto(ruta)
        except Exception:
            return {"formato": formato, "error": "No se pudo leer el PDF"}
    elif formato in (".txt", ".csv"):
        lineas = ruta.read_text(encoding="utf-8", errors="ignore").splitlines()
    else:
        return {"formato": formato, "mensaje": "No hay lector de forma para este formato"}
    return {"formato": formato, "lineas": len(lineas), "forma": [_forma(l) for l in lineas[:max_lineas]]}
