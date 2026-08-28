import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.criterios import nota_criterio
from dashboard.components.data_loader import cargar_avance_rubros, cargar_viviendas
from vision.decision import ETIQUETA_GRADO, explicar, grado_de_respaldo, leer_evidencia
from vision.evaluacion import (
    barrido_sensibilidad,
    cola_de_evidencia_insuficiente,
    cola_de_revision,
    correr_pipeline,
    distribucion_grados,
    metricas,
    precision_en_k,
)
from vision.percepcion import PercepcionSimulada, evidencia_ideal
from vision.rubrica import (
    EVIDENCIA_OBSERVABLE,
    ORDEN_RUBROS,
    RUBROS_POR_ID,
    RUBROS_VENTANA_TEMPORAL,
    peso_acumulado,
)
from vision.simulacion import preparar

st.set_page_config(page_title="Verificación por foto — VIVSO", layout="wide")

# Paleta estándar del proyecto (misma que notebooks y resto del dashboard)
C = {"base": "#4f46e5", "ok": "#10b981", "medio": "#f59e0b",
     "alerta": "#f43f5e", "neutro": "#94a3b8"}
TOP_K = 50

st.title("📷 Verificación del avance por foto")
st.caption(
    "Cuando la gestora reporta un avance, las fotos que adjunta se usan para **ponderar "
    "ese reporte**: decir si la evidencia lo respalda, lo contradice o no alcanza. "
    "El AFO lo sigue certificando el técnico — el sistema no aprueba nada."
)

st.warning(
    "**Prototipo con percepción simulada.** Todavía no hay fotos ni modelo de visión "
    "conectado. Lo que se muestra corre el pipeline real —la regla de decisión, el grado "
    "de respaldo, la cola— sobre evidencia generada a partir del avance por rubro que ya "
    "tiene el dataset, degradada con una tasa de error configurable. Sirve para responder "
    "**cuán bueno tiene que ser el modelo** antes de invertir en etiquetar fotos.",
    icon="🧪",
)


@st.cache_data(ttl=600)
def _conjunto_evaluacion() -> pd.DataFrame:
    return preparar(cargar_avance_rubros(), cargar_viviendas())


@st.cache_data(ttl=600)
def _barrido(k: int) -> pd.DataFrame:
    return barrido_sensibilidad(_conjunto_evaluacion(), k=k)


@st.cache_data(ttl=600)
def _corrida(tasa: float) -> pd.DataFrame:
    return correr_pipeline(_conjunto_evaluacion(), tasa_error=tasa)


df_eval = _conjunto_evaluacion()
if df_eval.empty:
    st.error("No hay datos de avance por rubro. Corré `python -m synthetic.generate`.")
    st.stop()

# ── Control principal ─────────────────────────────────────────────────────
st.divider()
st.subheader("¿Cuán bueno tiene que ser el modelo de visión?")
st.markdown(
    "Es la pregunta de diseño que normalmente se contesta tarde y cara. Movés el error "
    "del modelo y ves qué le pasa al sistema."
)

tasa = st.slider(
    "Tasa de error del modelo de percepción (probabilidad de leer mal un campo de evidencia)",
    min_value=0.0, max_value=0.5, value=0.10, step=0.05, format="%.2f",
)

res = _corrida(tasa)
m = metricas(res)
precision = precision_en_k(res, TOP_K)
baseline = res["sobre_reporta"].mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric(f"Precisión en el top {TOP_K}", f"{precision:.0%}",
          delta=f"{precision / baseline:.1f}× sobre el azar")
k2.metric("Baseline actual", f"{baseline:.0%}",
          help="Proporción de obras que sobre-reportan. Es lo que acertaría el técnico "
               "eligiendo al azar, que es el estado de hoy.")
k3.metric("Obras en la cola de revisión", f"{len(cola_de_revision(res))}")
k4.metric("Piden mejor foto", f"{len(cola_de_evidencia_insuficiente(res))}",
          delta=f"{m['tasa_abstencion']:.0%} del total", delta_color="off",
          help="El sistema se abstiene en vez de responder con seguridad. No es un fallo: "
               "es lo que lo hace confiable.")

nota_criterio("verificacion_foto")

# ── Curva de sensibilidad ─────────────────────────────────────────────────
barrido = _barrido(TOP_K)
col_izq, col_der = st.columns([3, 2])

with col_izq:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=barrido.index * 100, y=barrido["precision_top_k"] * 100,
        name=f"Precisión en el top {TOP_K}", mode="lines+markers",
        line=dict(color=C["base"], width=3), marker=dict(size=8),
    ))
    fig.add_trace(go.Scatter(
        x=barrido.index * 100, y=barrido["tasa_abstencion"] * 100,
        name="Se abstiene", mode="lines+markers",
        line=dict(color=C["medio"], width=2, dash="dot"),
    ))
    fig.add_hline(y=baseline * 100, line_dash="dash", line_color=C["neutro"],
                  annotation_text=f"Baseline ({baseline:.0%})",
                  annotation_position="bottom right")
    fig.add_vline(x=tasa * 100, line_color=C["alerta"], line_width=1, opacity=0.5)
    fig.update_layout(
        title="Cómo se degrada el sistema según el error del modelo",
        xaxis_title="Error del modelo de percepción (%)",
        yaxis_title="%", yaxis_range=[0, 100],
        legend=dict(orientation="h", y=1.12), margin=dict(l=0, t=60),
    )
    st.plotly_chart(fig, width="stretch")

with col_der:
    st.markdown("##### Cómo se lee")
    st.markdown(
        "El sistema **degrada de forma segura**: a medida que el modelo empeora, no se "
        "vuelve confiadamente incorrecto — se abstiene más. Lo que llega al tope de la "
        "cola sigue siendo confiable, y lo que no puede leer se devuelve pidiendo otra foto.\n\n"
        "Esa es la propiedad que hace utilizable a un triage. Un sistema que a mayor error "
        "empieza a inventar contradicciones sería peor que no tener nada: haría perder "
        "viajes y confianza al mismo tiempo."
    )
    st.markdown("##### Grados de respaldo con este error")
    for grado, pct in distribucion_grados(res).items():
        st.markdown(f"- {ETIQUETA_GRADO.get(grado, grado)} — **{pct:.1f}%**")

# ── Caso a caso ───────────────────────────────────────────────────────────
st.divider()
st.subheader("Qué ve el técnico, obra por obra")
st.markdown(
    "El producto del sistema no es un número: es un **motivo**. Esta es la diferencia "
    "entre poder discutirlo con una gestora y no poder."
)

cola = cola_de_revision(res)
if cola.empty:
    st.info("Con esta tasa de error el sistema no emite ninguna alerta con confianza.")
else:
    obra_sel = st.selectbox(
        f"Obras al tope de la cola de revisión ({len(cola)} en total)",
        options=cola.head(TOP_K)["vivienda_id"].tolist(),
    )
    fila_eval = df_eval[df_eval["vivienda_id"] == obra_sel].iloc[0]
    fila_res = cola[cola["vivienda_id"] == obra_sel].iloc[0]

    # Se reconstruye la lectura con la misma semilla del pipeline para que lo que se
    # muestra acá sea exactamente lo que produjo la fila de la cola, y no otra corrida.
    evidencia = PercepcionSimulada(tasa_error=tasa, seed=42) \
        .leer_desde_verdad(int(fila_eval.rubro_alcanzado))
    lectura = leer_evidencia(evidencia)
    grado, motivo = grado_de_respaldo(lectura, int(fila_eval.afo_declarado))

    c_ev, c_lec = st.columns([2, 3])

    with c_ev:
        st.markdown("##### Evidencia que reportó el modelo")
        ideal = evidencia_ideal(int(fila_eval.rubro_alcanzado))
        filas_ev = []
        for campo, valor in evidencia.items():
            if valor == "no_determinable":
                estado = "🟡 no determinable"
            elif valor == ideal[campo]:
                estado = "🟢 correcto"
            else:
                estado = f"🔴 debía ser «{ideal[campo]}»"
            filas_ev.append({"Campo": campo, "Leído": valor, "Contra la verdad": estado})
        st.dataframe(pd.DataFrame(filas_ev), width="stretch", hide_index=True)
        st.caption(
            "La columna de la derecha existe solo porque estamos simulando: con fotos "
            "reales no hay verdad conocida contra la cual comparar caso a caso."
        )

    with c_lec:
        st.markdown("##### Lectura y veredicto")
        color = {"contradicho_sobre_reporte": C["alerta"],
                 "contradicho_avance_rechazado": C["alerta"],
                 "respaldado": C["ok"]}.get(grado, C["medio"])
        st.markdown(
            f"<div style='border-left:4px solid {color};padding:0.6rem 1rem;"
            f"background:rgba(148,163,184,0.10);border-radius:4px'>"
            f"<b>{ETIQUETA_GRADO[grado]}</b><br>{motivo}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"**Lectura:** {explicar(lectura)}")

        b1, b2, b3 = st.columns(3)
        b1.metric("Declarado por la gestora", f"{int(fila_eval.afo_declarado)}%")
        b2.metric("Confirmado por la foto", f"{lectura.afo_estimado}%")
        b3.metric("AFO real (solo simulación)", f"{int(fila_eval.afo_real)}%")

        st.markdown(
            "**La acción cambia según el tipo de gestora:** a un municipio o comisión "
            "municipal se le gestiona institucionalmente; a una ONG o cooperativa se le "
            "reclama por convenio."
        )

# ── La rúbrica ────────────────────────────────────────────────────────────
st.divider()
st.subheader("La rúbrica: qué se ve en una foto de cada rubro")
st.markdown(
    "El modelo **no estima el porcentaje**: estima la evidencia física. La aritmética la "
    "hace el catálogo de rubros que ya existe. Eso es lo que permite explicarle el número "
    "a una gestora — el mismo criterio con el que se defendió el modelo de riesgo."
)

filas_rub = []
for rid in ORDEN_RUBROS:
    r = RUBROS_POR_ID[rid]
    if rid in RUBROS_VENTANA_TEMPORAL:
        verif = "🟡 Ventana temporal"
    elif rid == 15:
        verif = "🔴 No verificable"
    else:
        verif = "🟢 Alta"
    filas_rub.append({
        "#": rid, "Rubro": r["nombre"], "Peso": f"{r['peso_pct']}%",
        "AFO acumulado": f"{peso_acumulado(rid)}%",
        "Evidencia observable": EVIDENCIA_OBSERVABLE[rid],
        "Verificabilidad": verif,
    })
st.dataframe(pd.DataFrame(filas_rub), width="stretch", hide_index=True)
st.caption(
    "**87% del AFO es auditable con fotos oportunistas; 97% si el protocolo de carga "
    "obliga a capturar las dos ventanas temporales** (rubro 2, capa aisladora; rubro 8, "
    "aislante térmico). El rubro 15 no tiene manifestación visible propia."
)
