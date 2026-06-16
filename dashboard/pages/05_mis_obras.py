"""
Vista del técnico: sus obras asignadas, visitas pendientes y mapa de su zona.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import plotly.express as px
import pandas as pd
from dashboard.components.criterios import nota_criterio

st.set_page_config(page_title="Mis obras — VIVSO", layout="wide")
st.title("🗂 Mis obras")

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

# ── Selector de técnico (simula login) ────────────────────────────────────
nombres = df_tec.apply(lambda r: f"{r['apellido']}, {r['nombre']}", axis=1).tolist()
sel = st.sidebar.selectbox("Técnico", nombres)
tec_row = df_tec[df_tec.apply(
    lambda r: f"{r['apellido']}, {r['nombre']}" == sel, axis=1
)].iloc[0]
TECNICO_ID = int(tec_row["id"])

st.sidebar.markdown(f"**Zona:** {tec_row['departamentos']}")
st.sidebar.markdown(f"**Email:** {tec_row['email']}")

# ── Cargar datos del técnico ──────────────────────────────────────────────
mis_ids = df_asig[df_asig["tecnico_id"] == TECNICO_ID]["vivienda_id"]
mis_viv = df_viv[df_viv["num_exp"].isin(mis_ids)].copy()

vis_tec     = df_vis[df_vis["tecnico_id"] == TECNICO_ID]
vis_por_viv = vis_tec.groupby("vivienda_id").size()
ultima_vis  = vis_tec.sort_values("fecha").groupby("vivienda_id").last()

mis_viv["visitas"] = mis_viv["num_exp"].map(vis_por_viv).fillna(0).astype(int)
mis_viv["ultima_visita"] = mis_viv["num_exp"].map(ultima_vis["fecha"] if "fecha" in ultima_vis.columns else {})
mis_viv["avance_verificado"] = mis_viv["num_exp"].map(
    ultima_vis["avance_verificado"] if "avance_verificado" in ultima_vis.columns else {}
)

def clasificar_pendiente(row):
    if row["estado"] in ("Finalizada", "Adjudicada"):
        return "Finalizada"
    if row["visitas"] == 0:
        return "Sin visitar"
    if row["visitas"] == 1:
        return "Falta 2da visita"
    return "Completo"

mis_viv["estado_visita"] = mis_viv.apply(clasificar_pendiente, axis=1)

orden_prio  = {"Sin visitar": 0, "Falta 2da visita": 1, "Completo": 2, "Finalizada": 3}
orden_riesgo = {"alto": 0, "medio": 1, "bajo": 2}
mis_viv["_p"] = mis_viv["estado_visita"].map(orden_prio)
mis_viv["_r"] = mis_viv["nivel_riesgo"].map(orden_riesgo).fillna(2)
mis_viv = mis_viv.sort_values(["_p", "_r"])

# ── KPIs del técnico ──────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Obras asignadas",    len(mis_viv))
c2.metric("Sin visitar",        int((mis_viv["estado_visita"] == "Sin visitar").sum()),
          delta_color="inverse")
c3.metric("Falta 2da visita",   int((mis_viv["estado_visita"] == "Falta 2da visita").sum()),
          delta_color="off")
c4.metric("Riesgo alto",        int((mis_viv["nivel_riesgo"] == "alto").sum()),
          delta_color="inverse")
c5.metric("Visitas realizadas", int(mis_viv["visitas"].sum()))

nota_criterio("cobertura", "riesgo")

st.divider()

# ── Cola de prioridad ─────────────────────────────────────────────────────
st.subheader("Cola de trabajo — ordenada por prioridad")
st.caption(
    "Primero aparecen las obras sin visitar, luego las que necesitan segunda visita, "
    "ordenadas dentro de cada grupo por nivel de riesgo."
)

color_estado = {
    "Sin visitar":      "🔴",
    "Falta 2da visita": "🟡",
    "Completo":         "🟢",
    "Finalizada":       "⚫",
}
color_riesgo = {"alto": "🔴", "medio": "🟡", "bajo": "🟢"}

cols_tabla = [c for c in ["num_exp","localidad","estado",COL_AV,
                            "nivel_riesgo","visitas","ultima_visita","estado_visita"]
              if c in mis_viv.columns]
df_mostrar = mis_viv[cols_tabla].copy()
df_mostrar["estado_visita"] = df_mostrar["estado_visita"].apply(
    lambda x: f"{color_estado.get(x,'')} {x}"
)
df_mostrar["nivel_riesgo"] = df_mostrar["nivel_riesgo"].apply(
    lambda x: f"{color_riesgo.get(x,'')} {x}" if pd.notna(x) else x
)
st.dataframe(df_mostrar, width='stretch', hide_index=True)

# ── Distribución de estados de visita ────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    ev = mis_viv["estado_visita"].value_counts().reset_index()
    ev.columns = ["estado", "cantidad"]
    colores_ev = {
        "Sin visitar":      "#ef4444",
        "Falta 2da visita": "#f59e0b",
        "Completo":         "#22c55e",
        "Finalizada":       "#94a3b8",
    }
    fig = px.pie(ev, names="estado", values="cantidad",
                 title="Estado de visitas de mis obras",
                 color="estado", color_discrete_map=colores_ev, hole=0.4)
    st.plotly_chart(fig, width='stretch')

with col_b:
    # Avance ONG vs avance verificado en las obras visitadas
    comparar = mis_viv[mis_viv["avance_verificado"].notna()].copy()
    if not comparar.empty:
        fig2 = px.scatter(
            comparar,
            x=COL_AV, y="avance_verificado",
            color="nivel_riesgo",
            color_discrete_map={"bajo":"#22c55e","medio":"#f59e0b","alto":"#ef4444"},
            hover_data={"num_exp": True, "localidad": True},
            title="Avance reportado (ONG) vs. verificado (técnico)",
            labels={COL_AV: "Avance ONG (%)", "avance_verificado": "Verificado (%)"},
        )
        fig2.add_shape(type="line", x0=0, y0=0, x1=100, y1=100,
                       line=dict(color="#94a3b8", dash="dash"))
        st.plotly_chart(fig2, width='stretch')
    else:
        st.info("Sin datos de verificación aún — realizá tu primera visita.")

# ── Mapa de mi zona ───────────────────────────────────────────────────────
mapa_df = mis_viv.dropna(subset=["lat","lng"]).copy()
if not mapa_df.empty:
    st.subheader("Mapa de mi zona")
    fig3 = px.scatter_map(
        mapa_df, lat="lat", lon="lng",
        color="estado_visita",
        color_discrete_map={
            "Sin visitar":      "#ef4444",
            "Falta 2da visita": "#f59e0b",
            "Completo":         "#22c55e",
            "Finalizada":       "#94a3b8",
        },
        hover_data={"num_exp": True, "localidad": True, COL_AV: True,
                    "nivel_riesgo": True, "lat": False, "lng": False},
        zoom=7, map_style="carto-positron",
        title="Mis obras por estado de visita",
    )
    fig3.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=430)
    st.plotly_chart(fig3, width='stretch')
