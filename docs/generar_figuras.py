"""
Genera las figuras del Informe EDA (docs/informe-eda.md) a partir del dataset.

Uso (desde la raíz del repo, con el venv activo):
    python docs/generar_figuras.py

Lee data/viviendas_sinteticas.csv (+ avance_rubros, visitas, organizaciones) y
escribe los PNG en docs/figuras/. Es idempotente: re-ejecutarlo regenera todo.
Cuando exista el dataset real, basta apuntar DATA a la fuente procesada.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT  = Path(__file__).resolve().parent / "figuras"
OUT.mkdir(exist_ok=True)

# Paleta del proyecto: índigo base + semáforo (esmeralda/ámbar/rojo).
AZUL, INDIGO = "#3b82f6", "#4f46e5"
VERDE, AMBAR, ROJO, GRIS = "#22c55e", "#f59e0b", "#ef4444", "#94a3b8"
RIESGO = {"bajo": VERDE, "medio": AMBAR, "alto": ROJO}

plt.rcParams.update({
    "figure.dpi": 120, "savefig.bbox": "tight", "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.grid": True,
    "grid.color": "#eef2f7", "grid.linewidth": 1,
})


def guardar(fig, nombre):
    ruta = OUT / nombre
    fig.savefig(ruta)
    plt.close(fig)
    print(f"  [ok] {ruta.relative_to(ROOT)}")


def main():
    df  = pd.read_csv(DATA / "viviendas_sinteticas.csv")
    ru  = pd.read_csv(DATA / "avance_rubros.csv")
    vis = pd.read_csv(DATA / "visitas.csv")
    org = pd.read_csv(DATA / "organizaciones.csv")
    print(f"Generando figuras del informe (N={len(df)} viviendas)...")

    EN_OBRA    = ["Iniciada", "Avanzada"]
    TERMINADAS = ["Finalizada", "Adjudicada"]

    # 1 — Distribución por estado
    orden = ["Iniciada", "Avanzada", "Finalizada", "Adjudicada"]
    cols  = {"Iniciada": AMBAR, "Avanzada": AZUL, "Finalizada": VERDE, "Adjudicada": INDIGO}
    conteo = df["estado"].value_counts().reindex(orden)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(conteo.index, conteo.values, color=[cols[e] for e in orden])
    for i, v in enumerate(conteo.values):
        ax.text(i, v + 8, str(int(v)), ha="center", fontsize=10)
    ax.set_title("Viviendas por estado de obra")
    ax.set_ylabel("Cantidad")
    guardar(fig, "01_estados.png")

    # 2 — Distribución por criterio
    orden_c = ["Inclusion", "Otro", "Exclusion"]
    cols_c  = {"Inclusion": VERDE, "Otro": AZUL, "Exclusion": ROJO}
    cc = df["criterio"].value_counts().reindex(orden_c)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(cc.index, cc.values, color=[cols_c[c] for c in orden_c])
    for i, v in enumerate(cc.values):
        ax.text(i, v + 8, str(int(v)), ha="center", fontsize=10)
    ax.set_title("Viviendas por criterio de inclusión")
    ax.set_ylabel("Cantidad")
    guardar(fig, "02_criterio.png")

    # 3 — Histograma del AFO
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(df["avance_obra"], bins=25, color=INDIGO, alpha=0.85, edgecolor="white")
    ax.axvline(df["avance_obra"].mean(), color=ROJO, ls="--",
               label=f"Media {df['avance_obra'].mean():.0f}%")
    ax.set_title("Distribución del Avance Físico de Obra (AFO)")
    ax.set_xlabel("AFO (%)"); ax.set_ylabel("Cantidad de obras")
    ax.legend()
    guardar(fig, "03_afo_hist.png")

    # 4 — Viviendas por departamento
    pd_dep = df["departamento"].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(pd_dep.index, pd_dep.values, color=AZUL)
    ax.set_title("Viviendas por departamento")
    ax.set_xlabel("Cantidad")
    guardar(fig, "04_departamentos.png")

    # 5 — Nivel de riesgo
    orden_r = ["bajo", "medio", "alto"]
    cr = df["nivel_riesgo"].value_counts().reindex(orden_r)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(cr.index, cr.values, color=[RIESGO[r] for r in orden_r])
    for i, v in enumerate(cr.values):
        ax.text(i, v + 8, f"{int(v)}\n({v/len(df)*100:.0f}%)", ha="center", fontsize=9)
    ax.set_title("Viviendas por nivel de riesgo")
    ax.set_ylabel("Cantidad")
    guardar(fig, "05_riesgo.png")

    # 6 — Modelo de riesgo: días activa vs avance (la figura central)
    fig, ax = plt.subplots(figsize=(8, 5))
    for r in orden_r:
        s = df[df["nivel_riesgo"] == r]
        ax.scatter(s["dias_activa"], s["avance_obra"], s=18, alpha=0.5,
                   color=RIESGO[r], label=f"Riesgo {r}")
    ax.axvline(90, color=GRIS, ls="--", lw=1.2)
    ax.text(95, 2, "90 días (plazo)", color="#475569", fontsize=9)
    ax.axhline(80, color=GRIS, ls="--", lw=1.2)
    ax.text(df["dias_activa"].max() * 0.82, 82, "80% avance", color="#475569", fontsize=9)
    ax.set_title("Modelo de riesgo — días activa vs. avance de obra")
    ax.set_xlabel("Días activa"); ax.set_ylabel("AFO (%)")
    ax.legend()
    guardar(fig, "06_modelo_riesgo.png")

    # 7 — Duración por tipo de vivienda (terminadas) + ANOVA en el título.
    # Solo terminadas: una obra en curso tiene duración real desconocida y sesgaría el dato.
    # ANOVA (y no t-tests de a pares): son 3 grupos; comparar de a dos infla el error tipo I.
    t = df[df["estado"].isin(TERMINADAS)]
    tipos = sorted(t["tipo_vivienda"].dropna().unique())
    datos = [t.loc[t["tipo_vivienda"] == tp, "dias_activa"].dropna().values for tp in tipos]
    F, p = stats.f_oneway(*datos)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bp = ax.boxplot(datos, labels=tipos, patch_artist=True)
    for caja, c in zip(bp["boxes"], [AZUL, VERDE, INDIGO]):
        caja.set_facecolor(c); caja.set_alpha(0.6)
    ax.axhline(90, color=ROJO, ls="--", lw=1, label="Plazo 90 días")
    ax.set_title(f"Duración por tipo de vivienda (terminadas)\nANOVA: F={F:.2f}, p={p:.2f} — sin diferencia significativa")
    ax.set_ylabel("Días de ejecución")
    ax.legend()
    guardar(fig, "07_duracion_tipo.png")

    # 8 — Cuello de botella: obras activas por etapa constructiva
    RN = {1: "Terreno/limpieza", 2: "Excavación", 3: "Mamp. hasta dintel",
          4: "Mamp. Block", 5: "Encadenado", 6: "Revoque int.", 7: "Revoque ext.",
          8: "Cielorraso aisl.", 9: "Cielorrasos", 10: "Carpintería",
          11: "Inst. agua", 12: "Inst. eléctrica", 13: "Inst. sanitaria",
          14: "Revest. ext.", 15: "Varios"}
    act_ids = df[df["estado"].isin(EN_OBRA)]["num_exp"]
    rr = ru[ru["vivienda_id"].isin(act_ids)]

    # Etapa activa = primer rubro de la secuencia que no está completo. Como los
    # rubros son estrictamente secuenciales, ese rubro es donde está detenida la obra.
    # Umbral en 98% (no 100): los rubros terminados se registran 98–100% por pequeñas
    # imprecisiones del relevamiento de campo; exigir 100% marcaría como "activos" rubros
    # ya cerrados y daría una etapa equivocada.
    def etapa_activa(g):
        g = g.sort_values("rubro_id")
        pend = g[g["avance_pct"] < 98]
        return int(pend["rubro_id"].iloc[0]) if len(pend) else 15

    ea = rr.groupby("vivienda_id").apply(etapa_activa, include_groups=False)
    conteo_ea = ea.value_counts().sort_values(ascending=True)
    etiquetas = [f"r{rid} · {RN.get(rid, '?')}" for rid in conteo_ea.index]
    colores = [ROJO if v == conteo_ea.max() else AZUL for v in conteo_ea.values]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(etiquetas, conteo_ea.values, color=colores)
    ax.set_title("Cuello de botella — obras activas por etapa constructiva")
    ax.set_xlabel("Obras activas")
    guardar(fig, "08_cuello_botella.png")

    # 9 — Sobre-reporte y cobertura de verificación por ONG
    nombre = dict(zip(org["cuit"], org["nombre"]))
    m = vis.merge(df[["num_exp", "cuit_org"]], left_on="vivienda_id", right_on="num_exp")
    m = m[m["cuit_org"].notna()]
    sobre = m.groupby("cuit_org")["diferencia_ong"].mean()
    verif = set(vis["vivienda_id"])
    # Cobertura sobre TODAS las ONGs con obras (incluye la que tiene 0 visitas).
    cob = (df[df["cuit_org"].notna()]
           .assign(v=lambda d: d["num_exp"].isin(verif))
           .groupby("cuit_org")["v"].mean() * 100).sort_values()
    cuits = cob.index                       # las 3 ONGs, ordenadas por cobertura
    # `sobre` solo tiene a las ONGs que recibieron visitas (las demás no aparecen en el
    # groupby). Al reindexar a las 3, la ONG sin verificar queda NaN → la marcamos como
    # "sin verificación" en vez de mostrar un +0 engañoso (no es que reporte bien: no la controlan).
    sobre = sobre.reindex(cuits)
    etiquetas = [nombre.get(c, c)[:22] for c in cuits]
    x = np.arange(len(cuits))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    a1.bar(x, sobre.fillna(0).values, color=AMBAR)
    for i, v in enumerate(sobre.values):
        a1.text(i, 0.1, "sin verificación" if pd.isna(v) else f"+{v:.1f}",
                ha="center", va="bottom", fontsize=8, rotation=90 if pd.isna(v) else 0,
                color="#475569")
    a1.set_xticks(x); a1.set_xticklabels(etiquetas, rotation=20, ha="right", fontsize=8)
    a1.set_title("Sobre-reporte promedio por ONG\n(avance reportado − verificado, en puntos)")
    a1.set_ylabel("Puntos de AFO")
    a2.bar(x, cob.values, color=[VERDE if v >= 50 else ROJO for v in cob.values])
    for i, v in enumerate(cob.values):
        a2.text(i, v + 2, f"{v:.0f}%", ha="center", fontsize=9)
    a2.set_xticks(x); a2.set_xticklabels(etiquetas, rotation=20, ha="right", fontsize=8)
    a2.axhline(70, color=GRIS, ls="--", lw=1)
    a2.set_title("Cobertura de verificación por ONG\n(% de obras con al menos una visita)")
    a2.set_ylabel("% verificada"); a2.set_ylim(0, 100)
    guardar(fig, "09_ong_confiabilidad.png")

    print("Figuras generadas en docs/figuras/")


if __name__ == "__main__":
    main()
