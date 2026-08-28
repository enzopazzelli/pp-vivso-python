"""
Demo end-to-end del componente de verificación fotográfica, sin API y sin fotos.

    python -m vision.demo

Corre el pipeline completo sobre el dataset sintético con percepción simulada y
responde la pregunta que se puede contestar hoy: cuán bueno tiene que ser el modelo
de visión para que el sistema le sirva al área.
"""
import pandas as pd

from vision.decision import ETIQUETA_GRADO, explicar, grado_de_respaldo, leer_evidencia
from vision.evaluacion import (
    barrido_sensibilidad,
    correr_pipeline,
    distribucion_grados,
    precision_en_k,
)
from vision.percepcion import PercepcionSimulada
from vision.simulacion import preparar

TASA_REALISTA = 0.20   # supuesto de trabajo para el ejemplo puntual
TOP_K = 50


def _titulo(t: str) -> None:
    print("\n" + "=" * 74 + f"\n{t}\n" + "=" * 74)


def main() -> None:
    df_viv = pd.read_csv("data/viviendas_sinteticas.csv")
    df_rub = pd.read_csv("data/avance_rubros.csv")
    df_eval = preparar(df_rub, df_viv)

    _titulo("Conjunto de evaluación")
    print(f"Obras activas evaluadas : {len(df_eval)}")
    print(f"Sobre-reporte material  : {df_eval['sobre_reporta'].sum()} "
          f"({df_eval['sobre_reporta'].mean()*100:.1f}%)")
    print("\nRubro donde están paradas las obras:")
    print(df_eval["rubro_alcanzado"].value_counts().sort_index().to_string())

    # ── Dos casos concretos, que es como los ve el técnico ─────────────────
    # Se muestran una detección correcta y una abstención a propósito: el segundo
    # caso es tan importante como el primero, porque un sistema que nunca admite
    # no saber es un sistema en el que el técnico deja de confiar.
    _titulo("Dos casos, tal como los vería el técnico")
    percepcion = PercepcionSimulada(tasa_error=TASA_REALISTA, seed=1)
    mostrados = {"deteccion": False, "abstencion": False}

    for caso in df_eval.itertuples():
        evidencia = percepcion.leer_desde_verdad(int(caso.rubro_alcanzado))
        lectura = leer_evidencia(evidencia)
        grado, motivo = grado_de_respaldo(lectura, int(caso.afo_declarado))

        es_deteccion = grado == "contradicho_sobre_reporte" and caso.sobre_reporta
        es_abstencion = not lectura.determinable
        etiqueta = ("Detección correcta" if es_deteccion and not mostrados["deteccion"]
                    else "Abstención" if es_abstencion and not mostrados["abstencion"]
                    else None)
        if etiqueta is None:
            continue
        mostrados["deteccion" if es_deteccion else "abstencion"] = True

        print(f"\n── {etiqueta} · obra {caso.vivienda_id} " + "─" * 24)
        print("  Evidencia : " + ", ".join(f"{k}={v}" for k, v in evidencia.items()))
        print(f"  Lectura   : {explicar(lectura)}")
        print(f"  Grado     : {ETIQUETA_GRADO[grado]}")
        print(f"  Motivo    : {motivo}")
        if all(mostrados.values()):
            break

    # ── El resultado presentable de hoy ────────────────────────────────────
    _titulo(f"¿Cuán bueno tiene que ser el modelo? (barrido de sensibilidad, K={TOP_K})")
    barrido = barrido_sensibilidad(df_eval, k=TOP_K)
    cols = ["acierto_rubro_pm1", "mae_afo", "tasa_abstencion", "precision_alerta",
            "recall_alerta", "precision_top_k", "baseline", "cola_revision", "cola_mejor_foto"]
    print(barrido[cols].round(3).to_string())
    print("\nLectura: 'baseline' es la proporción de sobre-reporte en la población — lo que")
    print("acertaría el técnico eligiendo obras al azar, que es el estado actual.")
    print("'precision_top_k' es lo que acierta revisando las K primeras de la cola del sistema.")
    print("'cola_mejor_foto' son las obras que el sistema NO juzga y devuelve pidiendo otra foto.")

    # ── Distribución de grados con la tasa de trabajo ──────────────────────
    _titulo(f"Grados de respaldo con tasa de error {TASA_REALISTA:.0%}")
    res = correr_pipeline(df_eval, tasa_error=TASA_REALISTA)
    for grado, pct in distribucion_grados(res).items():
        print(f"  {ETIQUETA_GRADO.get(grado, grado):<34} {pct:>5.1f}%")

    precision = precision_en_k(res, TOP_K)
    baseline = res["sobre_reporta"].mean()
    print(f"\nPrecision@{TOP_K}: {precision:.1%} vs. baseline {baseline:.1%} "
          f"→ {precision / baseline:.1f}× mejor que elegir al azar")


if __name__ == "__main__":
    main()
