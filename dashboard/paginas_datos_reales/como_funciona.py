"""Pestaña «Cómo funciona»: el recorrido de un dato explicado paso a paso, con un ejemplo inventado.
No depende de la fuente elegida — el proceso es siempre el mismo."""
import streamlit as st

from dashboard.components.glosario import mostrar_glosario

_DIAGRAMA = """
digraph proceso {
    rankdir=LR; bgcolor="transparent";
    node [shape=box, style="rounded,filled", fontname="sans-serif", fontsize=11,
          fillcolor="#eef2ff", color="#4f46e5"];
    A [label="Export\\nPDF de VISOC"];
    B [label="Reconocer\\nel formato"];
    C [label="Leer y anonimizar\\nnombres y DNI"];
    D [label="Guardar el crudo\\n(ya anonimizado)"];
    E [label="Validar\\ncontra los totales\\ndel propio reporte"];
    F [label="Modelo propio\\nviviendas, organizaciones,\\nexpedientes, medidas",
       fillcolor="#d1fae5", color="#10b981"];
    G [label="Rechazada\\nqueda registrada,\\nel modelo no se toca",
       fillcolor="#fee2e2", color="#ef4444"];
    A -> B -> C -> D -> E;
    E -> F [label="  valida", fontsize=10];
    E -> G [label="  no valida", fontsize=10];
}
"""

# Nombre y clave puramente de ejemplo, para mostrar el paso de anonimización con datos inventados —
# nunca un archivo real del área.
_EJEMPLO_NOMBRE = "Juan Carlos Pérez"
_EJEMPLO_CLAVE = "clave-de-ejemplo-de-mas-de-16-caracteres-no-es-la-real"


def render() -> None:
    st.subheader("¿Cómo llega un dato al sistema?")
    st.caption(
        "Desde que se sube un reporte de VISOC hasta que aparece como un indicador acá, un dato pasa "
        "por estos pasos. Es siempre el mismo camino, sin importar qué fuente estés mirando en las "
        "otras pestañas."
    )
    st.graphviz_chart(_DIAGRAMA)

    st.divider()
    st.markdown("#### Un ejemplo concreto (con un nombre inventado)")
    from datos.anonimizador import Anonimizador
    seudonimo = Anonimizador(_EJEMPLO_CLAVE).seudonimo(_EJEMPLO_NOMBRE)
    c1, c2 = st.columns(2)
    c1.metric("Nombre en el PDF (nunca se guarda así)", _EJEMPLO_NOMBRE)
    c2.metric("Lo que queda guardado", seudonimo)
    st.caption(
        "La misma persona siempre recibe el mismo nombre inventado (mientras no cambie la clave del "
        "equipo), así se puede seguir un caso a través de varios reportes sin saber quién es."
    )

    mostrar_glosario()
