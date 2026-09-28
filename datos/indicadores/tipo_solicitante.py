"""Peso de cada tipo de solicitante, a partir de los totales que trae el pie de «Por Solicitante»
(no por organización: el reporte no dice a cuál de las 4 categorías pertenece cada fila, solo el total)."""
from datos.indicadores.base import Indicador, confianza_minima

_REPORTES = ["visoc_por_solicitante"]


def peso_tipo_solicitante(fuente, consulta: str = "solicitadas") -> Indicador:
    base = dict(codigo="peso_tipo_solicitante",
               pregunta="¿Quién pide más: cooperativas, asociaciones, comisiones o intendencias?",
               explicacion=(
                   "Suma las solicitudes de cada una de las categorías que trae el reporte «Por "
                   "Solicitante» (cooperativa, asociación/ONG, comisionado, intendencia y externa). "
                   "Es un total por categoría, no un dato por organización individual: el reporte no "
                   "dice a cuál de las 4 categorías pertenece cada organización, solo el total de cada una."),
               como_leerlo=(
                   "Si «ASOCIACION_ONG» tiene 507 solicitudes sobre un total de 1109, significa que "
                   "casi la mitad de todo lo solicitado viene de asociaciones civiles u ONG."),
               confianza=confianza_minima(_REPORTES), reportes=_REPORTES)

    medidas_categoria = fuente.medidas_categoria()
    if medidas_categoria.empty:
        return Indicador(**base, capacidad="no_disponible", valor={})

    de_la_consulta = medidas_categoria[
        (medidas_categoria["consulta"] == consulta) & (medidas_categoria["metrica"] == "solicitudes")]
    if de_la_consulta.empty:
        return Indicador(**base, capacidad="no_disponible", valor={})

    # Si esa consulta se importó más de una vez (otro período), se usa el pie del reporte más nuevo,
    # sin importar en qué orden se cargaron los archivos.
    mas_reciente = de_la_consulta["fecha_reporte"].max()
    de_la_consulta = de_la_consulta[de_la_consulta["fecha_reporte"] == mas_reciente]

    valor = {"solicitudes": dict(zip(de_la_consulta["tipo_solicitante"], de_la_consulta["valor"]))}
    return Indicador(**base, capacidad="disponible", valor=valor)
