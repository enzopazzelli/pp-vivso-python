"""Convierte un DataFrame a una lista de dict lista para responder en JSON.

No se usa el serializador por defecto de FastAPI (`jsonable_encoder`) porque no sabe qué hacer con
`NaN` ni con los objetos `date` sueltos que traen algunas columnas (ver «Verificación previa» del plan).
`DataFrame.to_json` sí los convierte bien: NaN -> null, date -> texto ISO.
"""
import json

import pandas as pd


def df_a_json(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))
