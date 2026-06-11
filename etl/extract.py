"""
Carga datos desde la API Java o, si no está disponible, desde los archivos
locales generados por synthetic/generate.py.

La lógica es siempre la misma para quien llama: recibe un DataFrame.
La fuente es transparente.
"""
import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("VIVSO_API_URL", "")

# Rutas siempre relativas a la raíz del proyecto, no al directorio desde donde
# se ejecuta el script o el notebook.
_ROOT    = Path(__file__).resolve().parent.parent
CSV_VIV  = _ROOT / "data" / "viviendas_sinteticas.csv"
CSV_ORGS = _ROOT / "data" / "organizaciones.csv"


def cargar_viviendas() -> tuple[pd.DataFrame, str]:
    """
    Devuelve (DataFrame, fuente) donde fuente es "api" o "local".
    Intentar la API primero. Si falla o no está configurada, usar CSV local.
    """
    if API_URL:
        try:
            resp = requests.get(f"{API_URL}/vivienda", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            df   = pd.DataFrame(data)
            # La API Java usa camelCase; normalizar a snake_case para consistencia
            df = df.rename(columns={
                "numExp":        "num_exp",
                "fechaInic":     "fecha_inic",
                "fechaFin":      "fecha_fin",
                "avanceObra":    "avance_obra",
                "tipoVivienda":  "tipo_vivienda",
                "cantDormitorios": "cant_dormitorios",
                "id_familia":    "id_familia",
            })
            return df, "api"
        except Exception as e:
            print(f"API no disponible ({e}). Usando datos locales.")

    if not os.path.exists(CSV_VIV):
        raise FileNotFoundError(
            "No hay datos locales. Ejecutar primero: python -m synthetic.generate"
        )
    return pd.read_csv(CSV_VIV), "local"


def cargar_organizaciones() -> tuple[pd.DataFrame, str]:
    """Mismo patrón que cargar_viviendas."""
    if API_URL:
        try:
            resp = requests.get(f"{API_URL}/organizacion/listar", timeout=5)
            resp.raise_for_status()
            return pd.DataFrame(resp.json()), "api"
        except Exception as e:
            print(f"API no disponible ({e}). Usando datos locales.")

    if not os.path.exists(CSV_ORGS):
        raise FileNotFoundError(
            "No hay datos locales. Ejecutar primero: python -m synthetic.generate"
        )
    return pd.read_csv(CSV_ORGS), "local"
