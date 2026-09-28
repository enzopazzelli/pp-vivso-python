"""
Vidriera de la capa de datos propia (Planes 1-3): importa los reportes reales de VISOC,
los valida contra sus propios totales y calcula indicadores — ver docs/como-funciona-la-capa-de-datos.md.

Esta página es la única del dashboard que puede mostrar datos reales (según la fuente elegida). El
resto de las páginas sigue usando exclusivamente el modelo simulado de PP2, sin cambios.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from datos.fuentes.registro import FUENTES_VALIDAS, obtener_fuente
from datos.indicadores.registro import calcular_todos

st.set_page_config(page_title="Datos reales — VIVSO", page_icon="🗄️", layout="wide")

C = {"base": "#4f46e5", "ok": "#10b981", "medio": "#f59e0b", "alerta": "#f43f5e", "neutro": "#94a3b8"}
COLOR_CAPACIDAD = {"disponible": C["ok"], "parcial": C["medio"], "no_disponible": C["neutro"]}
ETIQUETA_FUENTE = {"propia": "Base propia (reportes importados)", "simulada": "Datos simulados de PP2",
                   "json_prueba": "JSON de prueba (mínimo, sin PDF ni base)"}

st.title("🗄️ Datos reales — capa de datos propia")
st.caption(
    "Desde el 26 de septiembre de 2026 el equipo construye, además del modelo simulado, un camino "
    "para cargar los reportes reales que exporta VISOC (PDF), anonimizados y validados contra sus "
    "propios totales, con indicadores calculados sobre esa base. El resto del dashboard no cambió: "
    "sigue mostrando el modelo simulado de PP2, como siempre."
)

fuente_elegida = st.radio(
    "Fuente de datos", FUENTES_VALIDAS, format_func=lambda f: ETIQUETA_FUENTE[f], horizontal=True,
    help="«Propia» necesita reportes ya importados (`python -m datos.importar`); si no hay ninguno, "
        "usá «Simulada» o «JSON de prueba» para ver el panel funcionando igual.",
)
fuente = obtener_fuente(fuente_elegida)

st.divider()

# ── Estado de la fuente elegida ─────────────────────────────────────────────
try:
    capacidades = fuente.capacidades()
except RuntimeError as error:
    st.info(f"ℹ️ {error}")
    st.stop()

cols = st.columns(len(capacidades))
for col, (coleccion, estado) in zip(cols, capacidades.items()):
    disponible = estado["disponible"]
    col.metric(coleccion.replace("_", " ").capitalize(), "con datos" if disponible else "vacía")

st.divider()

# ── Indicadores ──────────────────────────────────────────────────────────
st.subheader("Indicadores")
st.caption(
    "Cada uno indica su **confianza** (qué tan seguro está el equipo de lo que sabe de ese reporte) "
    "y su **capacidad** con la fuente elegida: disponible, parcial (falta algo) o no disponible."
)

try:
    indicadores = calcular_todos(fuente)
except RuntimeError as error:
    st.info(f"ℹ️ {error}")
    st.stop()


def _grafico_barras(valores: dict, titulo: str):
    if not valores:
        st.caption("Sin datos para graficar.")
        return
    datos = pd.DataFrame({"categoría": list(map(str, valores.keys())), "cantidad": list(valores.values())})
    fig = px.bar(datos, x="categoría", y="cantidad", title=titulo, color_discrete_sequence=[C["base"]])
    fig.update_layout(height=280, margin=dict(t=40, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")


def _mostrar_valor(indicador) -> None:
    """Cada indicador tiene una forma distinta de `valor`; se dibuja según su código, y si es uno
    que todavía no tiene un gráfico propio, se muestra tal cual en crudo (nunca se rompe la página)."""
    v = indicador.valor
    if indicador.codigo == "viviendas_por_clasificacion_tipo_dormitorios":
        c1, c2, c3 = st.columns(3)
        with c1:
            _grafico_barras(v.get("por_tipo", {}), "Por tipo")
        with c2:
            _grafico_barras(v.get("por_clasificacion", {}), "Por clasificación")
        with c3:
            _grafico_barras(v.get("por_dormitorios", {}), "Por dormitorios")
    elif indicador.codigo == "terminadas_y_sin_terminar":
        c1, c2, c3 = st.columns(3)
        c1.metric("Terminadas", v.get("terminadas"))
        c2.metric("Sin terminar", v.get("sin_terminar"))
        c3.metric("Desaprobadas", v.get("desaprobadas"))
        c4, c5 = st.columns(2)
        with c4:
            _grafico_barras(v.get("solicitadas_por_anio", {}), "Solicitadas por año")
        with c5:
            _grafico_barras(v.get("finalizadas_por_anio", {}), "Finalizadas por año")
    elif indicador.codigo == "antiguedad_sin_terminar":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cantidad", v.get("cantidad"))
        c2.metric("Mínimo (días)", v.get("dias_minimo"))
        c3.metric("Mediana (días)", v.get("dias_mediana"))
        c4.metric("Máximo (días)", v.get("dias_maximo"))
    elif indicador.codigo == "tasa_activacion_finalizacion":
        c1, c2 = st.columns(2)
        c1.metric("Organizaciones con datos completos", v.get("organizaciones_con_datos_completos"))
        c2.metric("Organizaciones totales (en «solicitadas»)", v.get("organizaciones_totales"))
        por_organizacion = v.get("por_organizacion") or []
        if por_organizacion:
            st.dataframe(pd.DataFrame(por_organizacion), width="stretch", hide_index=True)
    elif indicador.codigo == "peso_tipo_solicitante":
        _grafico_barras(v.get("solicitudes", {}), "Solicitudes por tipo de solicitante")
    elif indicador.codigo == "tiempos_del_proceso":
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Solicitud → activación**")
            st.json(v.get("solicitud_a_activacion", {}))
        with c2:
            st.markdown("**Activación → fin de obra**")
            st.json(v.get("activacion_a_fin_obra", {}))
    else:
        st.json(v)


for indicador in indicadores:
    with st.container(border=True):
        st.markdown(f"#### {indicador.pregunta}")
        badge = (f":{'green' if indicador.capacidad == 'disponible' else 'orange' if indicador.capacidad == 'parcial' else 'grey'}"
                f"[{indicador.capacidad}]  ·  confianza: *{indicador.confianza}*  ·  "
                f"fuente: {', '.join(indicador.reportes)}")
        st.markdown(badge)
        st.write(indicador.explicacion)
        with st.expander("Cómo leerlo"):
            st.write(indicador.como_leerlo)
        if indicador.capacidad == "no_disponible":
            st.caption("No disponible con esta fuente.")
        else:
            _mostrar_valor(indicador)
