"""Indicadores sobre viviendas: qué se construye, cuántas terminan y desde hace cuánto se espera."""
from datos.indicadores.base import Indicador, _a_fecha, confianza_minima

_REPORTES = ["visoc_viviendas_segun_solicitante"]


def por_clasificacion_tipo_dormitorios(fuente) -> Indicador:
    base = dict(codigo="viviendas_por_clasificacion_tipo_dormitorios",
               pregunta="¿Qué se está construyendo?",
               explicacion=(
                   "Cuenta las viviendas según su tipo (urbana, rural o ecológica), su clasificación "
                   "(el criterio con el que se aprobó la solicitud) y su cantidad de dormitorios."),
               como_leerlo=(
                   "Si «Urbana» tiene 54 y «Rural» tiene 51, significa que de las viviendas que "
                   "conocemos, casi la mitad son en el campo, no en la ciudad."),
               confianza=confianza_minima(_REPORTES), reportes=_REPORTES)

    viviendas = fuente.viviendas()
    if viviendas.empty:
        return Indicador(**base, capacidad="no_disponible", valor={})

    valor = {
        "por_tipo": viviendas["tipo_vivienda"].value_counts(dropna=True).to_dict(),
        "por_clasificacion": viviendas["clasificacion"].value_counts(dropna=True).to_dict(),
        "por_dormitorios": {int(k): v for k, v in
                            viviendas["cant_dormitorios"].value_counts(dropna=True).sort_index().items()},
    }
    return Indicador(**base, capacidad="disponible", valor=valor)


def terminadas_y_sin_terminar(fuente) -> Indicador:
    base = dict(codigo="terminadas_y_sin_terminar",
               pregunta="¿Cuántas viviendas terminaron y cuántas siguen pendientes?",
               explicacion=(
                   "Compara las viviendas ya terminadas con las que siguen en curso. Las solicitudes "
                   "desaprobadas se cuentan aparte: no están «pendientes», quedaron rechazadas."),
               como_leerlo=(
                   "Si «sin terminar» es 27 y «terminadas» es 78, hay 27 viviendas que todavía no "
                   "llegaron al 100 % de avance, sobre un total de 107 solicitudes (sin contar las "
                   "desaprobadas)."),
               confianza=confianza_minima(_REPORTES), reportes=_REPORTES)

    viviendas = fuente.viviendas()
    if viviendas.empty:
        return Indicador(**base, capacidad="no_disponible", valor={})

    # «Adjudicada» es un cuarto estado que solo usan los datos simulados de PP2 (VISOC no lo tiene):
    # tanto el generador (synthetic/generate.py) como el tablero actual la tratan como obra terminada.
    terminadas = viviendas[viviendas["estado"].isin(["Finalizada", "Adjudicada"])]
    solicitudes = viviendas["fecha_solicitud"].dropna().map(_a_fecha).dropna()
    finalizaciones = terminadas["fecha_fin"].dropna().map(_a_fecha).dropna()

    def _por_anio(fechas):
        conteo: dict[int, int] = {}
        for f in fechas:
            conteo[f.year] = conteo.get(f.year, 0) + 1
        return dict(sorted(conteo.items()))

    valor = {
        "terminadas": int(viviendas["estado"].isin(["Finalizada", "Adjudicada"]).sum()),
        "sin_terminar": int(viviendas["estado"].isin(["Iniciada", "Avanzada"]).sum()),
        "desaprobadas": int((viviendas["estado"] == "Desaprobada").sum()),
        "solicitadas_por_anio": _por_anio(solicitudes),
        "finalizadas_por_anio": _por_anio(finalizaciones),
    }
    capacidad = "disponible" if (valor["solicitadas_por_anio"] or valor["finalizadas_por_anio"]
                                 or valor["terminadas"] or valor["sin_terminar"]) else "parcial"
    return Indicador(**base, capacidad=capacidad, valor=valor)


def antiguedad_sin_terminar(fuente, hoy: "date | None" = None) -> Indicador:
    from datetime import date as _date
    hoy = hoy or _date.today()
    base = dict(codigo="antiguedad_sin_terminar",
               pregunta="¿Hace cuánto esperan las solicitudes que todavía no terminaron?",
               explicacion=(
                   "De las viviendas que están iniciadas o avanzadas (ni terminadas ni desaprobadas), "
                   "cuenta cuántos días pasaron desde que se pidieron."),
               como_leerlo=(
                   "Si la mediana es 2610 días (unos 7 años), la mitad de las solicitudes pendientes "
                   "llevan esperando más de 7 años, y la otra mitad, menos."),
               confianza=confianza_minima(_REPORTES), reportes=_REPORTES)

    viviendas = fuente.viviendas()
    pendientes = viviendas[viviendas["estado"].isin(["Iniciada", "Avanzada"])] if not viviendas.empty else viviendas
    fechas = pendientes["fecha_solicitud"].map(_a_fecha).dropna() if not pendientes.empty else pendientes
    if fechas.empty:
        return Indicador(**base, capacidad="no_disponible", valor={})

    dias = sorted((hoy - f).days for f in fechas)
    mitad = len(dias) // 2
    mediana = dias[mitad] if len(dias) % 2 else (dias[mitad - 1] + dias[mitad]) // 2
    valor = {"cantidad": len(dias), "dias_minimo": dias[0], "dias_mediana": mediana, "dias_maximo": dias[-1]}
    return Indicador(**base, capacidad="disponible", valor=valor)
