"""
Generador de rutas para viajes de técnicos — componente extra, fuera de la
obligación de PP3 (docs/supuestos-abiertos.md §1).
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.criterios import nota_criterio
from rutas.parametros import (
    HORAS_JORNADA,
    MODO_MEZCLA,
    MODO_SOLO_URGENTES,
    PLANTILLAS,
)
from rutas.planificador import Viaje, armar_viaje, simular_proximos_viajes
from rutas.prioridad import clasificar_pendiente

st.set_page_config(page_title="Rutas — VIVSO", layout="wide")

C = {"base": "#4f46e5", "ok": "#10b981", "medio": "#f59e0b",
     "alerta": "#f43f5e", "neutro": "#94a3b8"}
COLORES_DIA = ["#4f46e5", "#10b981", "#f59e0b", "#ec4899", "#0ea5e9", "#a855f7"]

st.title("🗺️ Generador de rutas")
st.caption(
    "Un técnico visita obras en varios departamentos, muy separados entre sí. En vez de "
    "un viaje de ida y vuelta por cada una, esto arma un único viaje de varios días que "
    "encadena las visitas pendientes en una ruta eficiente — priorizando las urgentes, y "
    "aprovechando el trayecto para sumar pendientes de paso."
)
st.warning(
    "**Componente extra, fuera de la obligación de PP3.** No hay red vial real: la "
    "distancia se aproxima con línea recta corregida por un factor de ruta (`[R2]` en "
    "`rutas/parametros.py`) — los kilómetros y horas son una estimación, no un cálculo "
    "sobre caminos reales.",
    icon="🧭",
)


@st.cache_data(ttl=120)
def cargar():
    viv  = pd.read_csv("data/viviendas_sinteticas.csv")
    tec  = pd.read_csv("data/tecnicos.csv")
    asig = pd.read_csv("data/asignaciones.csv")
    vis  = pd.read_csv("data/visitas.csv")
    return viv, tec, asig, vis


df_viv, df_tec, df_asig, df_vis = cargar()

# ── Selector de técnico (mismo patrón que Mis obras) ───────────────────────
nombres = df_tec.apply(lambda r: f"{r['apellido']}, {r['nombre']}", axis=1).tolist()
sel = st.sidebar.selectbox("Técnico", nombres)
tec_row = df_tec[df_tec.apply(
    lambda r: f"{r['apellido']}, {r['nombre']}" == sel, axis=1
)].iloc[0]
TECNICO_ID = int(tec_row["id"])
DEPARTAMENTOS = tec_row["departamentos"]

st.sidebar.markdown(f"**Zona:** {DEPARTAMENTOS}")

plantilla = st.sidebar.selectbox(
    "Plantilla de viaje", PLANTILLAS, format_func=lambda p: p["nombre"],
    help="'2 y 1' = 2 días, 1 noche: ida y vuelta corta, sin día completo en el medio. "
         "'3 y 2' = 3 días, 2 noches: salida, 1 día completo en la zona, regreso.",
)
modo_label = st.sidebar.radio(
    "Selección de visitas",
    ["Mezcla (urgentes + de paso)", "Solo urgentes"],
    help="Mezcla completa el viaje con pendientes no urgentes que queden cerca de la "
         "ruta ya armada. Solo urgentes ignora esas oportunidades.",
)
modo = MODO_MEZCLA if modo_label.startswith("Mezcla") else MODO_SOLO_URGENTES

# ── Armar el viaje ──────────────────────────────────────────────────────────
mis_ids = df_asig[df_asig["tecnico_id"] == TECNICO_ID]["vivienda_id"]
mis_viv = df_viv[df_viv["num_exp"].isin(mis_ids)].copy()
vis_tec = df_vis[df_vis["tecnico_id"] == TECNICO_ID]
mis_viv["visitas"] = mis_viv["num_exp"].map(vis_tec.groupby("vivienda_id").size()) \
                                        .fillna(0).astype(int)
mis_viv["estado_visita"] = mis_viv.apply(clasificar_pendiente, axis=1)

viaje: Viaje = armar_viaje(mis_viv, DEPARTAMENTOS, sel, plantilla, modo)

if not viaje.paradas:
    st.info(f"{sel} no tiene visitas pendientes en este momento — nada que rutear.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Paradas", len(viaje.paradas))
k2.metric("Urgentes", viaje.urgentes_cubiertas,
          delta=f"{viaje.urgentes_pendientes_fuera} quedan afuera", delta_color="off")
k3.metric("De paso (no urgentes)", viaje.no_urgentes_cubiertas)
k4.metric("Km totales", f"{viaje.km_totales:.0f} km")
k5.metric("Horas ahorradas vs. visitar una por una", f"{viaje.horas_ahorradas:.1f} h",
          help=f"Viaje agrupado: {viaje.horas_totales:.1f} h · "
               f"Una por una: {viaje.horas_individual:.1f} h")

nota_criterio("rutas")

st.divider()

# ── Mapa de la ruta ──────────────────────────────────────────────────────────
st.subheader("Ruta")
puntos_todos = [viaje.base] + viaje.paradas
fig = go.Figure()

punto_actual = viaje.base
for i, dia in enumerate(viaje.dias):
    if not dia.paradas:
        continue
    secuencia = [punto_actual] + dia.paradas
    color = COLORES_DIA[i % len(COLORES_DIA)]
    fig.add_trace(go.Scattermap(
        lat=[p.lat for p in secuencia], lon=[p.lng for p in secuencia],
        mode="lines+markers",
        line=dict(width=3, color=color),
        marker=dict(size=[9] + [13 if p.urgente else 9 for p in dia.paradas],
                    color=color),
        text=[p.localidad for p in secuencia],
        customdata=[[p.num_exp or "(base)", p.nivel_riesgo or "-",
                     "urgente" if p.urgente else "de paso"] for p in secuencia],
        hovertemplate="<b>%{customdata[0]}</b><br>%{text}<br>"
                      "riesgo=%{customdata[1]} · %{customdata[2]}<extra></extra>",
        name=f"Día {dia.numero}",
    ))
    punto_actual = dia.paradas[-1]

# Base como marcador aparte, bien visible
fig.add_trace(go.Scattermap(
    lat=[viaje.base.lat], lon=[viaje.base.lng], mode="markers",
    marker=dict(size=16, color="#1e293b", symbol="star"),
    text=[viaje.base.localidad], hovertemplate="<b>Base</b><br>%{text}<extra></extra>",
    name="Base",
))

lats = [p.lat for p in puntos_todos]
lngs = [p.lng for p in puntos_todos]
fig.update_layout(
    map=dict(
        style="carto-positron",
        center=dict(lat=sum(lats) / len(lats), lon=sum(lngs) / len(lngs)),
        zoom=8,
    ),
    margin=dict(l=0, r=0, t=0, b=0), height=480,
    legend=dict(orientation="h", y=-0.05),
)
st.plotly_chart(fig, width="stretch")
st.caption(
    "El tamaño del punto indica urgencia (grande = urgente). La estrella es la base del "
    "técnico. Cada color es un día distinto del viaje."
)

# ── Itinerario día por día ──────────────────────────────────────────────────
st.subheader("Itinerario")
for dia in viaje.dias:
    pernocte = f"pernocta en **{dia.pernocta_en.localidad}**" if dia.pernocta_en else "vuelve a la base"
    with st.expander(
        f"Día {dia.numero} — {len(dia.paradas)} paradas · "
        f"{dia.horas_usadas:.1f} / {dia.presupuesto:.1f} h · {pernocte}",
        expanded=(dia.numero == 1),
    ):
        if dia.paradas:
            tabla = pd.DataFrame([{
                "Obra": p.num_exp, "Localidad": p.localidad,
                "Urgencia": "🔴 Urgente" if p.urgente else "🟢 De paso",
                "Riesgo": p.nivel_riesgo, "Estado": p.estado_visita,
            } for p in dia.paradas])
            st.dataframe(tabla, width="stretch", hide_index=True)
        else:
            st.caption("Sin paradas este día.")

# ── Próximos viajes ──────────────────────────────────────────────────────────
st.divider()
st.subheader("Próximos viajes para vaciar el backlog actual")
st.caption(f"Simula viajes consecutivos con la misma plantilla, sin repetir obras ya cubiertas.")

viajes_futuros = simular_proximos_viajes(mis_viv, DEPARTAMENTOS, sel, plantilla, modo,
                                         max_viajes=6)
resumen = pd.DataFrame([{
    "Viaje": i, "Paradas": len(v.paradas), "Urgentes": v.urgentes_cubiertas,
    "De paso": v.no_urgentes_cubiertas, "Km": round(v.km_totales),
    "Horas": round(v.horas_totales, 1),
} for i, v in enumerate(viajes_futuros, start=1)])
st.dataframe(resumen, width="stretch", hide_index=True)

total_paradas = sum(len(v.paradas) for v in viajes_futuros)
total_horas   = sum(v.horas_totales for v in viajes_futuros)
total_ahorro  = sum(v.horas_ahorradas for v in viajes_futuros)
st.markdown(
    f"**{len(viajes_futuros)} viajes** cubren **{total_paradas} obras** en "
    f"**{total_horas:.1f} h**. Visitándolas una por una habría costado "
    f"{total_horas + total_ahorro:.1f} h → **{total_ahorro:.1f} h ahorradas** "
    f"({total_ahorro / HORAS_JORNADA:.1f} jornadas de {HORAS_JORNADA:.0f} h)."
)
