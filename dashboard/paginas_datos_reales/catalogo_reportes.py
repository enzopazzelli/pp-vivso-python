"""Pestaña «Catálogo de reportes»: una ficha por cada tipo de reporte que el sistema sabe leer.
Puro renderizado: los textos ya existen íntegros en `datos/catalogo_reportes.py::FICHAS`."""
import streamlit as st

_COLOR_CONFIANZA = {"confirmado": "green", "inferido": "orange", "sin_confirmar": "grey"}


def render(fuente) -> None:
    st.subheader("Catálogo de reportes")
    st.caption(
        "Qué es cada reporte, qué mide, qué no mide, sus límites conocidos y qué tan segura está el "
        "equipo de lo que dice."
    )
    for ficha in fuente.catalogo_reportes():
        with st.container(border=True):
            st.markdown(f"#### {ficha['nombre']}")
            st.caption(f"Sistema de origen: {ficha['sistema_origen']} · Unidad: {ficha['unidad']} · "
                      f"Revisado el {ficha['revisado_en']:%d/%m/%Y}")
            color = _COLOR_CONFIANZA.get(ficha["confianza"], "grey")
            st.markdown(f":{color}[{ficha['confianza']}]")
            st.markdown("**Qué mide**")
            st.write(ficha["que_mide"])
            st.markdown("**Qué no mide**")
            st.write(ficha["que_no_mide"])
            with st.expander("Límites conocidos"):
                for limite in ficha["limites"]:
                    st.markdown(f"- {limite}")
