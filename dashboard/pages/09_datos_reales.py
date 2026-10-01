"""Vidriera de la capa de datos propia: seis pestañas que muestran qué hay cargado, cómo funciona el
pipeline, los indicadores, la cobertura y confianza, permiten importar un reporte nuevo y consultan el
catálogo de reportes — ver docs/capa-de-datos/como-funciona-la-capa-de-datos.md.

Esta página es la única del dashboard que puede mostrar datos reales (según la fuente elegida). El
resto de las páginas sigue usando exclusivamente el modelo simulado de PP2, sin cambios.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from dashboard.paginas_datos_reales import (
    catalogo_reportes, cobertura_confianza, como_funciona, importar, indicadores_clave, mapa_de_datos,
)
from datos.fuentes.registro import FUENTES_VALIDAS, obtener_fuente

st.set_page_config(page_title="Datos reales — VIVSO", page_icon="🗄️", layout="wide")

ETIQUETA_FUENTE = {"propia": "Base propia (reportes importados)", "simulada": "Datos simulados de PP2",
                   "json_prueba": "JSON de prueba (mínimo, sin PDF ni base)"}

st.title("🗄️ Datos reales — capa de datos propia")
st.caption(
    "Reportes reales de VISOC, anonimizados y validados, con indicadores calculados sobre esa base — "
    "ver docs/capa-de-datos/como-funciona-la-capa-de-datos.md. El resto del dashboard sigue igual, con el modelo "
    "simulado de siempre."
)

fuente_elegida = st.radio(
    "Fuente de datos", FUENTES_VALIDAS, format_func=lambda f: ETIQUETA_FUENTE[f], horizontal=True,
    help="«Propia» necesita reportes ya importados (pestaña «Importar»); si no hay ninguno, usá "
        "«Simulada» o «JSON de prueba» para ver el panel funcionando igual.",
)
fuente = obtener_fuente(fuente_elegida)

st.divider()


def _render_con_fuente(funcion_render) -> None:
    """"Propia" sin base creada o sin migrar tira RuntimeError al pedirle cualquier dato — acá se
    convierte en un aviso, pestaña por pestaña, en vez de cortar toda la página antes de armar las
    pestañas (encontrado en la revisión final: eso escondía "Importar", la pestaña que justamente
    permite arreglarlo, detrás del mismo error que "Importar" resuelve)."""
    try:
        funcion_render(fuente)
    except RuntimeError as error:
        st.info(f"ℹ️ {error}")


tabs = st.tabs(["🗺️ Mapa de datos", "❓ Cómo funciona", "📊 Indicadores clave",
               "🎯 Cobertura y confianza", "⬆️ Importar", "📚 Catálogo de reportes"])
with tabs[0]:
    _render_con_fuente(mapa_de_datos.render)
with tabs[1]:
    como_funciona.render()
with tabs[2]:
    _render_con_fuente(indicadores_clave.render)
with tabs[3]:
    _render_con_fuente(cobertura_confianza.render)
with tabs[4]:
    importar.render()
with tabs[5]:
    catalogo_reportes.render(fuente)
