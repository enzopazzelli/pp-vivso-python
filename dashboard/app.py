import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard.components.data_loader import cargar_viviendas, cargar_visitas
from dashboard.components.criterios import nota_criterio

st.set_page_config(
    page_title="VIVSO — Resumen Ejecutivo",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Encabezado ─────────────────────────────────────────────────────────────
st.title("🏠 VIVSO — Sistema de Gestión de Viviendas Sociales")
st.markdown(
    "**Subsecretaría de Promoción Humana** · Gobierno de Santiago del Estero  \n"
    "Panel de análisis — Equipo Ciencia de Datos · PP2 ITSE"
)
st.divider()

df  = cargar_viviendas()
vis = cargar_visitas()

EN_OBRA    = ["Iniciada", "Avanzada"]
TERMINADAS = ["Finalizada", "Adjudicada"]

# ── Alerta operativa ───────────────────────────────────────────────────────
# Obras en riesgo alto que todavía no recibieron ninguna visita técnica:
# son las que un jefe de área querría ver apenas abre el panel.
visitadas = set(vis["vivienda_id"].unique()) if not vis.empty else set()
riesgo_alto = df[df["nivel_riesgo"] == "alto"]
sin_visita  = riesgo_alto[~riesgo_alto["num_exp"].isin(visitadas)]

if len(sin_visita):
    ca, cb = st.columns([5, 1])
    ca.error(
        f"⚠️  **{len(riesgo_alto)} obras en riesgo alto** · "
        f"**{len(sin_visita)} sin ninguna visita técnica** — requieren atención prioritaria."
    )
    cb.page_link("pages/04_tecnicos.py", label="Ver detalle →")

# ── KPIs principales ───────────────────────────────────────────────────────
total      = len(df)
en_obra    = int(df["estado"].isin(EN_OBRA).sum())
terminadas = int(df["estado"].isin(TERMINADAS).sum())
avance     = df["avance_obra"].mean()
n_alto     = int((df["nivel_riesgo"] == "alto").sum())
n_deptos   = int(df["departamento"].nunique())

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Viviendas",       f"{total:,}".replace(",", "."))
k2.metric("En obra",         f"{en_obra:,}".replace(",", "."))
k3.metric("Terminadas",      f"{terminadas:,}".replace(",", "."))
k4.metric("Avance promedio", f"{avance:.1f}%")
k5.metric("Riesgo alto",     n_alto, delta=f"{n_alto/total*100:.0f}% del total",
          delta_color="inverse")
k6.metric("Departamentos",   n_deptos)

nota_criterio("estados", "avance", "riesgo", "tasa_finalizacion")

st.divider()

# ── Estado del programa + tendencia de inicios ─────────────────────────────
col_donut, col_linea = st.columns([2, 3])

with col_donut:
    colores_estado = {
        "Iniciada": "#f59e0b", "Avanzada": "#3b82f6",
        "Finalizada": "#22c55e", "Adjudicada": "#6366f1",
    }
    por_estado = df["estado"].value_counts().reset_index()
    por_estado.columns = ["estado", "cantidad"]
    fig_donut = px.pie(
        por_estado, names="estado", values="cantidad",
        title="Estado del programa",
        color="estado", color_discrete_map=colores_estado,
        hole=0.55,
    )
    fig_donut.update_traces(textposition="inside", textinfo="percent+label")
    fig_donut.update_layout(
        showlegend=False, height=340, margin=dict(t=50, b=10, l=10, r=10),
        annotations=[dict(text=f"{total:,}".replace(",", ".") + "<br>obras",
                          x=0.5, y=0.5, font_size=16, showarrow=False)],
    )
    st.plotly_chart(fig_donut, width="stretch")

with col_linea:
    # fecha_inic viene como "DD-MM-YYYY"; agrupamos por mes calendario.
    fechas = pd.to_datetime(df["fecha_inic"], format="%d-%m-%Y", errors="coerce")
    por_mes = (
        fechas.dropna().dt.to_period("M").dt.to_timestamp()
        .value_counts().sort_index()
        .reset_index()
    )
    por_mes.columns = ["mes", "cantidad"]
    fig_linea = px.area(
        por_mes, x="mes", y="cantidad",
        title="Obras iniciadas por mes",
        labels={"mes": "", "cantidad": "Obras iniciadas"},
        color_discrete_sequence=["#3b82f6"],
    )
    fig_linea.update_traces(line=dict(width=2), fillcolor="rgba(59,130,246,0.15)")
    fig_linea.update_layout(height=340, margin=dict(t=50, b=10, l=10, r=10))
    st.plotly_chart(fig_linea, width="stretch")

# ── Mapa provincial ────────────────────────────────────────────────────────
mapa_df = df.dropna(subset=["lat", "lng"])
if not mapa_df.empty:
    st.subheader(f"Distribución geográfica — {len(mapa_df):,} obras por nivel de riesgo".replace(",", "."))
    fig_mapa = px.scatter_map(
        mapa_df, lat="lat", lon="lng",
        color="nivel_riesgo",
        color_discrete_map={"bajo": "#22c55e", "medio": "#f59e0b", "alto": "#ef4444"},
        hover_data={"num_exp": True, "localidad": True, "avance_obra": True,
                    "lat": False, "lng": False},
        zoom=6, map_style="carto-positron",
    )
    fig_mapa.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=380,
                           legend=dict(orientation="h", y=-0.05))
    st.plotly_chart(fig_mapa, width="stretch")
    nota_criterio("geografia", "riesgo")

st.divider()

# ── Navegación a las secciones ─────────────────────────────────────────────
st.subheader("Explorar el sistema")

SECCIONES = [
    ("pages/01_viviendas.py", "🏘", "Viviendas", "Catastro, filtros y mapa de riesgo"),
    ("pages/02_ongs.py",      "🤝", "ONGs",      "Rendimiento de las gestoras"),
    ("pages/03_mineria.py",   "🔬", "Minería",   "Modelo de riesgo, rubros y tiempos"),
    ("pages/06_evolucion.py", "📈", "Evolución", "Series de tiempo del programa"),
    ("pages/04_tecnicos.py",  "👷", "Técnicos",  "Vista del jefe de área"),
    ("pages/05_mis_obras.py", "🗂", "Mis obras", "Cola de trabajo del técnico"),
]

cols = st.columns(len(SECCIONES))
for col, (ruta, icono, titulo, desc) in zip(cols, SECCIONES):
    with col.container(border=True):
        st.markdown(f"### {icono} {titulo}")
        st.caption(desc)
        st.page_link(ruta, label="Abrir →")

st.divider()
st.caption(
    "El sistema VIVSO unifica tres sistemas legacy (App GPS, VISOC y GEDO) para el "
    "seguimiento del programa de viviendas sociales asociado al Programa Chagas. "
    "Flujo de datos: API Java → ETL Python → Base local → este panel."
)
