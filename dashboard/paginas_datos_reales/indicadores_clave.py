"""Pestaña «Indicadores clave»: los 6 indicadores existentes, cada uno con el gráfico que le
corresponde según la sección 10.1 de la especificación original."""
import pandas as pd
import plotly.express as px
import streamlit as st

from datos.indicadores.registro import calcular_todos

C = {"base": "#4f46e5"}


def _grafico_barras(valores: dict, titulo: str) -> None:
    if not valores:
        st.caption("Sin datos para graficar.")
        return
    datos = pd.DataFrame({"categoría": list(map(str, valores.keys())), "cantidad": list(valores.values())})
    fig = px.bar(datos, x="categoría", y="cantidad", title=titulo, color_discrete_sequence=[C["base"]])
    fig.update_layout(height=280, margin=dict(t=40, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")


def _grafico_donut(valores: dict, titulo: str) -> None:
    if not valores:
        st.caption("Sin datos para graficar.")
        return
    datos = pd.DataFrame({"categoría": list(map(str, valores.keys())), "cantidad": list(valores.values())})
    fig = px.pie(datos, names="categoría", values="cantidad", title=titulo, hole=0.55)
    fig.update_layout(height=280, margin=dict(t=40, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")


def _histograma(dias: list, titulo: str) -> None:
    if not dias:
        st.caption("Sin datos para graficar.")
        return
    fig = px.histogram(pd.DataFrame({"días": dias}), x="días", title=titulo,
                       color_discrete_sequence=[C["base"]])
    fig.update_layout(height=280, margin=dict(t=40, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")


def _mostrar_valor(indicador) -> None:
    v = indicador.valor
    if indicador.codigo == "viviendas_por_clasificacion_tipo_dormitorios":
        c1, c2, c3 = st.columns(3)
        with c1:
            _grafico_donut(v.get("por_tipo", {}), "Por tipo de vivienda")
        with c2:
            _grafico_donut(v.get("por_clasificacion", {}), "Por clasificación")
        with c3:
            _grafico_barras({str(k): n for k, n in v.get("por_dormitorios", {}).items()}, "Por dormitorios")
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
        c2.metric("Organizaciones totales", v.get("organizaciones_totales"))
        por_organizacion = v.get("por_organizacion") or []
        if por_organizacion:
            datos = pd.DataFrame(por_organizacion)
            fig = px.bar(datos, x="nombre", y=["tasa_activacion", "tasa_finalizacion"],
                        barmode="group", title="Tasas por organización")
            fig.update_layout(height=320, margin=dict(t=40, b=10, l=10, r=10))
            st.plotly_chart(fig, width="stretch")
    elif indicador.codigo == "peso_tipo_solicitante":
        _grafico_donut(v.get("solicitudes", {}), "Solicitudes por tipo de solicitante")
    elif indicador.codigo == "tiempos_del_proceso":
        c1, c2 = st.columns(2)
        with c1:
            _histograma(v.get("dias_solicitud_a_activacion", []), "Solicitud → activación (días)")
        with c2:
            _histograma(v.get("dias_activacion_a_fin_obra", []), "Activación → fin de obra (días)")
    else:
        st.json(v)


def render(fuente) -> None:
    st.subheader("Indicadores clave")
    st.caption(
        "Cada uno indica su **confianza** (qué tan seguro está el equipo de lo que sabe de ese "
        "reporte) y su **capacidad** con la fuente elegida: disponible, parcial (falta algo) o no "
        "disponible."
    )
    for indicador in calcular_todos(fuente):
        with st.container(border=True):
            st.markdown(f"#### {indicador.pregunta}")
            color = ("green" if indicador.capacidad == "disponible"
                    else "orange" if indicador.capacidad == "parcial" else "grey")
            st.markdown(f":{color}[{indicador.capacidad}] · confianza: *{indicador.confianza}* · "
                       f"fuente: {', '.join(indicador.reportes)}")
            st.write(indicador.explicacion)
            with st.expander("Cómo leerlo"):
                st.write(indicador.como_leerlo)
            if indicador.capacidad == "no_disponible":
                # La sección 10.2 de la especificación original pide explicar qué exportar lo
                # habilitaría, no solo decir que falta (encontrado en la revisión final).
                from datos.catalogo_reportes import FICHAS
                nombres = [FICHAS[r]["nombre"] for r in indicador.reportes if r in FICHAS]
                if nombres:
                    st.caption(f"Se habilita importando: {', '.join(nombres)} "
                              "(pestaña «Importar»).")
                else:
                    st.caption("No disponible con esta fuente.")
            else:
                _mostrar_valor(indicador)
