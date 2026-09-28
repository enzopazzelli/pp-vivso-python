"""Ficha de cada tipo de reporte, y el historial de lo que se importó (Tarea 5 agrega esto último)."""
from fastapi import APIRouter, Depends

from datos.api.dependencias import fuente_actual
from datos.fuentes.base import FuenteDeDatos

router = APIRouter()


@router.get("/catalogo-reportes")
def catalogo_reportes(fuente: FuenteDeDatos = Depends(fuente_actual)) -> list[dict]:
    return fuente.catalogo_reportes()


def _abrir_sesion():
    from sqlalchemy.orm import Session

    from datos.sesion import crear_engine
    return Session(crear_engine())


@router.get("/importaciones")
def importaciones() -> list[dict]:
    """No depende de `?fuente=`: solo la base propia tiene esta noción. Si no existe o está vacía,
    "no hay importaciones todavía" es un estado normal, no un error (a diferencia de las colecciones)."""
    from sqlalchemy.exc import OperationalError

    from datos.modelo import Importacion

    with _abrir_sesion() as sesion:
        try:
            filas = sesion.query(Importacion).order_by(Importacion.importado_en.desc()).all()
        except OperationalError:
            return []
    return [{
        "id": f.id, "tipo_reporte": f.tipo_reporte, "archivo_nombre": f.archivo_nombre,
        "fecha_reporte": f.fecha_reporte.isoformat() if f.fecha_reporte else None,
        "estado": f.estado, "filas_leidas": f.filas_leidas,
        "importado_en": f.importado_en.isoformat(),
    } for f in filas]
