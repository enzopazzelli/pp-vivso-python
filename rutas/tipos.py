"""Tipo compartido entre geografia.py, ruteo.py y planificador.py."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Punto:
    """
    Una parada del viaje: una obra a visitar, o la base del técnico.

    La base se representa con el mismo tipo que una obra (num_exp=None) para que
    el cálculo de distancias no tenga que distinguir casos: cualquier Punto tiene
    lat/lng y eso alcanza para el ruteo.
    """
    lat: float
    lng: float
    localidad: str
    departamento: str
    num_exp: Optional[str]
    urgente: bool
    nivel_riesgo: Optional[str]
    estado_visita: Optional[str]

    @property
    def es_base(self) -> bool:
        return self.num_exp is None
