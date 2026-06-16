"""
Vista del jefe de área: rendimiento comparativo del equipo técnico.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.components.criterios import nota_criterio

st.set_page_config(page_title="Equipo técnico — VIVSO", layout="wide")
st.title("👷 Equipo técnico — Vista del jefe de área")

_ROOT = Path(__file__).resolve().parent.parent.parent
DATA  = _ROOT / "data"


@st.cache_data(ttl=120)
def cargar():
    # Usa el dataset procesado si existe; si no, cae al sintético (mismas columnas base)
    procesadas = DATA / "viviendas_procesadas.csv"
    viv  = pd.read_csv(procesadas if procesadas.exists() else DATA / "viviendas_sinteticas.csv")
    tec  = pd.read_csv(DATA / "tecnicos.csv")
    asig = pd.read_csv(DATA / "asignaciones.csv")
    vis  = pd.read_csv(DATA / "visitas.csv")
    col  = "avance_obra" if "avance_obra" in viv.columns else "avanceObra"
    return viv, tec, asig, vis, col


df_viv, df_tec, df_asig, df_vis, COL_AV = cargar()

# ── Tabla de rendimiento consolidada ─────────────────────────────────────
asig_c = df_asig.groupby("tecnico_id").size().reset_index(name="obras")
vis_c  = df_vis.groupby("tecnico_id").size().reset_index(name="visitas")
prim_c = df_vis[df_vis["tipo"]=="primera"].groupby("tecnico_id").size().reset_index(name="primeras")
seg_c  = df_vis[df_vis["tipo"]=="segunda"].groupby("tecnico_id").size().reset_index(name="segundas")

base  = df_tec[["id","nombre","apellido","departamentos"]]
carga = (
    base
    .merge(asig_c, left_on="id", right_on="tecnico_id", how="left").drop(columns="tecnico_id")
    .merge(vis_c,  left_on="id", right_on="tecnico_id", how="left").drop(columns="tecnico_id")
    .merge(prim_c, left_on="id", right_on="tecnico_id", how="left").drop(columns="tecnico_id")
    .merge(seg_c,  left_on="id", right_on="tecnico_id", how="left").drop(columns="tecnico_id")
    .fillna(0)
)
for c in ["obras","visitas","primeras","segundas"]:
    carga[c] = carga[c].astype(int)

carga["sin_visita"]  = carga["obras"] - carga["primeras"]
carga["cobertura"]   = (carga["primeras"] / carga["obras"].replace(0,1) * 100).round(1)
carga["nombre_c"]    = carga["apellido"] + ", " + carga["nombre"]

# ── KPIs globales ─────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Técnicos activos",   int(df_tec["activo"].sum()))
c2.metric("Visitas realizadas", len(df_vis))
c3.metric("Cobertura promedio", f"{carga['cobertura'].mean():.1f}%")
c4.metric("Obras sin visitar",  int(carga["sin_visita"].sum()), delta_color="inverse")

nota_criterio("tecnicos")

st.divider()

# ── Gráficos comparativos ─────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    fig = go.Figure()
    fig.add_bar(name="Primera visita", y=carga["nombre_c"], x=carga["primeras"],
                orientation="h", marker_color="#22c55e")
    fig.add_bar(name="Segunda visita", y=carga["nombre_c"], x=carga["segundas"],
                orientation="h", marker_color="#3b82f6")
    fig.add_bar(name="Sin visitar",    y=carga["nombre_c"], x=carga["sin_visita"],
                orientation="h", marker_color="#ef4444")
    fig.update_layout(barmode="stack", title="Cobertura de visitas",
                      xaxis_title="Obras", yaxis_title="",
                      legend=dict(orientation="h", y=-0.15), height=350)
    st.plotly_chart(fig, width='stretch')

with col2:
    fig2 = px.scatter(
        carga, x="obras", y="cobertura", text="apellido",
        title="Carga vs. cobertura de visitas",
        labels={"obras": "Obras asignadas", "cobertura": "Cobertura (%)"},
        color="cobertura",
        color_continuous_scale=["#ef4444","#f59e0b","#22c55e"],
        range_color=[0, 100],
        size=[12]*len(carga),
    )
    fig2.add_hline(y=70, line_dash="dash", line_color="#94a3b8",
                   annotation_text="70% objetivo")
    fig2.update_traces(textposition="top center")
    fig2.update_layout(coloraxis_showscale=False, height=350)
    st.plotly_chart(fig2, width='stretch')

# ── Discrepancias ONG vs. técnico ─────────────────────────────────────────
st.subheader("Discrepancias: lo que reporta la ONG vs. lo que verifica el técnico")
st.caption(
    "Valores positivos = la ONG reportó más avance del que el técnico encontró. "
    "Una discrepancia alta y consistente puede indicar sobreestimación deliberada."
)

df_v = df_vis.merge(df_tec[["id","apellido"]], left_on="tecnico_id", right_on="id", how="left")

disc_tec = (
    df_v.groupby("apellido")["diferencia_ong"]
    .agg(["mean","std","count"])
    .round(2)
    .reset_index()
    .rename(columns={"mean":"promedio","std":"desvío","count":"visitas"})
    .sort_values("promedio", ascending=False)
)

col3, col4 = st.columns(2)
with col3:
    fig3 = px.bar(
        disc_tec, x="apellido", y="promedio",
        error_y="desvío",
        title="Discrepancia promedio por técnico",
        color="promedio",
        color_continuous_scale=["#22c55e","#f59e0b","#ef4444"],
        labels={"promedio": "Diferencia promedio (puntos)", "apellido": ""},
    )
    fig3.add_hline(y=0, line_color="#64748b", line_dash="dash")
    fig3.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig3, width='stretch')

with col4:
    fig4 = px.histogram(
        df_v, x="diferencia_ong", nbins=30,
        color="apellido",
        title="Distribución de discrepancias",
        labels={"diferencia_ong": "Diferencia (puntos)"},
        barmode="overlay", opacity=0.6,
    )
    fig4.add_vline(x=0, line_color="#64748b", line_dash="dash")
    st.plotly_chart(fig4, width='stretch')

# ── Tabla de rendimiento ───────────────────────────────────────────────────
st.subheader("Tabla de rendimiento")
st.dataframe(
    carga[["nombre_c","departamentos","obras","primeras","segundas","sin_visita","cobertura"]]
    .rename(columns={
        "nombre_c": "Técnico", "departamentos": "Zona",
        "obras": "Asignadas", "primeras": "1ª visita",
        "segundas": "2ª visita", "sin_visita": "Sin visitar", "cobertura": "Cobertura %"
    })
    .sort_values("Cobertura %"),
    width='stretch', hide_index=True,
)

# ── Alertas: obras activas con riesgo alto sin ninguna visita ─────────────
st.subheader("⚠️ Alertas — obras en riesgo sin visitar")
visitadas   = set(df_vis["vivienda_id"].unique())
sin_visita  = df_viv[
    df_viv["estado"].isin(["Iniciada","Avanzada"]) &
    ~df_viv["num_exp"].isin(visitadas) &
    (df_viv["nivel_riesgo"] == "alto")
]
if sin_visita.empty:
    st.success("Todas las obras en riesgo alto han sido visitadas.")
else:
    st.error(f"{len(sin_visita)} obra(s) en riesgo alto sin ninguna visita técnica")
    cols_a = [c for c in ["num_exp","localidad","departamento",COL_AV,"dias_activa"] if c in sin_visita.columns]
    st.dataframe(sin_visita[cols_a].sort_values("dias_activa", ascending=False),
                 width='stretch', hide_index=True)
