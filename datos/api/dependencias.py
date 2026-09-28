"""Dependencias compartidas por los endpoints: qué fuente usar en este pedido."""
from fastapi import HTTPException, Query

from datos.fuentes.base import FuenteDeDatos
from datos.fuentes.registro import obtener_fuente


def fuente_actual(fuente: str | None = Query(None, description="propia / simulada / json_prueba")) -> FuenteDeDatos:
    try:
        return obtener_fuente(fuente)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
