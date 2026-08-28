"""
Harness de evaluación — etapa 6 (Evaluación) de PP3.

Mide lo que importa operativamente, no lo que es fácil de medir. La métrica que se
presenta al área no es el acierto de rubro sino **precision@K**: de las obras que el
técnico terminó mirando, cuántas estaban en el tope de la cola que armó el sistema.
Responde la única pregunta que al área le interesa — ¿me hace ahorrar viajes o no?

El baseline a superar es honesto y bajo: hoy el avance de la gestora se acepta sin
contraste. Cualquier mejora sobre eso es ganancia medible sin inflar nada.
"""
import pandas as pd

from vision.decision import SOBRE_REPORTE, grado_de_respaldo, leer_evidencia
from vision.percepcion import PercepcionSimulada


def correr_pipeline(df_eval: pd.DataFrame, tasa_error: float, seed: int = 42) -> pd.DataFrame:
    """
    Corre el pipeline completo sobre el conjunto de evaluación con un modelo simulado.

    Devuelve una fila por obra con lo que el sistema concluyó, para poder comparar
    contra la verdad. Es el mismo camino que recorrería una foto real: la única pieza
    intercambiada es de dónde sale la evidencia.
    """
    percepcion = PercepcionSimulada(tasa_error=tasa_error, seed=seed)
    filas = []
    for fila in df_eval.itertuples():
        evidencia = percepcion.leer_desde_verdad(fila.rubro_alcanzado)
        lectura = leer_evidencia(evidencia)
        grado, motivo = grado_de_respaldo(lectura, int(fila.afo_declarado))
        filas.append({
            "vivienda_id":      fila.vivienda_id,
            "rubro_real":       fila.rubro_alcanzado,
            "rubro_estimado":   lectura.rubro_alcanzado,
            "afo_real":         fila.afo_real,
            "afo_estimado":     lectura.afo_estimado,
            "afo_declarado":    fila.afo_declarado,
            "determinable":     lectura.determinable,
            "grado":            grado,
            "motivo":           motivo,
            "sobre_reporta":    fila.sobre_reporta,
            "sobre_reporte":    fila.sobre_reporte,
            "brecha_declarada": fila.afo_declarado - lectura.afo_estimado,
        })
    return pd.DataFrame(filas)


def metricas(res: pd.DataFrame) -> dict:
    """
    Métricas de una corrida. Cada una responde una pregunta distinta:

    - acierto de rubro (exacto y ±1): diagnóstico interno del modelo.
    - MAE en puntos de AFO: conecta con el indicador que el área ya conoce.
    - precisión / recall de la alerta: la métrica operativa. Como el técnico revisa
      igual, conviene privilegiar recall — un falso positivo cuesta minutos, un falso
      negativo deja pasar sobre-reporte.
    - tasa de abstención: salud del sistema, cuánto admite no saber.
    """
    determinables = res[res["determinable"]]
    alerta = res["grado"] == SOBRE_REPORTE
    verdad = res["sobre_reporta"]

    vp = int((alerta & verdad).sum())
    fp = int((alerta & ~verdad).sum())
    fn = int((~alerta & verdad).sum())

    return {
        "obras":              len(res),
        "acierto_rubro":      float((res["rubro_estimado"] == res["rubro_real"]).mean()),
        "acierto_rubro_pm1":  float((res["rubro_estimado"] - res["rubro_real"]).abs().le(1).mean()),
        "mae_afo":            float((res["afo_estimado"] - res["afo_real"]).abs().mean()),
        "tasa_abstencion":    float((~res["determinable"]).mean()),
        "alertas_emitidas":   int(alerta.sum()),
        "precision_alerta":   vp / (vp + fp) if (vp + fp) else float("nan"),
        "recall_alerta":      vp / (vp + fn) if (vp + fn) else float("nan"),
        "mae_afo_determinables": float(
            (determinables["afo_estimado"] - determinables["afo_real"]).abs().mean()
        ) if len(determinables) else float("nan"),
    }


def cola_de_revision(res: pd.DataFrame) -> pd.DataFrame:
    """
    La cola que efectivamente recibe el técnico, ordenada por prioridad.

    Solo entran las obras con lectura **determinable** y alerta de sobre-reporte. Una
    obra cuya foto no se pudo leer no pertenece acá: no hay evidencia de que sobre-reporte,
    hay ausencia de evidencia. Va a una cola distinta ("pedir mejor foto"), y mezclarlas
    arruina las dos — el AFO estimado de una lectura cortada es artificialmente bajo, así
    que si se mezclan, las fotos ilegibles copan el tope y desplazan a los sobre-reportes
    reales.
    """
    alertadas = res[(res["determinable"]) & (res["grado"] == SOBRE_REPORTE)]
    return alertadas.sort_values("brecha_declarada", ascending=False)


def cola_de_evidencia_insuficiente(res: pd.DataFrame) -> pd.DataFrame:
    """Obras donde la foto no alcanzó. No es un fallo: es un pedido concreto de mejor foto."""
    return res[~res["determinable"]]


def precision_en_k(res: pd.DataFrame, k: int = 50) -> float:
    """
    De las K obras que el sistema pone al tope de la cola, cuántas sobre-reportan de verdad.

    Es la métrica que se lleva a la presentación: el técnico no revisa 900 obras, revisa
    las primeras K. Que el sistema acierte en el promedio general no sirve de nada si se
    equivoca justo arriba de la lista.
    """
    top = cola_de_revision(res).head(k)
    if top.empty:
        return float("nan")
    return float(top["sobre_reporta"].mean())


def baseline_sin_sistema(res: pd.DataFrame) -> float:
    """
    Con qué acertaría el técnico eligiendo K obras al azar — que es el estado actual.

    Es la referencia contra la cual se mide la ganancia. Deliberadamente generosa con
    el statu quo: hoy ni siquiera hay una lista, se elige por cercanía o criterio propio.
    """
    return float(res["sobre_reporta"].mean())


def barrido_sensibilidad(df_eval: pd.DataFrame,
                         tasas=(0.0, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50),
                         k: int = 50, seed: int = 42) -> pd.DataFrame:
    """
    **El resultado que se puede presentar hoy, sin una sola foto.**

    Barre la tasa de error del modelo de percepción y mide cómo se degrada el sistema.
    Responde una pregunta de diseño que normalmente se contesta tarde y cara: *¿cuán
    bueno tiene que ser el modelo de visión para que esto le sirva al área?*

    Si el sistema sigue siendo útil con un modelo que se equivoca en un cuarto de los
    campos, la apuesta es razonable. Si necesita un modelo casi perfecto, conviene
    saberlo antes de invertir en etiquetar fotos.
    """
    filas = []
    for tasa in tasas:
        res = correr_pipeline(df_eval, tasa_error=tasa, seed=seed)
        m = metricas(res)
        m["tasa_error"] = tasa
        m["precision_top_k"] = precision_en_k(res, k)
        m["baseline"] = baseline_sin_sistema(res)
        m["cola_revision"] = len(cola_de_revision(res))
        m["cola_mejor_foto"] = len(cola_de_evidencia_insuficiente(res))
        filas.append(m)
    return pd.DataFrame(filas).set_index("tasa_error")


def matriz_confusion_rubro(res: pd.DataFrame) -> pd.DataFrame:
    """Rubro real contra rubro estimado. Diagnóstico interno, no material de presentación."""
    return pd.crosstab(res["rubro_real"], res["rubro_estimado"],
                       rownames=["real"], colnames=["estimado"])


def distribucion_grados(res: pd.DataFrame) -> pd.Series:
    """Cómo se reparten los grados de respaldo. Muestra cuánto el sistema admite no saber."""
    return res["grado"].value_counts(normalize=True).mul(100).round(1)
