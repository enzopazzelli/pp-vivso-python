"""
Carga centralizada de datos para el dashboard.
Prioriza datos procesados (con nivel_riesgo calculado),
cae a los sintéticos crudos si no existen.
"""
from pathlib import Path
import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent.parent


@st.cache_data(ttl=120)
def cargar_viviendas() -> pd.DataFrame:
    procesadas = _ROOT / "data" / "viviendas_procesadas.csv"
    sinteticas = _ROOT / "data" / "viviendas_sinteticas.csv"
    path = procesadas if procesadas.exists() else sinteticas
    df = pd.read_csv(path)
    # Si el procesado no tiene criterio (generado antes del cambio de schema),
    # complementar desde el sintético que sí lo tiene
    if "criterio" not in df.columns and sinteticas.exists():
        df_sin = pd.read_csv(sinteticas)[["num_exp", "criterio"]]
        df = df.merge(df_sin, on="num_exp", how="left")
    # Nombres canónicos para que las páginas no dependan del origen
    df = df.rename(columns={
        "avanceObra":      "avance_obra",
        "tipoVivienda":    "tipo_vivienda",
        "cantDormitorios": "cant_dormitorios",
        "fechaInic":       "fecha_inic",
        "fechaFin":        "fecha_fin",
        "numExp":          "num_exp",
    })
    return df


@st.cache_data(ttl=120)
def cargar_organizaciones() -> pd.DataFrame:
    path = _ROOT / "data" / "organizaciones.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=120)
def cargar_indicadores_ong() -> pd.DataFrame:
    path = _ROOT / "data" / "indicadores_ong.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=120)
def cargar_avance_rubros() -> pd.DataFrame:
    path = _ROOT / "data" / "avance_rubros.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=120)
def cargar_visitas() -> pd.DataFrame:
    path = _ROOT / "data" / "visitas.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)
