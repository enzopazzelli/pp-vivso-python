"""Cuánto tiempo pasa entre la solicitud, la activación y el fin de obra de una vivienda."""
from datos.indicadores.base import Indicador, _a_fecha, confianza_minima

_REPORTES = ["visoc_viviendas_segun_solicitante"]


def _resumen_de_dias(pares: list[tuple]) -> dict:
    dias = sorted((fin - inicio).days for inicio, fin in pares if fin >= inicio)
    if not dias:
        return {"cantidad": 0, "dias_minimo": None, "dias_mediana": None, "dias_maximo": None}
    mitad = len(dias) // 2
    mediana = dias[mitad] if len(dias) % 2 else (dias[mitad - 1] + dias[mitad]) // 2
    return {"cantidad": len(dias), "dias_minimo": dias[0], "dias_mediana": mediana, "dias_maximo": dias[-1]}


def tiempos_del_proceso(fuente) -> Indicador:
    base = dict(codigo="tiempos_del_proceso",
               pregunta="¿Cuánto pasa entre que se pide una vivienda, se activa y se termina?",
               explicacion=(
                   "Mide dos tramos: desde que se solicita hasta que se activa (el área confirmó que "
                   "«activar» es el paso previo al Acta de Finalización, cuando el técnico ya "
                   "certificó el 100 % de la obra), y desde que se activa hasta el fin de obra "
                   "registrado. Solo se calcula sobre viviendas que tienen ambas fechas."),
               como_leerlo=(
                   "Si la mediana de «solicitud a activación» es de varios cientos de días, significa "
                   "que la mitad de las viviendas tardan más que eso desde que se piden hasta que "
                   "llegan a esa etapa final del trámite."),
               confianza=confianza_minima(_REPORTES), reportes=_REPORTES)

    viviendas = fuente.viviendas()
    if viviendas.empty:
        return Indicador(**base, capacidad="no_disponible", valor={})

    solicitud = viviendas["fecha_solicitud"].map(_a_fecha)
    activacion = viviendas["fecha_activacion"].map(_a_fecha)
    fin = viviendas["fecha_fin"].map(_a_fecha)

    solicitud_a_activacion = [(s, a) for s, a in zip(solicitud, activacion) if s and a]
    activacion_a_fin = [(a, f) for a, f in zip(activacion, fin) if a and f]

    if not solicitud_a_activacion and not activacion_a_fin:
        return Indicador(**base, capacidad="no_disponible", valor={})

    valor = {"solicitud_a_activacion": _resumen_de_dias(solicitud_a_activacion),
             "activacion_a_fin_obra": _resumen_de_dias(activacion_a_fin)}
    return Indicador(**base, capacidad="disponible", valor=valor)
