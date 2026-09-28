"""La forma común de un indicador, y las funciones auxiliares que usan todos."""
from dataclasses import dataclass, field
from datetime import date, datetime

import pandas as pd

from datos.catalogo_reportes import FICHAS

# De más a menos confiable (sección 8 de la especificación)
_ORDEN_CONFIANZA = ("confirmado", "inferido", "sin_confirmar")


def confianza_minima(codigos_tipo_reporte: list[str]) -> str:
    """La confianza de un indicador es la más baja (la peor) de los reportes de los que sale."""
    confianzas = [FICHAS[codigo]["confianza"] for codigo in codigos_tipo_reporte]
    return max(confianzas, key=_ORDEN_CONFIANZA.index)


def _a_fecha(valor) -> date | None:
    """Interpreta una fecha venga como venga: objeto date, texto ISO o texto dd-mm-aaaa (las tres formas
    que usan hoy las distintas fuentes — ver el Ruling de fechas del Plan 2), o los vacíos de pandas
    (NaT, NA, NaN) que puede traer una columna de un DataFrame aunque hoy ninguna fuente los produzca."""
    if valor is None:
        return None
    try:
        if pd.isna(valor):   # cubre NaT, NA y NaN; algo no escalar (por ejemplo una lista) da array y sigue
            return None
    except (TypeError, ValueError):
        pass
    if valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor)
    for formato in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


@dataclass
class Indicador:
    """Un indicador ya calculado. `capacidad` es "disponible", "parcial" o "no_disponible" con la
    fuente que se usó para calcularlo."""
    codigo: str
    pregunta: str
    explicacion: str
    como_leerlo: str
    confianza: str
    capacidad: str
    valor: dict = field(default_factory=dict)
    reportes: list = field(default_factory=list)   # de qué tipo_reporte sale (sección 8 de la especificación)

    def __post_init__(self):
        if not self.explicacion.strip():
            raise ValueError(f"El indicador «{self.codigo}» no tiene «explicacion»")
        if not self.como_leerlo.strip():
            raise ValueError(f"El indicador «{self.codigo}» no tiene «como_leerlo»")
