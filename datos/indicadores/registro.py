"""Junta todos los indicadores para poder calcularlos o consultar su disponibilidad de una sola vez."""
from datos.fuentes.base import FuenteDeDatos
from datos.indicadores.base import Indicador
from datos.indicadores.organizaciones import tasa_activacion_finalizacion
from datos.indicadores.tiempos import tiempos_del_proceso
from datos.indicadores.tipo_solicitante import peso_tipo_solicitante
from datos.indicadores.viviendas import antiguedad_sin_terminar, por_clasificacion_tipo_dormitorios, \
    terminadas_y_sin_terminar

TODOS = [
    por_clasificacion_tipo_dormitorios,
    terminadas_y_sin_terminar,
    antiguedad_sin_terminar,
    tasa_activacion_finalizacion,
    peso_tipo_solicitante,
    tiempos_del_proceso,
]


def calcular_todos(fuente: FuenteDeDatos) -> list[Indicador]:
    return [funcion(fuente) for funcion in TODOS]


def capacidades_indicadores(fuente: FuenteDeDatos) -> dict[str, str]:
    """Código de indicador -> "disponible" / "parcial" / "no_disponible" con la fuente activa."""
    return {indicador.codigo: indicador.capacidad for indicador in calcular_todos(fuente)}
