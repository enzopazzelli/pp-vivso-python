"""Los endpoints de colección: cada uno entrega lo que su `FuenteDeDatos` tiene, en JSON."""
from fastapi import APIRouter, Depends, HTTPException, Query

from datos.api.dependencias import fuente_actual
from datos.api.serializacion import df_a_json
from datos.fuentes.base import FuenteDeDatos

router = APIRouter()


def _con_manejo(obtener_df):
    try:
        return df_a_json(obtener_df())
    except RuntimeError as error:   # base propia sin crear o sin migrar (Plan 3)
        raise HTTPException(status_code=503, detail=str(error)) from error


def _filtrar(filas: list[dict], **filtros: str | None) -> list[dict]:
    for campo, valor in filtros.items():
        if valor is not None:
            filas = [f for f in filas if f.get(campo) == valor]
    return filas


@router.get("/viviendas")
def viviendas(fuente: FuenteDeDatos = Depends(fuente_actual),
             departamento: str | None = Query(None), estado: str | None = Query(None)) -> list[dict]:
    filas = _con_manejo(fuente.viviendas)
    return _filtrar(filas, departamento=departamento, estado=estado)


@router.get("/organizaciones")
def organizaciones(fuente: FuenteDeDatos = Depends(fuente_actual),
                   tipo_gestora: str | None = Query(None)) -> list[dict]:
    filas = _con_manejo(fuente.organizaciones)
    return _filtrar(filas, tipo_gestora=tipo_gestora)


@router.get("/medidas")
def medidas(fuente: FuenteDeDatos = Depends(fuente_actual),
           consulta: str | None = Query(None), metrica: str | None = Query(None)) -> list[dict]:
    filas = _con_manejo(fuente.medidas)
    return _filtrar(filas, consulta=consulta, metrica=metrica)


@router.get("/expedientes")
def expedientes(fuente: FuenteDeDatos = Depends(fuente_actual), tipo: str | None = Query(None)) -> list[dict]:
    filas = _con_manejo(fuente.expedientes)
    return _filtrar(filas, tipo=tipo)


@router.get("/reclamos")
def reclamos(fuente: FuenteDeDatos = Depends(fuente_actual), estado: str | None = Query(None)) -> list[dict]:
    filas = _con_manejo(fuente.reclamos)
    return _filtrar(filas, estado=estado)


@router.get("/medidas-categoria")
def medidas_categoria(fuente: FuenteDeDatos = Depends(fuente_actual),
                      consulta: str | None = Query(None), metrica: str | None = Query(None)) -> list[dict]:
    filas = _con_manejo(fuente.medidas_categoria)
    return _filtrar(filas, consulta=consulta, metrica=metrica)
