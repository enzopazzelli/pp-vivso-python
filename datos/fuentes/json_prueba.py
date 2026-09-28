"""Fuente de prueba: un JSON mínimo, sin PDF ni base, con la estructura común completa."""
import json
from pathlib import Path

import pandas as pd

from datos.fuentes.base import FuenteDeDatos
from datos.fuentes.estructura import (
    COLUMNAS_EXPEDIENTE, COLUMNAS_MEDIDA, COLUMNAS_MEDIDA_CATEGORIA, COLUMNAS_ORGANIZACION, COLUMNAS_RECLAMO,
    COLUMNAS_VIVIENDA, marco_vacio,
)

_RAIZ = Path(__file__).resolve().parent.parent.parent
_RUTA_PREDETERMINADA = _RAIZ / "datos_prueba" / "ejemplo.json"


class FuenteJSON(FuenteDeDatos):
    nombre = "json_prueba"

    def __init__(self, ruta: Path | str | None = None):
        ruta = Path(ruta) if ruta is not None else _RUTA_PREDETERMINADA
        self._datos = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}

    def _marco(self, clave: str, columnas: list[str]) -> pd.DataFrame:
        filas = self._datos.get(clave) or []
        # `reindex`, no `[columnas]`: un archivo «mínimo» de verdad puede no traer todas las columnas
        # de golpe. Las que falten quedan en None, igual que en las otras fuentes.
        return pd.DataFrame(filas).reindex(columns=columnas) if filas else marco_vacio(columnas)

    def viviendas(self) -> pd.DataFrame:
        return self._marco("viviendas", COLUMNAS_VIVIENDA)

    def organizaciones(self) -> pd.DataFrame:
        return self._marco("organizaciones", COLUMNAS_ORGANIZACION)

    def medidas(self) -> pd.DataFrame:
        return self._marco("medidas", COLUMNAS_MEDIDA)

    def expedientes(self) -> pd.DataFrame:
        return self._marco("expedientes", COLUMNAS_EXPEDIENTE)

    def reclamos(self) -> pd.DataFrame:
        return self._marco("reclamos", COLUMNAS_RECLAMO)

    def medidas_categoria(self) -> pd.DataFrame:
        return self._marco("medidas_categoria", COLUMNAS_MEDIDA_CATEGORIA)
