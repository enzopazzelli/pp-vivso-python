import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from dashboard.components.data_loader import cargar_viviendas, cargar_avance_rubros
from dashboard.components.criterios import nota_criterio

st.set_page_config(page_title="Minería — VIVSO", layout="wide")
st.title("🔬 Minería de datos")
st.markdown(
    "Modelo de riesgo, desglose del AFO por rubros de construcción y tiempos de ejecución."
)

df = cargar_viviendas()
df_rubros = cargar_avance_rubros()

RUBROS_NOMBRES = {
    1:"Terreno y limpieza", 2:"Excavación e impermeabilización", 3:"Mampostería hasta dintel",
    4:"Mampostería cerámico/Block", 5:"Encadenado", 6:"Revoque interior", 7:"Revoque exterior",
    8:"Cielorraso con aislante", 9:"Construcción de cielorrasos", 10:"Carpintería",
    11:"Instalación de agua", 12:"Instalación eléctrica", 13:"Instalación sanitaria",
    14:"Revestimiento exterior", 15:"Varios",
}

# ── Tabs ──────────────────────────────────────────────────────────────────
tab_riesgo, tab_rubros, tab_tiempo = st.tabs(
    ["⚠️ Modelo de riesgo", "🧱 Rubros AFO", "⏱ Tiempos de ejecución"]
)

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Modelo de riesgo
# ════════════════════════════════════════════════════════════════════════════
with tab_riesgo:
    st.subheader("Obras en riesgo de demora")
    st.markdown(
        "**Criterio:** obra activa que **superó el plazo contractual de 90 días** y todavía no está por terminar.  \n"
        "🔴 Riesgo alto: pasó los 90 días con avance < 30% · 🟡 Riesgo medio: pasó los 90 días con avance 30–80%."
    )

    total = len(df)
    n_alto  = int((df["nivel_riesgo"] == "alto").sum())
    n_medio = int((df["nivel_riesgo"] == "medio").sum())
    n_bajo  = int((df["nivel_riesgo"] == "bajo").sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Riesgo alto",  n_alto,  delta=f"{n_alto/total*100:.1f}% del total",  delta_color="inverse")
    c2.metric("Riesgo medio", n_medio, delta=f"{n_medio/total*100:.1f}% del total", delta_color="off")
    c3.metric("Sin riesgo",   n_bajo,  delta=f"{n_bajo/total*100:.1f}% del total",  delta_color="normal")

    nota_criterio("riesgo")

    col_scatter, col_bar = st.columns([3, 2])

    with col_scatter:
        fig = px.scatter(
            df, x="dias_activa", y="avance_obra",
            color="nivel_riesgo",
            color_discrete_map={"bajo":"#22c55e","medio":"#f59e0b","alto":"#ef4444"},
            opacity=0.55,
            hover_data={"num_exp": True, "localidad": True, "estado": True,
                        "dias_activa": True, "avance_obra": True},
            title="Días activa vs. avance de obra",
            labels={"dias_activa": "Días activa", "avance_obra": "Avance (%)",
                    "nivel_riesgo": "Riesgo"},
        )
        fig.add_vline(x=90, line_dash="dash", line_color="#94a3b8",
                      annotation_text="90 días (plazo)")
        fig.add_hline(y=80, line_dash="dash", line_color="#94a3b8",
                      annotation_text="80%")
        st.plotly_chart(fig, width='stretch')

    with col_bar:
        por_depto = (
            df[df["nivel_riesgo"] == "alto"]
            .groupby("departamento").size()
            .reset_index(name="riesgo_alto")
            .sort_values("riesgo_alto", ascending=True)
        )
        fig2 = px.bar(
            por_depto, x="riesgo_alto", y="departamento",
            orientation="h",
            title="Riesgo alto por departamento",
            color="riesgo_alto",
            color_continuous_scale=["#fef9c3","#ef4444"],
            labels={"riesgo_alto": "Obras", "departamento": ""},
        )
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig2, width='stretch')

    st.subheader("Listado de obras en riesgo alto")
    riesgo_alto_df = (
        df[df["nivel_riesgo"] == "alto"]
        [[c for c in ["num_exp","localidad","departamento","estado",
                       "avance_obra","dias_activa","cuit_org"] if c in df.columns]]
        .sort_values("dias_activa", ascending=False)
    )
    st.dataframe(riesgo_alto_df, width='stretch', hide_index=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Rubros AFO
# ════════════════════════════════════════════════════════════════════════════
with tab_rubros:
    st.subheader("Avance Físico de Obra por rubro de construcción")
    st.markdown(
        "El AFO total se calcula como la suma ponderada de 15 rubros de construcción "
        "(sistema legacy VISOC). Este análisis identifica qué etapas son el cuello de botella."
    )
    nota_criterio("rubros")

    if df_rubros.empty:
        st.info("No se encontró `data/avance_rubros.csv`. Ejecutá `python -m synthetic.generate`.")
    else:
        df_r = df_rubros.copy()
        df_r["nombre_rubro"] = df_r["rubro_id"].map(RUBROS_NOMBRES)
        df_r = df_r.merge(
            df[["num_exp", "nivel_riesgo", "estado"]],
            left_on="vivienda_id", right_on="num_exp", how="left"
        )

        # Filtro: solo obras activas para el análisis de cuellos de botella
        activos_ids = df[df["estado"].isin(["Iniciada", "Avanzada"])]["num_exp"]
        dr_act = df_r[df_r["vivienda_id"].isin(activos_ids)]

        prom = (dr_act.groupby(["rubro_id", "nombre_rubro"])["avance_pct"]
                .mean().reset_index().sort_values("rubro_id"))

        color_fn = lambda v: "#22c55e" if v >= 70 else "#f59e0b" if v >= 30 else "#ef4444"
        prom["color"] = prom["avance_pct"].apply(color_fn)

        fig_r = px.bar(
            prom, x="avance_pct", y="nombre_rubro", orientation="h",
            title="Avance promedio por rubro — obras activas (Verde ≥70% | Amarillo 30–70% | Rojo <30%)",
            color="avance_pct",
            color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
            range_color=[0, 100],
            labels={"avance_pct": "Avance promedio (%)", "nombre_rubro": ""},
            text="avance_pct",
        )
        fig_r.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig_r.add_vline(x=70, line_dash="dash", line_color="#64748b", opacity=0.5)
        fig_r.update_layout(coloraxis_showscale=False, height=480)
        st.plotly_chart(fig_r, width='stretch')

        st.divider()
        st.subheader("Avance por rubro según nivel de riesgo")

        prom_riesgo = (df_r.groupby(["rubro_id", "nombre_rubro", "nivel_riesgo"])["avance_pct"]
                       .mean().reset_index())
        prom_riesgo = prom_riesgo.sort_values("rubro_id")

        fig_r2 = px.bar(
            prom_riesgo, x="nombre_rubro", y="avance_pct",
            color="nivel_riesgo",
            barmode="group",
            color_discrete_map={"alto": "#ef4444", "medio": "#f59e0b", "bajo": "#22c55e"},
            title="Las obras en riesgo, ¿están rezagadas en los mismos rubros?",
            labels={"avance_pct": "Avance promedio (%)", "nombre_rubro": "", "nivel_riesgo": "Riesgo"},
        )
        fig_r2.update_layout(xaxis_tickangle=-40, height=420)
        st.plotly_chart(fig_r2, width='stretch')

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Tiempos de ejecución
# ════════════════════════════════════════════════════════════════════════════
with tab_tiempo:
    st.subheader("Tiempos de ejecución de obras terminadas")
    st.markdown(
        "Solo se consideran obras Finalizadas o Adjudicadas. Incluir obras en curso "
        "distorsionaría el promedio ya que su duración real todavía no está definida."
    )
    nota_criterio("tiempos")

    terminadas = df[df["estado"].isin(["Finalizada","Adjudicada"])].copy()

    if terminadas.empty:
        st.info("No hay obras terminadas en el dataset actual.")
    else:
        t1, t2, t3 = st.columns(3)
        t1.metric("Obras analizadas", len(terminadas))
        t2.metric("Promedio",  f"{terminadas['dias_activa'].mean():.0f} días")
        t3.metric("Mediana",   f"{terminadas['dias_activa'].median():.0f} días")

        col_h, col_box = st.columns(2)

        with col_h:
            fig5 = px.histogram(
                terminadas, x="dias_activa", nbins=25,
                title="Distribución del tiempo de ejecución",
                color_discrete_sequence=["#6366f1"],
                labels={"dias_activa": "Días"},
            )
            fig5.add_vline(x=terminadas["dias_activa"].mean(),
                           line_dash="dash", line_color="#ef4444",
                           annotation_text="Promedio")
            st.plotly_chart(fig5, width='stretch')

        with col_box:
            fig6 = px.box(
                terminadas, x="tipo_vivienda", y="dias_activa",
                color="tipo_vivienda",
                title="Duración por tipo de vivienda",
                labels={"dias_activa": "Días", "tipo_vivienda": ""},
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig6.update_layout(showlegend=False)
            st.plotly_chart(fig6, width='stretch')

        fig7 = px.bar(
            terminadas.groupby("clasificacion")["dias_activa"]
            .mean().reset_index().sort_values("dias_activa"),
            x="clasificacion", y="dias_activa",
            title="Duración promedio por clasificación",
            color="dias_activa",
            color_continuous_scale=["#22c55e","#f59e0b","#ef4444"],
            labels={"dias_activa": "Días promedio", "clasificacion": ""},
        )
        fig7.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig7, width='stretch')
