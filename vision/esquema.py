"""
Esquema de salida estructurada del modelo de visión.

Se genera a partir de CAMPOS_EVIDENCIA en vez de escribirse a mano: si mañana se
agrega un campo de evidencia, el esquema, el prompt y la capa de decisión quedan
sincronizados solos. Duplicarlo a mano es la forma más rápida de que el modelo
responda algo que la regla no sabe leer.
"""
from vision.rubrica import CAMPOS_EVIDENCIA, NO_DETERMINABLE, TIPOS_DE_TOMA


def _enum_campo(valores: list[str]) -> dict:
    """Todo campo de evidencia admite además 'no_determinable' (ver rubrica.py)."""
    return {"enum": [*valores, NO_DETERMINABLE]}


EVIDENCIA_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["tipo_toma", "evidencia", "confianza", "observaciones"],
    "properties": {
        "tipo_toma": {"enum": TIPOS_DE_TOMA},
        "evidencia": {
            "type": "object",
            "additionalProperties": False,
            "required": list(CAMPOS_EVIDENCIA),
            "properties": {c: _enum_campo(v) for c, v in CAMPOS_EVIDENCIA.items()},
        },
        "confianza": {"enum": ["alta", "media", "baja"]},
        "observaciones": {
            "type": "string",
            "description": "Defectos visibles para que los revise el técnico. Nunca un rechazo.",
        },
    },
}


def evidencia_vacia() -> dict:
    """Evidencia con todo en 'no_determinable' — el punto de partida seguro."""
    return {c: NO_DETERMINABLE for c in CAMPOS_EVIDENCIA}


def lectura_no_util(motivo: str = "") -> dict:
    """Respuesta canónica para una foto que no sirve, sin inventar evidencia."""
    return {
        "tipo_toma": "no_util",
        "evidencia": evidencia_vacia(),
        "confianza": "baja",
        "observaciones": motivo,
    }
