"""
Criterios de cálculo de cada indicador del dashboard, con la etiqueta [S#] del
supuesto ajustable correspondiente (ver synthetic/generate.py y docs/datos-a-confirmar.md).

Por qué existe: que el responsable del área pueda ver, junto a cada indicador, con
qué criterio se calculó y qué se puede corregir. Centralizar los textos acá hace que,
si un criterio cambia, se edite en un solo lugar y se refleje en todo el dashboard.

Uso en una página:
    from dashboard.components.criterios import nota_criterio
    nota_criterio("riesgo", "cuello_botella")   # despliega un expander con esos criterios

Nota: el helper se llama `nota_criterio` (no `criterio`) para no chocar con la
variable de dominio `criterio` (Inclusión/Exclusión) que usan algunas páginas.
"""
import streamlit as st

# Cada clave agrupa las líneas de criterio de un indicador. El texto entre [S#]
# señala el supuesto editable en synthetic/generate.py.
CRITERIOS = {
    "estados": [
        ("En obra", "viviendas en estado *Iniciada* o *Avanzada*."),
        ("Terminadas", "viviendas *Finalizada* (obra completa) o *Adjudicada* (entregada a la familia)."),
        ("Distribución por estado [S2]", "proporción de obras en cada estado del programa."),
        ("Rango de avance por estado [S3]", "AFO esperado en cada estado (Iniciada 0–35%, Avanzada 36–79%, etc.)."),
    ],
    "avance": [
        ("Avance Físico de Obra (AFO) [S14]",
         "suma ponderada de 15 rubros constructivos (los pesos salen del sistema VISOC). "
         "El promedio es el AFO medio de las obras mostradas."),
    ],
    "riesgo": [
        ("Plazo contractual [S1]", "la etapa de construcción tiene un plazo de **90 días**."),
        ("Riesgo alto [S1·S6]", "obra activa **vencida** (>90 días) y con avance **< 30%** — casi paralizada."),
        ("Riesgo medio [S1·S6]", "obra activa **vencida** (>90 días) con avance **30–80%** — atrasada pero avanza."),
        ("Sin riesgo", "obra en plazo, terminada, o vencida pero casi lista (avance ≥ 80%)."),
    ],
    "cuello_botella": [
        ("Etapa activa", "primer rubro de la secuencia constructiva que no llegó al 98% "
                         "(los rubros son secuenciales: el N arranca cuando el N-1 terminó)."),
        ("Cuello de botella [S7]", "la etapa donde se concentran más obras activas. Las etapas "
                                   "donde se modelan los bloqueos (mampostería, revoques, instalaciones) son ajustables."),
    ],
    "sobre_reporte": [
        ("Discrepancia ONG vs. técnico [S8]",
         "avance que reporta la ONG menos el que verifica el técnico en la visita. "
         "Positivo = la ONG **sobre-reportó**; negativo = subestimó."),
    ],
    "cobertura": [
        ("Cobertura de visitas [S11]", "porcentaje de obras de un técnico con **al menos una** visita."),
        ("Regla de visitas", "máximo **2 visitas** por obra; entre visitas, la ONG cubre con reportes."),
    ],
    "tasa_finalizacion": [
        ("Tasa de finalización [S2]", "viviendas *Finalizada* o *Adjudicada* sobre el total."),
    ],
    "tiempos": [
        ("Tiempo de ejecución [S5]", "días entre inicio y fin. Solo obras **terminadas**: incluir las "
                                     "activas sesgaría el promedio (su duración real es desconocida)."),
    ],
    "geografia": [
        ("Distribución geográfica [S15]", "obras por departamento, según la concentración poblacional real."),
    ],
    "ong_sin_asignar": [
        ("Obras sin ONG [S9]", "proporción de obras sin organización gestora asignada."),
    ],
    "actas": [
        ("Actas atascadas [S10]", "obras *Finalizada* cuyo acta de finalización no se tramitó a tiempo "
                                  "(cuello de botella administrativo)."),
    ],
}


def nota_criterio(*claves: str, titulo: str = "ℹ️ Cómo se calcula / criterio") -> None:
    """
    Despliega un expander con los criterios de las claves pedidas, cada uno con
    su etiqueta [S#]. Pensado para ir debajo de un bloque de KPIs o un gráfico,
    para que el responsable del área entienda y, si hace falta, marque correcciones.
    """
    with st.expander(titulo):
        for clave in claves:
            for nombre, desc in CRITERIOS.get(clave, []):
                st.markdown(f"- **{nombre}:** {desc}")
        st.caption(
            "Los valores entre **[S#]** son supuestos ajustables. ¿Algún criterio no "
            "coincide con la realidad del programa? Se anota en `docs/datos-a-confirmar.md` "
            "(cada fila tiene su [S#]) y se corrige en `synthetic/generate.py`."
        )
