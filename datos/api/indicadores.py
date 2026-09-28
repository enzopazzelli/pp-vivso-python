"""Indicadores calculados sobre la fuente activa, y qué tan disponibles están."""
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException

from datos.api.dependencias import fuente_actual
from datos.fuentes.base import FuenteDeDatos
from datos.indicadores.registro import calcular_todos, capacidades_indicadores

router = APIRouter()


def _con_manejo(obtener):
    """Misma firma y mismo propósito que `_con_manejo` en `colecciones.py`: los indicadores llaman a
    `fuente.viviendas()` etc. sin manejo propio (Plan 3), y acá se convierte la `FuentePropia` sin crear
    o sin migrar en un 503 legible en vez de un 500 con traceback."""
    try:
        return obtener()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/indicadores")
def indicadores(fuente: FuenteDeDatos = Depends(fuente_actual)) -> list[dict]:
    return [asdict(i) for i in _con_manejo(lambda: calcular_todos(fuente))]


@router.get("/indicadores/{codigo}")
def indicador(codigo: str, fuente: FuenteDeDatos = Depends(fuente_actual)) -> dict:
    for i in _con_manejo(lambda: calcular_todos(fuente)):
        if i.codigo == codigo:
            return asdict(i)
    raise HTTPException(status_code=404, detail=f"No existe el indicador «{codigo}»")


@router.get("/capacidades")
def capacidades(fuente: FuenteDeDatos = Depends(fuente_actual)) -> dict:
    return {"colecciones": _con_manejo(fuente.capacidades),
           "indicadores": _con_manejo(lambda: capacidades_indicadores(fuente))}
