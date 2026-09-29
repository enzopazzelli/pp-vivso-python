"""Pestaña «Cobertura y confianza»: qué tan cubierto está cada indicador por los reportes
disponibles, y cuándo se importó cada cosa."""
import pandas as pd
import plotly.express as px
import streamlit as st

from datos.catalogo_reportes import FICHAS
from datos.indicadores.registro import TODOS

_PESO_CONFIANZA = {"confirmado": 3, "inferido": 2, "sin_confirmar": 1}


def _mapa_de_calor(fuente) -> pd.DataFrame:
    filas = []
    for funcion in TODOS:
        indicador = funcion(fuente)
        fila = {"indicador": indicador.pregunta}
        for reporte in FICHAS:
            fila[reporte] = _PESO_CONFIANZA[indicador.confianza] if reporte in indicador.reportes else 0
        filas.append(fila)
    return pd.DataFrame(filas).set_index("indicador")


def _figura_calor(calor: pd.DataFrame):
    """La escala de colores se fija de 0 a 3 explícitamente (`zmin`/`zmax`) — sin esto, Plotly la
    estira al rango de valores realmente presentes en `calor`, y como hoy las dos fichas de
    `datos/catalogo_reportes.py` son "inferido" (peso 2), el mapa terminaba pintando "inferido" con
    el color de "confirmado" (encontrado en la revisión final)."""
    fig = px.imshow(calor, aspect="auto", zmin=0, zmax=3,
                    color_continuous_scale=["#e5e7eb", "#fde68a", "#fcd34d", "#34d399"],
                    labels=dict(x="Reporte", y="Indicador", color="Confianza"))
    fig.update_xaxes(tickvals=list(range(len(FICHAS))), ticktext=[f["nombre"] for f in FICHAS.values()])
    fig.update_layout(height=380, margin=dict(t=20, b=10, l=10, r=10), coloraxis_showscale=False)
    return fig


def _linea_de_tiempo() -> pd.DataFrame:
    from sqlalchemy.exc import OperationalError
    from sqlalchemy.orm import Session

    from datos.modelo import Importacion
    from datos.sesion import crear_engine

    columnas = ["archivo", "importado_en", "estado", "tipo_reporte"]
    engine = crear_engine()
    try:
        with Session(engine) as sesion:
            filas = sesion.query(Importacion).order_by(Importacion.importado_en).all()
            return pd.DataFrame([{
                "archivo": f.archivo_nombre, "importado_en": f.importado_en, "estado": f.estado,
                "tipo_reporte": f.tipo_reporte or "(no reconocido)",
            } for f in filas], columns=columnas)
    except OperationalError:
        # Base propia sin crear o sin migrar: no hay importaciones que mostrar todavía.
        return pd.DataFrame(columns=columnas)
    finally:
        engine.dispose()


def render(fuente) -> None:
    st.subheader("Cobertura y confianza")
    st.caption(
        "El mapa de calor muestra qué tan seguro está cada indicador y de qué reporte depende. La "
        "línea de tiempo muestra cuándo se importó cada archivo y con qué resultado."
    )

    calor = _mapa_de_calor(fuente)
    if calor.empty or (calor.to_numpy() == 0).all():
        st.caption("Todavía no hay indicadores que dependan de ningún reporte con esta fuente.")
    else:
        st.plotly_chart(_figura_calor(calor), width="stretch")
        st.caption(
            "Colores: gris = ese indicador no depende de ese reporte · amarillo claro = confianza "
            "«sin confirmar» · amarillo = confianza «inferido» · verde = confianza «confirmado»."
        )

    st.divider()
    st.markdown("#### Línea de tiempo de importaciones")
    linea = _linea_de_tiempo()
    if linea.empty:
        st.info("ℹ️ Todavía no se importó ningún reporte. Andá a la pestaña «Importar» para cargar el primero.")
        return
    fig = px.scatter(linea, x="importado_en", y="tipo_reporte", color="estado", hover_data=["archivo"],
                     color_discrete_map={"ok": "#10b981", "con_advertencias": "#f59e0b",
                                        "rechazada": "#f43f5e", "sin_importador": "#94a3b8",
                                        "duplicada": "#94a3b8"})
    fig.update_layout(height=280, margin=dict(t=20, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")
