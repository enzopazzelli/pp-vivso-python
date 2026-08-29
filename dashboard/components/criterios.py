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
        "Panorama de todo el programa, sobre la tabla **vivienda** (una fila por obra). "
        "*En obra*: estados Iniciada/Avanzada · *Terminadas*: Finalizada/Adjudicada · "
        "*Avance promedio*: promedio del AFO de todas las obras · *Riesgo alto*: obra "
        "activa que pasó los 90 días con avance menor al 30%.",

    "mapa":
        "El mapa ubica cada obra por su **latitud y longitud** (tabla **vivienda**) y la "
        "colorea según su nivel de riesgo: verde (bajo), amarillo (medio) y rojo (alto).",

    "viviendas":
        "Toma las obras de la tabla **vivienda** y las **agrupa** según los filtros del "
        "panel lateral (departamento, estado, riesgo…); los KPIs y gráficos se recalculan "
        "sobre ese subconjunto.",

    "gestoras":
        "Agrupa las obras (tabla **vivienda**) por su **organización gestora** (tabla "
        "**organizacion**) para comparar el desempeño de cada una: su avance promedio y "
        "cuántas de sus obras están **en riesgo** (vencidas y con poco avance). La gestora "
        "puede ser un **municipio**, una **comisión municipal**, una **ONG** o una "
        "**cooperativa** (`tipo_gestora`); el *ámbito* agrupa esos tipos en público y "
        "privado, que es donde cambia la palanca del ministerio ante una obra trabada.",

    "riesgo":
        "Cada obra se ubica por sus **días activa** y su **avance** (tabla **vivienda**). "
        "Se marca *riesgo alto* si pasó los 90 días con avance menor al 30%, y *riesgo "
        "medio* si pasó los 90 días con avance entre 30% y 80%.",

    "rubros":
        "Usa la tabla **avance_rubro**, que guarda el avance de las 15 etapas "
        "constructivas de cada obra. La *etapa activa* es el primer rubro sin terminar; el "
        "*cuello de botella* es la etapa donde se acumulan más obras detenidas.",

    "tiempos":
        "Mide los días entre la fecha de inicio y la de fin de cada obra (tabla "
        "**vivienda**). Solo cuenta las obras terminadas, porque las que siguen en curso "
        "todavía no tienen una duración final.",

    "tecnicos":
        "Cruza tres fuentes: **asignacion_tecnico** (qué obras tiene cada técnico), "
        "**visita** (las visitas hechas, con el avance verificado en el campo) y "
        "**vivienda**. *Cobertura*: % de obras con al menos una visita · *Discrepancia*: "
        "avance que reporta la gestora menos el que verifica el técnico.",

    "mis_obras":
        "Muestra las obras asignadas al técnico seleccionado (**asignacion_tecnico**), con "
        "sus **visitas** y el riesgo de cada obra (**vivienda**). La cola de trabajo se "
        "ordena por estado de visita y nivel de riesgo.",

    "verificacion_foto":
        "Un modelo de visión reporta la **evidencia física observable** en la foto (¿hay "
        "muros?, ¿a qué altura?, ¿encadenado?, ¿aberturas?) y una **regla determinista** la "
        "convierte en rubro alcanzado y AFO usando el catálogo de **rubro_obra** — el modelo "
        "nunca estima el porcentaje. Ese AFO se contrasta con lo que declaró la gestora para "
        "darle un **grado de respaldo documental**. Los supuestos del componente son los "
        "`[V#]` de `vision/rubrica.py`. **Hoy la percepción está simulada**: no hay fotos ni "
        "modelo conectado, así que los números miden la regla y la cola, no el modelo real.",

    "rutas":
        "Toma las obras pendientes del técnico (**vivienda** + **asignacion_tecnico**, "
        "misma cola que en Mis obras) y arma un viaje de varios días: primero encadena las "
        "**urgentes** (riesgo alto o medio) por el camino más corto, y en modo mezcla suma "
        "pendientes no urgentes que queden de paso sin desviarse mucho. No hay red vial real: "
        "la distancia se aproxima con línea recta corregida por un factor de ruta. Los "
        "supuestos son los `[R#]` de `rutas/parametros.py`.",

    "evolucion":
        "Agrupa por mes las fechas de inicio y de fin de las obras (tabla **vivienda**). "
        "El *backlog* son las obras abiertas en cada momento: inicios acumulados menos "
        "finalizaciones acumuladas.",
}


def nota_criterio(seccion: str, titulo: str = "ℹ️ Cómo se calcula") -> None:
    """Despliega un expander breve con el cálculo y la fuente de datos de la sección."""
    with st.expander(titulo):
        st.markdown(NOTAS.get(seccion, ""))
        st.caption("Datos del modelo sintético; los criterios se validan con el área en "
                   "`docs/datos-a-confirmar.md`.")
