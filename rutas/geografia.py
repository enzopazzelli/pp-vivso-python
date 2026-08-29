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


# [R8] La base de todo técnico es Santiago Capital, donde está el ministerio — no
#      la zona que cubre. Corregido 2026-08-29 (antes se asumía la cabecera del
#      primer departamento de su cobertura, un supuesto de conveniencia sin
#      respaldo). El técnico recorre distancia real desde el ministerio hasta su
#      zona antes de empezar a visitar, y eso es justamente lo que hace largos a
#      los viajes de varios días — no es un costo a minimizar, es el punto de
#      partida real.
DEPARTAMENTO_BASE = "Capital"


def base_tecnico(departamentos: str) -> Punto:
    """
    Punto de partida y llegada de los viajes de un técnico [R8]: siempre Santiago
    Capital, sin importar qué departamentos cubra. El parámetro `departamentos` no
    se usa para elegir la base — se conserva en la firma porque el resto de
    `rutas/` ya lo pasa, y porque un cambio futuro (ej. bases regionales) solo
    tendría que tocar esta función.

    Import perezoso a propósito: synthetic.generate carga Faker y el resto del
    generador de datos solo para leer esta tabla — mismo motivo que en
    vision/simulacion.py con [S8]. `rutas/` tiene que poder correr en el dashboard
    desplegado sin ese costo.
    """
    from synthetic.generate import LOCALIDADES

    loc = next((l for l in LOCALIDADES if l["departamento"] == DEPARTAMENTO_BASE), None)
    if loc is None:
        raise ValueError(f"'{DEPARTAMENTO_BASE}' no está en synthetic.generate.LOCALIDADES")
    return Punto(
        lat=loc["lat"], lng=loc["lng"], localidad=loc["localidad"],
        departamento=DEPARTAMENTO_BASE, num_exp=None, urgente=False,
        nivel_riesgo=None, estado_visita=None,
    )
