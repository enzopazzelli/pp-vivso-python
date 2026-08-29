"""Distancias, tiempos de viaje, y la base de partida de cada técnico."""
import math

from rutas.parametros import FACTOR_RUTA, VELOCIDAD_PROMEDIO_KMH
from rutas.tipos import Punto


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distancia en línea recta entre dos coordenadas, en kilómetros."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def tiempo_viaje_horas(a: Punto, b: Punto) -> float:
    """
    Horas de viaje entre dos puntos.

    No hay red vial real disponible (sin datos de caminos ni un servicio de
    ruteo): se aproxima con la distancia en línea recta, corregida por
    FACTOR_RUTA [R2] porque los caminos rurales no son rectos.
    """
    km = haversine_km(a.lat, a.lng, b.lat, b.lng) * FACTOR_RUTA
    return km / VELOCIDAD_PROMEDIO_KMH


def base_tecnico(departamentos: str) -> Punto:
    """
    Punto de partida y llegada de los viajes de un técnico [R8]: la cabecera del
    primer departamento de su zona de cobertura, tomada del mismo catálogo que usa
    el generador de datos.

    Import perezoso a propósito: synthetic.generate carga Faker y el resto del
    generador de datos solo para leer esta tabla — mismo motivo que en
    vision/simulacion.py con [S8]. `rutas/` tiene que poder correr en el dashboard
    desplegado sin ese costo.
    """
    from synthetic.generate import LOCALIDADES

    primer_depto = departamentos.split(",")[0].strip()
    loc = next((l for l in LOCALIDADES if l["departamento"] == primer_depto), None)
    if loc is None:
        raise ValueError(
            f"Departamento '{primer_depto}' no está en synthetic.generate.LOCALIDADES"
        )
    return Punto(
        lat=loc["lat"], lng=loc["lng"], localidad=loc["localidad"],
        departamento=primer_depto, num_exp=None, urgente=False,
        nivel_riesgo=None, estado_visita=None,
    )
