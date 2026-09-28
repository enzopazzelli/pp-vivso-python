"""Fuente simulada: los CSV de PP2 en `data/`. Se leen tal cual, nunca se modifican."""
from pathlib import Path

import pandas as pd

from datos.fuentes.base import FuenteDeDatos
from datos.fuentes.estructura import (
    COLUMNAS_EXPEDIENTE, COLUMNAS_MEDIDA, COLUMNAS_MEDIDA_CATEGORIA, COLUMNAS_ORGANIZACION, COLUMNAS_RECLAMO,
    COLUMNAS_VIVIENDA, marco_vacio,
)
from datos.normalizacion import clasificar_formato_expediente, normalizar_organizacion

_RAIZ = Path(__file__).resolve().parent.parent.parent


class FuenteSimulada(FuenteDeDatos):
    nombre = "simulada"

    def __init__(self, carpeta_datos: Path | None = None):
        self._dir = carpeta_datos or (_RAIZ / "data")

    def _leer(self, nombre_archivo: str) -> pd.DataFrame | None:
        ruta = self._dir / nombre_archivo
        return pd.read_csv(ruta) if ruta.exists() else None

    def _leer_viviendas_crudo(self) -> pd.DataFrame | None:
        """Mismo criterio que `dashboard/components/data_loader.py`: prefiere el procesado, y si a
        ese le falta `criterio` (se generó antes de que existiera esa columna), lo completa."""
        procesadas = self._leer("viviendas_procesadas.csv")
        sinteticas = self._leer("viviendas_sinteticas.csv")
        crudo = procesadas if procesadas is not None else sinteticas
        if crudo is None:
            return None
        if "criterio" not in crudo.columns and sinteticas is not None:
            crudo = crudo.merge(sinteticas[["num_exp", "criterio"]], on="num_exp", how="left")
        return crudo

    def viviendas(self) -> pd.DataFrame:
        crudo = self._leer_viviendas_crudo()
        if crudo is None:
            return marco_vacio(COLUMNAS_VIVIENDA)
        df = pd.DataFrame({c: crudo[c] if c in crudo.columns else None for c in COLUMNAS_VIVIENDA})
        # PP2 no distingue el expediente de la clave de la vivienda, ni modeló el titular anonimizado
        # de VISOC (su «representante» es otro concepto: el representante familiar).
        df["expediente"] = crudo["num_exp"]
        df["fecha_activacion"] = None   # PP2 nunca modeló este dato por vivienda
        return df[COLUMNAS_VIVIENDA]

    def organizaciones(self) -> pd.DataFrame:
        crudo = self._leer("organizaciones.csv")
        if crudo is None:
            return marco_vacio(COLUMNAS_ORGANIZACION)
        df = pd.DataFrame({c: crudo[c] if c in crudo.columns else None for c in COLUMNAS_ORGANIZACION})
        df["nombre_normalizado"] = crudo["nombre"].map(normalizar_organizacion)
        df["cuit_provisional"] = False
        return df[COLUMNAS_ORGANIZACION]

    def medidas(self) -> pd.DataFrame:
        return marco_vacio(COLUMNAS_MEDIDA)   # PP2 no midió activaciones por organización

    def expedientes(self) -> pd.DataFrame:
        crudo = self._leer_viviendas_crudo()
        if crudo is None:
            return marco_vacio(COLUMNAS_EXPEDIENTE)
        return pd.DataFrame({
            "id": range(1, len(crudo) + 1),
            "vivienda_num_exp": crudo["num_exp"],
            "numero": crudo["num_exp"],
            "formato": crudo["num_exp"].map(clasificar_formato_expediente),
            "tipo": "solicitud",
            "fecha_reporte": None,
        })[COLUMNAS_EXPEDIENTE]

    def reclamos(self) -> pd.DataFrame:
        return marco_vacio(COLUMNAS_RECLAMO)

    def medidas_categoria(self) -> pd.DataFrame:
        return marco_vacio(COLUMNAS_MEDIDA_CATEGORIA)   # PP2 no trae totales por categoría
