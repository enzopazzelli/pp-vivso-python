"""La interfaz común que cumple cualquier fuente de datos."""
from abc import ABC, abstractmethod

import pandas as pd

from datos.catalogo_reportes import FICHAS
from datos.fuentes.estructura import COLUMNAS_ORGANIZACION, COLUMNAS_VIVIENDA


class FuenteDeDatos(ABC):
    """Todas las fuentes entregan la misma estructura (`datos/fuentes/estructura.py`); ver
    `capacidades()` para saber qué tan completa está con cada una."""

    nombre: str

    @abstractmethod
    def viviendas(self) -> pd.DataFrame: ...

    @abstractmethod
    def organizaciones(self) -> pd.DataFrame: ...

    @abstractmethod
    def medidas(self) -> pd.DataFrame: ...

    @abstractmethod
    def expedientes(self) -> pd.DataFrame: ...

    @abstractmethod
    def reclamos(self) -> pd.DataFrame: ...

    @abstractmethod
    def medidas_categoria(self) -> pd.DataFrame: ...

    def catalogo_reportes(self) -> list[dict]:
        """Es documentación, no datos medidos: igual para cualquier fuente."""
        return [{"codigo": codigo, **ficha} for codigo, ficha in FICHAS.items()]

    def capacidades(self) -> dict:
        """Qué colecciones tienen datos con esta fuente, y qué campos de viviendas/organizaciones
        están poblados. Sirve de base para las capacidades por indicador (plan posterior)."""
        resultado = {}
        for coleccion, columnas in (("viviendas", COLUMNAS_VIVIENDA), ("organizaciones", COLUMNAS_ORGANIZACION)):
            df = getattr(self, coleccion)()
            resultado[coleccion] = {
                "disponible": not df.empty,
                "campos": {c: bool(df[c].notna().any()) if not df.empty else False for c in columnas},
            }
        for coleccion in ("medidas", "expedientes", "reclamos", "medidas_categoria"):
            df = getattr(self, coleccion)()
            resultado[coleccion] = {"disponible": not df.empty}
        return resultado
