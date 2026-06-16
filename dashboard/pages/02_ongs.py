import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dashboard.components.data_loader import cargar_viviendas, cargar_organizaciones
from dashboard.components.criterios import nota_criterio

st.set_page_config(page_title="ONGs — VIVSO", layout="wide")
st.title("🤝 ONGs gestoras")

df  = cargar_viviendas()
orgs = cargar_organizaciones()

if orgs.empty:
    st.warning("No se encontró el archivo de organizaciones.")
    st.stop()

nombre_map = dict(zip(orgs["cuit"], orgs["nombre"])) if not orgs.empty else {}

# ── KPIs globales ─────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("ONGs registradas",  len(orgs))
c2.metric("ONGs activas",      int((orgs["estado"] == "ACTIVA").sum()))
c3.metric("Viviendas con ONG", int(df["cuit_org"].notna().sum()))
c4.metric("Sin ONG asignada",  int(df["cuit_org"].isna().sum()))

nota_criterio("ongs")

st.divider()

# ── Rendimiento comparativo ───────────────────────────────────────────────
st.subheader("Rendimiento comparativo por organización")

df_org = df[df["cuit_org"].notna()].copy()
df_org["nombre_org"] = df_org["cuit_org"].map(nombre_map).fillna(df_org["cuit_org"])
df_org["org_corta"]  = df_org["nombre_org"].str[:32]

rendimiento = (
    df_org.groupby("org_corta")
    .agg(
        obras        =("avance_obra", "count"),
        avance_prom  =("avance_obra", "mean"),
        riesgo_alto  =("nivel_riesgo", lambda x: (x == "alto").sum()),
        riesgo_medio =("nivel_riesgo", lambda x: (x == "medio").sum()),
        terminadas   =("estado", lambda x: x.isin(["Finalizada","Adjudicada"]).sum()),
        dias_prom    =("dias_activa", "mean"),
    )
    .round(1)
    .reset_index()
    .sort_values("avance_prom", ascending=False)
)

col_a, col_b = st.columns(2)

with col_a:
    promedio_general = df["avance_obra"].mean()
    fig = px.bar(
        rendimiento,
        x="avance_prom", y="org_corta",
        orientation="h",
        title="Avance promedio de obras activas",
        color="avance_prom",
        color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
        range_color=[0, 100],
        labels={"avance_prom": "Avance (%)", "org_corta": ""},
    )
    fig.add_vline(x=promedio_general, line_dash="dash", line_color="#64748b",
                  annotation_text=f"Promedio: {promedio_general:.1f}%",
                  annotation_position="top right")
    fig.update_layout(coloraxis_showscale=False, margin=dict(l=0))
    st.plotly_chart(fig, width='stretch')

with col_b:
    fig2 = px.bar(
        rendimiento,
        x="org_corta",
        y=["riesgo_alto", "riesgo_medio"],
        title="Obras en riesgo por organización",
        color_discrete_map={"riesgo_alto": "#ef4444", "riesgo_medio": "#f59e0b"},
        labels={"value": "Cantidad", "org_corta": "", "variable": "Nivel"},
        barmode="stack",
    )
    fig2.update_layout(margin=dict(l=0))
    st.plotly_chart(fig2, width='stretch')

# ── Detalle por ONG seleccionada ──────────────────────────────────────────
st.subheader("Detalle por organización")

ong_sel = st.selectbox(
    "Seleccioná una ONG",
    options=rendimiento["org_corta"].tolist(),
)

df_sel = df_org[df_org["org_corta"] == ong_sel]
info_cuit = df_sel["cuit_org"].iloc[0] if len(df_sel) else None
info_org  = orgs[orgs["cuit"] == info_cuit].iloc[0] if info_cuit and not orgs.empty else None

if info_org is not None:
    with st.expander("Datos de la organización", expanded=True):
        i1, i2, i3 = st.columns(3)
        i1.markdown(f"**Nombre:** {info_org.get('nombre','—')}")
        i1.markdown(f"**Tipo:** {info_org.get('tipo','—')}")
        i2.markdown(f"**Presidente:** {info_org.get('presidente','—')}")
        i2.markdown(f"**DNI:** {info_org.get('dni_presidente','—')}")
        i3.markdown(f"**Contacto:** {info_org.get('contacto','—')}")
        i3.markdown(f"**Estado:** {info_org.get('estado','—')}")

# KPIs de la ONG seleccionada
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Obras totales",   len(df_sel))
m2.metric("Avance promedio", f"{df_sel['avance_obra'].mean():.1f}%")
m3.metric("Terminadas",      int(df_sel["estado"].isin(["Finalizada","Adjudicada"]).sum()))
m4.metric("Riesgo alto",     int((df_sel["nivel_riesgo"] == "alto").sum()), delta_color="inverse")
m5.metric("Días prom.",      f"{df_sel['dias_activa'].mean():.0f}")

# Distribución de estados de esta ONG
col_p, col_q = st.columns(2)
with col_p:
    est_sel = df_sel["estado"].value_counts().reset_index()
    est_sel.columns = ["estado", "cantidad"]
    fig3 = px.pie(
        est_sel, names="estado", values="cantidad",
        title=f"Estados de obra — {ong_sel[:25]}",
        color="estado",
        color_discrete_map={"Iniciada":"#f59e0b","Avanzada":"#3b82f6",
                             "Finalizada":"#22c55e","Adjudicada":"#6366f1"},
        hole=0.4,
    )
    st.plotly_chart(fig3, width='stretch')

with col_q:
    fig4 = px.histogram(
        df_sel, x="avance_obra", nbins=20,
        title="Distribución del avance",
        color_discrete_sequence=["#2563eb"],
        labels={"avance_obra": "Avance (%)"},
    )
    st.plotly_chart(fig4, width='stretch')

# Tabla de obras
st.dataframe(
    df_sel[["num_exp","localidad","estado","avance_obra","nivel_riesgo","dias_activa","representante"]]
    .sort_values("nivel_riesgo", key=lambda x: x.map({"alto":0,"medio":1,"bajo":2})),
    width='stretch',
    hide_index=True,
)
