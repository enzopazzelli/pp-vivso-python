import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import plotly.express as px
from dashboard.components.data_loader import cargar_viviendas

st.set_page_config(page_title="Viviendas — VIVSO", layout="wide")
st.title("🏘 Viviendas")

df = cargar_viviendas()

# ── Sidebar: filtros ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")

    deptos = st.multiselect(
        "Departamento",
        sorted(df["departamento"].dropna().unique()),
    )
    estados = st.multiselect(
        "Estado",
        sorted(df["estado"].dropna().unique()),
    )
    tipos = st.multiselect(
        "Tipo de vivienda",
        sorted(df["tipo_vivienda"].dropna().unique()),
    )
    riesgo = st.multiselect(
        "Nivel de riesgo",
        ["alto", "medio", "bajo"],
    )
    criterio = st.multiselect(
        "Criterio de inclusión",
        sorted(df["criterio"].dropna().unique()) if "criterio" in df.columns else [],
        help="Inclusion = apta | Exclusion = rechazada | Otro = caso especial",
    )
    avance_min = st.slider("Avance mínimo (%)", 0, 100, 0)

# Aplicar filtros
dff = df.copy()
if deptos:   dff = dff[dff["departamento"].isin(deptos)]
if estados:  dff = dff[dff["estado"].isin(estados)]
if tipos:    dff = dff[dff["tipo_vivienda"].isin(tipos)]
if riesgo:   dff = dff[dff["nivel_riesgo"].isin(riesgo)]
if criterio and "criterio" in dff.columns:
    dff = dff[dff["criterio"].isin(criterio)]
dff = dff[dff["avance_obra"] >= avance_min]

# ── KPIs ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total",          len(dff))
c2.metric("En obra",        int((dff["estado"].isin(["Iniciada","Avanzada"])).sum()))
c3.metric("Terminadas",     int((dff["estado"].isin(["Finalizada","Adjudicada"])).sum()))
c4.metric("Avance promedio",f"{dff['avance_obra'].mean():.1f}%")
c5.metric("Riesgo alto",    int((dff["nivel_riesgo"] == "alto").sum()),
          delta_color="inverse")

st.divider()

# ── Gráficos ──────────────────────────────────────────────────────────────
col_izq, col_der = st.columns(2)

with col_izq:
    por_depto = (
        dff.groupby("departamento").size()
        .reset_index(name="cantidad")
        .sort_values("cantidad")
    )
    fig = px.bar(
        por_depto, x="cantidad", y="departamento", orientation="h",
        title="Viviendas por departamento",
        color="cantidad", color_continuous_scale="Blues",
        labels={"cantidad": "Cantidad", "departamento": ""},
    )
    fig.update_layout(coloraxis_showscale=False, margin=dict(l=0))
    st.plotly_chart(fig, width='stretch')

with col_der:
    if "criterio" in dff.columns:
        por_criterio = dff["criterio"].value_counts().reset_index()
        por_criterio.columns = ["criterio", "cantidad"]
        fig2 = px.bar(
            por_criterio, x="criterio", y="cantidad",
            title="Viviendas por criterio de inclusión",
            color="criterio",
            color_discrete_map={
                "Inclusion": "#22c55e", "Exclusion": "#ef4444", "Otro": "#3b82f6"
            },
            labels={"criterio": "", "cantidad": "Cantidad"},
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, width='stretch')
    else:
        colores_estado = {
            "Iniciada": "#f59e0b", "Avanzada": "#3b82f6",
            "Finalizada": "#22c55e", "Adjudicada": "#6366f1",
        }
        por_estado = dff["estado"].value_counts().reset_index()
        por_estado.columns = ["estado", "cantidad"]
        fig2 = px.pie(
            por_estado, names="estado", values="cantidad",
            title="Distribución por estado",
            color="estado", color_discrete_map=colores_estado,
            hole=0.4,
        )
        st.plotly_chart(fig2, width='stretch')

# ── Mapa ──────────────────────────────────────────────────────────────────
mapa_df = dff.dropna(subset=["lat", "lng"]).copy()
if not mapa_df.empty:
    st.subheader(f"Mapa — {len(mapa_df)} viviendas con coordenadas GPS")
    fig_mapa = px.scatter_map(
        mapa_df,
        lat="lat", lon="lng",
        color="nivel_riesgo",
        color_discrete_map={"bajo": "#22c55e", "medio": "#f59e0b", "alto": "#ef4444"},
        hover_data={"num_exp": True, "localidad": True, "avance_obra": True,
                    "estado": True, "lat": False, "lng": False},
        zoom=6,
        map_style="carto-positron",
        title="Distribución geográfica por nivel de riesgo",
    )
    fig_mapa.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=450)
    st.plotly_chart(fig_mapa, width='stretch')
else:
    st.info("Sin coordenadas GPS en los registros filtrados.")

# ── Tabla ─────────────────────────────────────────────────────────────────
st.subheader("Detalle de viviendas")
cols_tabla = [c for c in ["num_exp", "localidad", "departamento",
                            "estado", "avance_obra", "nivel_riesgo",
                            "tipo_vivienda", "representante"] if c in dff.columns]
st.dataframe(
    dff[cols_tabla].sort_values("avance_obra"),
    width='stretch',
    hide_index=True,
)
