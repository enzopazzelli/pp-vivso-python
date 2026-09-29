"""Pestaña «Mapa de datos»: postal del estado actual de las colecciones (cuánto hay de cada una,
ahora), no del proceso — eso lo cubre «Cómo funciona» (`como_funciona.py`)."""
import streamlit as st

# (clave de la colección, etiqueta en español llano, emoji)
_COLECCIONES = [
    ("viviendas", "Viviendas", "🏠"),
    ("organizaciones", "Organizaciones", "🤝"),
    ("medidas", "Medidas", "📊"),
    ("expedientes", "Expedientes", "📁"),
    ("reclamos", "Reclamos", "⚠️"),
    ("medidas_categoria", "Medidas por categoría", "📈"),
]

# Qué colección se relaciona con cuál, para dibujar la estructura además del volumen
_RELACIONES = [
    ("viviendas", "organizaciones"),
    ("expedientes", "viviendas"),
    ("medidas", "organizaciones"),
    ("medidas_categoria", "organizaciones"),
]

_GUIA = {
    "viviendas": "Una vivienda social solicitada, en cualquier etapa: iniciada, activada, finalizada o desaprobada.",
    "organizaciones": "Quien gestiona el trámite: un municipio, una comisión municipal, una ONG o una cooperativa.",
    "medidas": "Los números del reporte «Por Solicitante»: solicitudes, beneficiarios, activadas y fin de obra, por organización.",
    "expedientes": "Los números de expediente asociados a una vivienda: de solicitud, de reclamo o de acta.",
    "reclamos": "Reclamos presentados sobre una vivienda o un expediente. Depende de GDE, todavía sin importador.",
    "medidas_categoria": "Los mismos números que «Medidas», agrupados por tipo de solicitante en vez de por organización.",
}


def _conteos(fuente) -> dict[str, int]:
    return {
        "viviendas": len(fuente.viviendas()),
        "organizaciones": len(fuente.organizaciones()),
        "medidas": len(fuente.medidas()),
        "expedientes": len(fuente.expedientes()),
        "reclamos": len(fuente.reclamos()),
        "medidas_categoria": len(fuente.medidas_categoria()),
    }


def _diagrama(conteos: dict[str, int]) -> str:
    lineas = ["digraph mapa {", '  rankdir=LR; bgcolor="transparent";',
             '  node [shape=box, style="rounded,filled", fontname="sans-serif", fontsize=12];']
    for clave, etiqueta, emoji in _COLECCIONES:
        cantidad = conteos[clave]
        relleno = "#d1fae5" if cantidad > 0 else "#e5e7eb"
        borde = "#10b981" if cantidad > 0 else "#9ca3af"
        lineas.append(
            f'  {clave} [label="{emoji} {etiqueta}\\n{cantidad}", fillcolor="{relleno}", color="{borde}"];')
    for origen, destino in _RELACIONES:
        lineas.append(f'  {origen} -> {destino} [dir=none, color="#94a3b8"];')
    lineas.append("}")
    return "\n".join(lineas)


def render(fuente) -> None:
    st.subheader("¿Qué hay cargado hoy?")
    st.caption(
        "Un vistazo a cuánta información tiene el sistema ahora mismo, con la fuente elegida arriba. "
        "El verde significa que esa colección tiene datos; el gris, que está vacía."
    )
    conteos = _conteos(fuente)
    st.graphviz_chart(_diagrama(conteos))

    st.divider()
    st.markdown("#### ¿Qué es cada cosa?")
    for clave, etiqueta, emoji in _COLECCIONES:
        st.markdown(f"**{emoji} {etiqueta}** ({conteos[clave]}) — {_GUIA[clave]}")
