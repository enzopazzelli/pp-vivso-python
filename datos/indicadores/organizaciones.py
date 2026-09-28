"""Tasa de activación y de finalización por organización, a partir de «Por Solicitante»."""
from datos.indicadores.base import Indicador, confianza_minima

_REPORTES = ["visoc_por_solicitante"]


def tasa_activacion_finalizacion(fuente) -> Indicador:
    base = dict(codigo="tasa_activacion_finalizacion",
               pregunta="¿Qué porcentaje de lo solicitado por cada organización ya se activó o se terminó?",
               explicacion=(
                   "Compara, para cada organización, las solicitudes del reporte «solicitadas» contra "
                   "las activadas del reporte «activadas» y las terminadas del reporte «finalizadas». "
                   "Ojo: VISOC mezcla solicitudes de distintos años en cada reporte, así que una "
                   "organización puede tener más activadas que solicitadas del período — no es un "
                   "error, es una limitación conocida del sistema (no se puede armar una cohorte "
                   "única y trazable). Solo se calcula para las organizaciones que tienen datos en "
                   "las tres consultas: una organización ausente en el reporte «activadas» o "
                   "«finalizadas» queda afuera del cálculo, no se le asume 0 %, porque no sabemos si "
                   "esa ausencia significa que no tuvo ninguna o que el reporte no la incluyó."),
               como_leerlo=(
                   "Una tasa de activación de 1.0 (100 %) significa que se activó tanto como se "
                   "solicitó en el período; no significa que no queden solicitudes pendientes de "
                   "años anteriores."),
               confianza=confianza_minima(_REPORTES), reportes=_REPORTES)

    medidas = fuente.medidas()
    if medidas.empty:
        return Indicador(**base, capacidad="no_disponible", valor={})

    # Un reporte puede volver a importarse con datos distintos (otro período). Si eso pasa, se usa el
    # más nuevo por «fecha_reporte» para esa organización y esa consulta — nunca se promedian entre sí
    # ni se toma el que haya entrado último a la base por casualidad.
    medidas = medidas.sort_values("fecha_reporte").drop_duplicates(
        subset=["cuit", "consulta", "metrica"], keep="last")
    piv = medidas.pivot(index=["cuit", "nombre_organizacion"], columns=["consulta", "metrica"], values="valor")
    columnas_necesarias = [("solicitadas", "solicitudes"), ("activadas", "activadas"),
                           ("finalizadas", "fin_obras")]
    if not all(c in piv.columns for c in columnas_necesarias):
        return Indicador(**base, capacidad="parcial",
                         valor={"organizaciones_con_datos_completos": 0,
                                "organizaciones_totales": piv.shape[0], "por_organizacion": []})

    completas = piv.dropna(subset=columnas_necesarias)
    por_organizacion = []
    for (cuit, nombre), fila in completas.iterrows():
        solicitudes = fila[("solicitadas", "solicitudes")]
        activadas = fila[("activadas", "activadas")]
        fin_obras = fila[("finalizadas", "fin_obras")]
        por_organizacion.append({
            "cuit": cuit, "nombre": nombre, "solicitudes": solicitudes, "activadas": activadas,
            "fin_obras": fin_obras,
            "tasa_activacion": round(activadas / solicitudes, 4) if solicitudes else None,
            "tasa_finalizacion": round(fin_obras / solicitudes, 4) if solicitudes else None,
        })
    capacidad = "disponible" if len(completas) == piv.shape[0] else "parcial"
    valor = {"organizaciones_con_datos_completos": len(completas), "organizaciones_totales": piv.shape[0],
             "por_organizacion": por_organizacion}
    return Indicador(**base, capacidad=capacidad, valor=valor)
