import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dashboard.components.data_loader import cargar_viviendas
from dashboard.components.criterios import nota_criterio

st.set_page_config(page_title="Evolución — VIVSO", layout="wide")
st.title("📈 Evolución del programa")
st.markdown(
    "Series de tiempo del programa: ritmo de inicios, finalizaciones, obras "
    "acumuladas en curso (backlog) y tasa de finalización por trimestre."
)

df = cargar_viviendas()
TERMINADAS = ["Finalizada", "Adjudicada"]

# ── Series mensuales ───────────────────────────────────────────────────────
# fecha_inic / fecha_fin vienen como "DD-MM-YYYY".
ini = pd.to_datetime(df["fecha_inic"], format="%d-%m-%Y", errors="coerce")
fin = pd.to_datetime(df["fecha_fin"],  format="%d-%m-%Y", errors="coerce")

m_ini = ini.dropna().dt.to_period("M").value_counts()
m_fin = fin.dropna().dt.to_period("M").value_counts()

# Índice mensual continuo que cubre todo el rango (sin huecos).
inicio = min(m_ini.index.min(), m_fin.index.min())
fin_p  = max(m_ini.index.max(), m_fin.index.max())
meses  = pd.period_range(inicio, fin_p, freq="M")

serie = pd.DataFrame({
    "iniciadas":  m_ini.reindex(meses, fill_value=0),
    "terminadas": m_fin.reindex(meses, fill_value=0),
})
serie["backlog"] = (serie["iniciadas"].cumsum() - serie["terminadas"].cumsum())
serie["mes"] = meses.to_timestamp()

# ── KPIs ───────────────────────────────────────────────────────────────────
mes_pico = m_ini.idxmax()
backlog_actual = int(serie["backlog"].iloc[-1])
tasa_global = df["estado"].isin(TERMINADAS).mean() * 100

k1, k2, k3, k4 = st.columns(4)
k1.metric("Meses con actividad", int((serie["iniciadas"] > 0).sum()))
k2.metric("Mes pico de inicios", str(mes_pico), delta=f"{int(m_ini.max())} obras",
          delta_color="off")
k3.metric("En obra (backlog actual)", f"{backlog_actual:,}".replace(",", "."))
k4.metric("Tasa de finalización", f"{tasa_global:.1f}%")

nota_criterio("evolucion")

st.divider()

# ── Iniciadas vs terminadas por mes ────────────────────────────────────────
st.subheader("Ritmo de inicios y finalizaciones")
serie_long = serie.melt(
    id_vars="mes", value_vars=["iniciadas", "terminadas"],
    var_name="tipo", value_name="cantidad",
)
fig = px.line(
    serie_long, x="mes", y="cantidad", color="tipo",
    color_discrete_map={"iniciadas": "#3b82f6", "terminadas": "#22c55e"},
    labels={"mes": "", "cantidad": "Obras", "tipo": ""},
    markers=False,
)
fig.update_traces(line=dict(width=2))
fig.update_layout(height=360, margin=dict(t=20, b=10, l=10, r=10),
                  legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig, width="stretch")

# ── Backlog acumulado ──────────────────────────────────────────────────────
col_back, col_trim = st.columns(2)

with col_back:
    st.subheader("Obras en curso acumuladas")
    st.caption("Inicios acumulados menos finalizaciones acumuladas: cuántas obras "
               "estaban abiertas en cada momento.")
    fig2 = px.area(
        serie, x="mes", y="backlog",
        labels={"mes": "", "backlog": "Obras en curso"},
        color_discrete_sequence=["#6366f1"],
    )
    fig2.update_traces(line=dict(width=2), fillcolor="rgba(99,102,241,0.15)")
    fig2.update_layout(height=340, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig2, width="stretch")

# ── Tasa de finalización por trimestre ─────────────────────────────────────
with col_trim:
    st.subheader("Inicios vs. finalizaciones por trimestre")
    st.caption("Barras: obras del trimestre. Línea: finalizaciones sobre inicios (%).")
    q_ini = ini.dropna().dt.to_period("Q").value_counts()
    q_fin = fin.dropna().dt.to_period("Q").value_counts()
    trimestres = pd.period_range(min(q_ini.index.min(), q_fin.index.min()),
                                 max(q_ini.index.max(), q_fin.index.max()), freq="Q")
    qt = pd.DataFrame({
        "iniciadas":  q_ini.reindex(trimestres, fill_value=0),
        "terminadas": q_fin.reindex(trimestres, fill_value=0),
    })
    qt["tasa"] = (qt["terminadas"] / qt["iniciadas"].where(qt["iniciadas"] > 0) * 100).round(0)
    etiquetas = [str(t) for t in trimestres]

    fig3 = go.Figure()
    fig3.add_bar(x=etiquetas, y=qt["iniciadas"], name="Iniciadas", marker_color="#93c5fd")
    fig3.add_bar(x=etiquetas, y=qt["terminadas"], name="Terminadas", marker_color="#22c55e")
    fig3.add_trace(go.Scatter(
        x=etiquetas, y=qt["tasa"], name="Tasa finalización (%)",
        yaxis="y2", mode="lines+markers", line=dict(color="#ef4444", width=2),
    ))
    fig3.update_layout(
        height=340, margin=dict(t=10, b=10, l=10, r=10), barmode="group",
        yaxis=dict(title="Obras"),
        yaxis2=dict(title="%", overlaying="y", side="right", range=[0, 100], showgrid=False),
        legend=dict(orientation="h", y=1.15),
    )
    st.plotly_chart(fig3, width="stretch")
