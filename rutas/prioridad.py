"""
Clasifica las obras pendientes de un técnico en candidatas a viaje, y separa
urgentes de no urgentes.

La clasificación de "estado_visita" reproduce la de dashboard/pages/05_mis_obras.py
a propósito — es la misma cola de trabajo que ya ve el técnico, no una nueva. Se
duplica en vez de importarse porque 05_mis_obras.py es un script de Streamlit (su
sola importación ejecutaría toda la página); si esa clasificación cambia ahí,
cambiar acá también.
"""
import pandas as pd

# Una obra "Completo" o "Finalizada" no es candidata a viaje: ya no hace falta
# visitarla. Solo estos dos estados quedan pendientes.
PENDIENTES = {"Sin visitar", "Falta 2da visita"}

# Urgente = pendiente de visitar Y con nivel de riesgo alto o medio. Reutiliza la
# misma noción de riesgo que ya está en el dashboard — no inventa un score nuevo.
RIESGO_URGENTE = {"alto", "medio"}


def clasificar_pendiente(row) -> str:
    """Misma regla que 05_mis_obras.py:clasificar_pendiente — ver docstring del módulo."""
    if row["estado"] in ("Finalizada", "Adjudicada"):
        return "Finalizada"
    if row["visitas"] == 0:
        return "Sin visitar"
    if row["visitas"] == 1:
        return "Falta 2da visita"
    return "Completo"


def candidatos_viaje(df_viv_tecnico: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra a las obras que todavía necesitan una visita y marca cuáles son urgentes.

    Espera un DataFrame ya con `estado_visita` calculada (ver clasificar_pendiente
    o dashboard/pages/05_mis_obras.py, que arma esa columna igual). Devuelve una
    copia con la columna `urgente` agregada, filtrada a las pendientes.
    """
    df = df_viv_tecnico[df_viv_tecnico["estado_visita"].isin(PENDIENTES)].copy()
    df["urgente"] = df["nivel_riesgo"].isin(RIESGO_URGENTE)
    return df
