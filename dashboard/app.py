import streamlit as st

st.set_page_config(
    page_title="VIVSO — Ciencia de Datos",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("VIVSO — Sistema de Gestión de Viviendas Sociales")
st.markdown(
    "**Subsecretaría de Promoción Humana** · Gobierno de Santiago del Estero  \n"
    "Panel de análisis — Equipo Ciencia de Datos · PP2 ITSE"
)

st.divider()

col1, col2, col3 = st.columns(3)
col1.page_link("pages/01_viviendas.py", label="🏘 Viviendas",   icon="🏘")
col2.page_link("pages/02_ongs.py",      label="🤝 ONGs",         icon="🤝")
col3.page_link("pages/03_mineria.py",   label="🔬 Minería",      icon="🔬")

st.markdown("""
### Acerca del proyecto

El sistema VIVSO unifica tres sistemas legacy desconectados (App GPS, VISOC y GEDO)
para el seguimiento del programa de viviendas sociales asociado al **Programa Chagas**.

Este panel corresponde al componente de **Ciencia de Datos**: ETL, análisis exploratorio,
clustering y modelo de riesgo desarrollados en Python.

**Flujo de datos:**
`API Java (Programación)` → `ETL Python` → `Base de datos local` → `Este dashboard`
""")
