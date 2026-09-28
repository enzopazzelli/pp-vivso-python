"""Interfaz común de los importadores y los objetos que intercambian."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


def fecha_corta(texto: str) -> date:
    """Convierte «dd/mm/aa» en una fecha (los reportes de VISOC usan año de 2 cifras)."""
    dia, mes, anio = texto.split("/")
    return date(2000 + int(anio), int(mes), int(dia))


@dataclass
class Chequeo:
    """Un control de la validación: por ejemplo «la suma de las filas coincide con el pie»."""
    nombre: str
    ok: bool
    detalle: str = ""


@dataclass
class Validacion:
    chequeos: list[Chequeo] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.chequeos)


@dataclass
class Lectura:
    """Lo que un importador leyó de un archivo: filas ya anonimizadas y los totales que el propio
    reporte declara, para poder validarlas."""
    tipo_reporte: str
    parametros: dict
    fecha_reporte: date | None
    filas: list[dict]
    totales_declarados: dict = field(default_factory=dict)
    advertencias: list[str] = field(default_factory=list)


class Importador(ABC):
    """Un importador por formato de reporte."""

    codigo: str                # el `tipo_reporte` que entiende
    version: str = "1"         # se guarda en cada importación; subirla al cambiar la lectura

    @abstractmethod
    def reconoce(self, ruta: Path) -> float:
        """De 0 a 1: qué tan seguro está de que el archivo es de su formato. Nunca debe fallar."""

    @abstractmethod
    def leer(self, ruta: Path, anonimizar, opciones: dict | None = None) -> Lectura:
        """Lee el archivo y devuelve las filas ya anonimizadas."""

    @abstractmethod
    def validar(self, lectura: Lectura) -> Validacion:
        """Controla la lectura contra los totales que declara el propio reporte."""

    @abstractmethod
    def mapear(self, lectura: Lectura, sesion, importacion) -> None:
        """Escribe la lectura (ya validada) en el modelo propio."""
