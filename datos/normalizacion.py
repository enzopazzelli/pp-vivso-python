"""Normalización de textos: nombres de organización, tipo de gestora y números de expediente."""
import re
import unicodedata

# Abreviaturas que VISOC escribe de distintas formas. Solo se reemplaza la palabra completa.
_ABREVIATURAS = {
    "ASOC": "ASOCIACION", "CIV": "CIVIL", "COOP": "COOPERATIVA", "COM": "COMISION",
    "MUN": "MUNICIPAL", "FOM": "FOMENTO", "VEC": "VECINAL",
}

# Mismas reglas que usa el informe OG/ONG (informe_ong_og_2026/procesar_informe.py).
# Los «\b» son obligatorios: sin el de `_MUNICIPIO`, «COMUN.DE» (de una asociación) se leería como municipio.
_COMISION = re.compile(r"COM\.?\s*MUN\b|COMISI[OÓ]N\s+MUNICIPAL\b|COMISIONADO\s+MUNICIPAL")
_MUNICIPIO = re.compile(r"\bMUNICIPALID|\bMUN\.\s*DE|\bMUNICIPIO\b")


def normalizar_texto(texto: str) -> str:
    """Mayúsculas, sin tildes, sin puntuación y con los espacios colapsados."""
    sin_tildes = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    solo_alfanumerico = re.sub(r"[^A-Za-z0-9 ]", " ", sin_tildes)
    return re.sub(r"\s+", " ", solo_alfanumerico).strip().upper()


def normalizar_organizacion(nombre: str) -> str:
    """Como `normalizar_texto`, y además unifica abreviaturas (ASOC. = ASOCIACION)."""
    return " ".join(_ABREVIATURAS.get(palabra, palabra) for palabra in normalizar_texto(nombre).split())


def tipo_gestora_por_nombre(nombre: str) -> str:
    """Deduce el tipo de gestora del texto. Cooperativas y asociaciones quedan como ONG."""
    mayusculas = (nombre or "").upper()
    if _COMISION.search(mayusculas):
        return "Comisión Municipal"
    if _MUNICIPIO.search(mayusculas):
        return "Municipio"
    return "ONG"


def normalizar_expediente(numero: str) -> str:
    """Sin espacios y en mayúsculas. Conviven varios formatos y se conservan tal cual."""
    return re.sub(r"\s+", "", numero or "").upper()


# Los formatos de expediente que ya conocemos (sección 4.3 de la especificación). Los números de
# reclamo o de acta digital no siguen ninguno de estos: quedan «desconocido», no se fuerza un formato.
_FORMATOS_EXPEDIENTE = [
    (re.compile(r"^\d{3,6}-\d{2}-\d{4}$"), "NNNNN-NN-NNNN"),
    (re.compile(r"^\d{5,8}-\d{4}$"), "NNNNNNN-AAAA"),
    (re.compile(r"^EX-\d{4}-.+$"), "EX-AAAA-…"),
]


def clasificar_formato_expediente(numero: str) -> str:
    """La forma de un número de expediente, o «desconocido» si no coincide con ninguna conocida."""
    numero = normalizar_expediente(numero)
    for patron, nombre in _FORMATOS_EXPEDIENTE:
        if patron.match(numero):
            return nombre
    return "desconocido"
