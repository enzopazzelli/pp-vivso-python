"""Anonimización de nombres de personas: seudónimos legibles y consistentes.

Se aplica ANTES de guardar cualquier dato. La misma persona recibe siempre el mismo seudónimo
(mientras no cambie la clave), así se pueden seguir casos sin saber quién es.
"""
import hashlib
import hmac
import re

from faker import Faker

from datos.normalizacion import normalizar_texto as normalizar_persona  # noqa: F401  (se reexporta)

# Números de 7 u 8 cifras, con o sin puntos. Solo para texto libre: un expediente de 7 cifras
# también coincidiría, así que NO se usa sobre campos ya estructurados.
_DNI = re.compile(r"(?<!\d)\d{1,2}\.?\d{3}\.?\d{3}(?!\d)")


def limpiar_dni(texto: str) -> str:
    return _DNI.sub("[DNI]", texto)


class Anonimizador:
    """Convierte un nombre real en un seudónimo. No guarda ni registra el nombre original."""

    def __init__(self, secreto: str):
        if not secreto or len(secreto) < 16:
            raise ValueError("La clave de anonimización debe tener al menos 16 caracteres")
        self._clave = secreto.encode("utf-8")

    def huella(self, nombre: str) -> str:
        """Huella HMAC del nombre normalizado. No se puede revertir sin la clave."""
        normalizado = normalizar_persona(nombre)
        return hmac.new(self._clave, normalizado.encode("utf-8"), hashlib.sha256).hexdigest()[:16]

    def seudonimo(self, nombre: str) -> str:
        """Nombre inventado, siempre el mismo para la misma persona. Termina con 4 caracteres de la
        huella para distinguir a dos personas a las que Faker les inventara el mismo nombre."""
        if not normalizar_persona(nombre):
            return ""
        huella = self.huella(nombre)
        generador = Faker("es_AR")
        generador.seed_instance(int(huella, 16))
        return f"{generador.name()} · {huella[:4]}"

    __call__ = seudonimo
