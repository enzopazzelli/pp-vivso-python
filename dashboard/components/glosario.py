"""Glosario de términos técnicos del programa, en lenguaje llano — para desplegar en la barra
lateral de cualquier pantalla que use jerga del sistema (activación, AFO, OG/ONG, seudónimo...).

Uso:
    from dashboard.components.glosario import mostrar_glosario
    mostrar_glosario()
"""
import streamlit as st

TERMINOS = {
    "Activación": (
        "El paso previo al Acta de Finalización: cuando el técnico certifica el 100 % de la obra, "
        "el área «activa» el expediente en VISOC para poder emitir el acta."),
    "AFO": "Avance Físico de Obra: el porcentaje de avance de una vivienda, de 0 a 100.",
    "Orden de Pago": (
        "El paso anterior a la activación: la institución cobra y compra materiales para empezar a "
        "construir."),
    "OG / ONG": (
        "Organización Gubernamental / No Gubernamental: dos de los tipos de organización que pueden "
        "gestionar un trámite de vivienda, junto con municipios y cooperativas."),
    "Seudónimo": (
        "El nombre inventado que reemplaza al nombre real de una persona antes de guardar cualquier "
        "dato — siempre el mismo para la misma persona, pero no se puede revertir al nombre original."),
    "Huella": (
        "Un código corto que identifica a una persona o a un archivo sin guardar su dato real (un "
        "hash). Sirve para reconocer si dos registros son de la misma persona o el mismo archivo, "
        "sin saber quién es o qué dice."),
    "Reporte": (
        "Un archivo exportado por VISOC (PDF) con datos de organizaciones o de viviendas, en un "
        "formato que uno de los importadores del sistema sabe reconocer."),
    "Confianza": (
        "Qué tan seguro está el equipo de lo que dice un indicador: «confirmado» (el área lo validó), "
        "«inferido» (se dedujo de los datos) o «sin confirmar» (todavía no se sabe)."),
}


def mostrar_glosario(contenedor=None) -> None:
    """Despliega el glosario en un expander de la barra lateral (o el contenedor que se le pase)."""
    contenedor = contenedor if contenedor is not None else st.sidebar
    with contenedor.expander("📖 Glosario"):
        for termino, explicacion in TERMINOS.items():
            st.markdown(f"**{termino}** — {explicacion}")
