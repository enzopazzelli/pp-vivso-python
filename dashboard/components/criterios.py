"""
Nota breve de "cómo se calcula" cada sección del dashboard, con la fuente de datos
(qué tabla / qué tipo de info). Pensada para que el responsable del área entienda
de un vistazo el indicador que está viendo, sin tecnicismos ni listado de supuestos.

Centralizar los textos acá permite editarlos en un solo lugar. El detalle de los
supuestos ajustables vive aparte, en docs/datos-a-confirmar.md.

Uso en una página:
    from dashboard.components.criterios import nota_criterio
    nota_criterio("riesgo")
"""
import streamlit as st

# Una nota corta por sección: cómo se calcula + de dónde salen los datos (en negrita
# el nombre de la tabla de origen). Breve a propósito.
NOTAS = {
    "resumen":
        "Sobre la tabla **vivienda** (una fila por obra). *En obra*: estados "
        "Iniciada/Avanzada · *Terminadas*: Finalizada/Adjudicada · *Avance promedio*: "
        "promedio del AFO · *Riesgo alto*: obra vencida (más de 90 días) con avance menor al 30%.",

    "mapa":
        "Cada punto es una obra con coordenadas GPS (campos *lat/lng* de la tabla "
        "**vivienda**), coloreada por su nivel de riesgo.",

    "viviendas":
        "Sobre la tabla **vivienda**, aplicando los filtros del panel lateral. "
        "*Avance promedio*: promedio del AFO · *Riesgo alto*: obra vencida (más de 90 "
        "días) con avance menor al 30%.",

    "ongs":
        "Cruza la tabla **vivienda** (avance, estado y riesgo de cada obra) con "
        "**organizacion** (datos de cada ONG), agrupando por la ONG gestora de la obra.",

    "riesgo":
        "Cada obra se ubica por sus **días activa** y su **avance** (tabla **vivienda**). "
        "El modelo marca *riesgo alto* si pasó los 90 días con avance menor al 30%, y "
        "*riesgo medio* si pasó los 90 días con avance entre 30% y 80%.",

    "rubros":
        "Usa la tabla **avance_rubro**: el avance de cada una de las 15 etapas "
        "constructivas por obra. La *etapa activa* es el primer rubro sin terminar; el "
        "*cuello de botella* es la etapa donde se acumulan más obras.",

    "tiempos":
        "Días entre la fecha de inicio y la de fin (tabla **vivienda**). Solo obras "
        "terminadas: las que siguen en curso todavía no tienen duración final.",

    "tecnicos":
        "Cruza **asignacion_tecnico** (qué obras tiene cada técnico), **visita** "
        "(visitas hechas y avance verificado en el campo) y **vivienda**. *Cobertura*: "
        "% de obras con al menos una visita · *Discrepancia*: avance que reporta la ONG "
        "menos el que verifica el técnico.",

    "mis_obras":
        "Las obras asignadas al técnico (**asignacion_tecnico**), con sus **visitas** y "
        "el riesgo de cada obra (**vivienda**). La cola se ordena por estado de visita y "
        "nivel de riesgo.",

    "evolucion":
        "Agrupa por mes las fechas de inicio y de fin de la tabla **vivienda**. "
        "*Backlog*: inicios acumulados menos finalizaciones acumuladas.",
}


def nota_criterio(seccion: str, titulo: str = "ℹ️ Cómo se calcula") -> None:
    """Despliega un expander breve con el cálculo y la fuente de datos de la sección."""
    with st.expander(titulo):
        st.markdown(NOTAS.get(seccion, ""))
        st.caption(
            "Datos del modelo sintético. Si algún criterio no coincide con la realidad "
            "del programa, se anota en `docs/datos-a-confirmar.md`."
        )
