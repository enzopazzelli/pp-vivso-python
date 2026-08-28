"""
Verdad de referencia y reportes simulados, construidos sobre el dataset que ya existe.

La idea que hace posible medir sin fotos: el dataset sintético ya tiene el avance por
rubro de cada obra (tabla `avance_rubro`), así que sabemos exactamente en qué rubro
está parada cada vivienda. De ahí se deriva la evidencia que una foto perfecta
mostraría, se la degrada con una tasa de error controlada y se corre el pipeline
completo. Lo que se mide no es el modelo de visión —todavía no existe— sino **la capa
de decisión y el harness**, y sobre todo: cuán bueno tiene que ser el modelo real para
que el sistema le sirva al área.
"""
import numpy as np
import pandas as pd

from vision.rubrica import ORDEN_RUBROS, UMBRAL_RUBRO_COMPLETO, peso_acumulado

# Cuánto tiene que exceder un reporte a la realidad para considerarlo sobre-reporte
# *material*. Es el criterio de negocio con el que se etiqueta la verdad: por debajo
# de esto la diferencia es ruido de medición y no amerita mandar a un técnico.
SOBRE_REPORTE_MATERIAL_PTS = 10


def verdad_por_obra(df_rubros: pd.DataFrame, df_viviendas: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada obra: en qué rubro está realmente parada y cuál es su AFO.

    `rubro_alcanzado` es el último rubro terminado — el primero que no llegó al umbral,
    menos uno. Es el mismo criterio de "etapa activa" que ya usa el análisis de cuello
    de botella, para que ambos hablen de lo mismo.

    Se distingue `afo_rubros` (solo rubros terminados, que es todo lo que una foto puede
    confirmar) de `afo_real` (el avance declarado en el expediente, que incluye el avance
    parcial dentro del rubro en curso). La diferencia entre ambos no es un error: es un
    límite físico de la foto, y es lo que la tolerancia tiene que absorber.
    """
    incompletos = df_rubros[df_rubros["avance_pct"] < UMBRAL_RUBRO_COMPLETO]
    primer_incompleto = (incompletos.sort_values("rubro_id")
                                    .groupby("vivienda_id")["rubro_id"].first())

    todas = df_viviendas[["num_exp", "avance_obra", "estado", "cuit_org"]].copy()
    todas = todas.rename(columns={"num_exp": "vivienda_id"})
    # Una obra sin ningún rubro incompleto está terminada: alcanzó el último.
    todas["rubro_alcanzado"] = (todas["vivienda_id"].map(primer_incompleto)
                                                    .fillna(ORDEN_RUBROS[-1] + 1) - 1).astype(int)
    todas["afo_rubros"] = todas["rubro_alcanzado"].map(peso_acumulado)
    todas = todas.rename(columns={"avance_obra": "afo_real"})
    todas["parcial"] = todas["afo_real"] - todas["afo_rubros"]
    return todas


def inyectar_reportes(df_verdad: pd.DataFrame, seed: int = 7) -> pd.DataFrame:
    """
    Simula lo que la gestora declara: el avance real más una discrepancia.

    El rango sale de [S8] en `synthetic/generate.py` —la misma distribución de
    sobre-reporte que ya usa el dataset para las visitas técnicas—, así que no se
    inventa un supuesto nuevo: se reutiliza uno ya documentado y confirmable.

    El import va acá adentro a propósito: el dashboard desplegado consume este módulo,
    y no tiene por qué cargar el generador de datos entero —con Faker y todo— en cada
    arranque en frío solo para leer una constante. Además desacopla el deploy de un
    módulo que existe para correrse a mano.
    """
    from synthetic.generate import DISCREPANCIA_GESTORA_PRIMERA   # [S8]

    rng = np.random.default_rng(seed)
    df = df_verdad.copy()
    lo, hi = DISCREPANCIA_GESTORA_PRIMERA
    df["sobre_reporte"] = rng.integers(lo, hi + 1, size=len(df))
    df["afo_declarado"] = (df["afo_real"] + df["sobre_reporte"]).clip(0, 100)
    # Etiqueta de verdad para medir la alerta: sobre-reporte material, no cualquier ruido.
    df["sobre_reporta"] = df["sobre_reporte"] > SOBRE_REPORTE_MATERIAL_PTS
    return df


def preparar(df_rubros: pd.DataFrame, df_viviendas: pd.DataFrame,
             solo_activas: bool = True, seed: int = 7) -> pd.DataFrame:
    """
    Arma el conjunto de evaluación completo, listo para el harness.

    Por defecto se limita a obras activas: son las únicas donde la verificación
    fotográfica tiene sentido operativo. Una obra ya adjudicada no se va a visitar.
    """
    df = verdad_por_obra(df_rubros, df_viviendas)
    if solo_activas:
        df = df[df["estado"].isin(["Iniciada", "Avanzada"])]
    return inyectar_reportes(df, seed=seed)
