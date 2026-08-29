"""
Arma un viaje completo para un técnico: filtra sus obras pendientes, arma la ruta
y la reparte en días. Es el punto de entrada del módulo.
"""
from dataclasses import dataclass

import pandas as pd

from rutas.geografia import base_tecnico, haversine_km, tiempo_viaje_horas
from rutas.parametros import FACTOR_RUTA, MODO_MEZCLA, TIEMPO_POR_VISITA_HORAS
from rutas.prioridad import candidatos_viaje
from rutas.ruteo import Dia, construir_ruta, partir_en_dias, presupuesto_por_dia
from rutas.tipos import Punto


@dataclass
class Viaje:
    tecnico: str
    plantilla: dict
    base: Punto
    dias: list[Dia]
    horas_totales: float
    km_totales: float
    urgentes_cubiertas: int
    no_urgentes_cubiertas: int
    urgentes_pendientes_fuera: int   # urgentes que NO entraron en este viaje
    horas_individual: float          # costo de visitar lo mismo una por una (§comparación)

    @property
    def paradas(self) -> list[Punto]:
        return [p for dia in self.dias for p in dia.paradas]

    @property
    def horas_ahorradas(self) -> float:
        return self.horas_individual - self.horas_totales


def _df_a_puntos(df: pd.DataFrame) -> list[Punto]:
    return [
        Punto(lat=r["lat"], lng=r["lng"], localidad=r["localidad"],
              departamento=r["departamento"], num_exp=r["num_exp"],
              urgente=bool(r["urgente"]), nivel_riesgo=r["nivel_riesgo"],
              estado_visita=r["estado_visita"])
        for _, r in df.iterrows()
    ]


def _distancia_ruta_km(ruta: list[Punto]) -> float:
    """Kilómetros totales de la ruta ya armada, recorriendo sus tramos en orden."""
    return sum(
        haversine_km(a.lat, a.lng, b.lat, b.lng) * FACTOR_RUTA
        for a, b in zip(ruta, ruta[1:])
    )


def _costo_individual(base: Punto, paradas: list[Punto]) -> float:
    """
    Costo de visitar cada parada por separado, ida y vuelta desde la base — el
    "as is" contra el que se mide la ganancia de agrupar en un viaje.
    """
    return sum(2 * tiempo_viaje_horas(base, p) + TIEMPO_POR_VISITA_HORAS for p in paradas)


def armar_viaje(
    df_viv_tecnico: pd.DataFrame,
    departamentos: str,
    nombre_tecnico: str,
    plantilla: dict,
    modo: str = MODO_MEZCLA,
) -> Viaje:
    """
    Arma un viaje para las obras pendientes de un técnico.

    `df_viv_tecnico` tiene que traer ya la columna `estado_visita` calculada
    (ver rutas.prioridad o dashboard/pages/05_mis_obras.py, que hacen lo mismo).
    """
    candidatos = candidatos_viaje(df_viv_tecnico)
    urgentes    = _df_a_puntos(candidatos[candidatos["urgente"]])
    no_urgentes = _df_a_puntos(candidatos[~candidatos["urgente"]])
    base = base_tecnico(departamentos)

    horas_totales_disponibles = sum(presupuesto_por_dia(plantilla))
    ruta, _ = construir_ruta(
        base, urgentes, no_urgentes, horas_totales_disponibles, modo, tiempo_viaje_horas
    )
    dias = partir_en_dias(ruta, plantilla, tiempo_viaje_horas)

    # `construir_ruta` respeta el presupuesto TOTAL del viaje, pero partir_en_dias
    # reparte ese total entre días con presupuestos distintos (parcial/completo) en
    # un orden fijo — una ruta que entra en el total puede no entrar día por día, y
    # partir_en_dias recorta la cola en ese caso. Por eso las paradas realmente
    # cubiertas son las que quedaron en `dias`, no las de `ruta`: cualquier otra
    # cuenta (urgentes cubiertas, km, comparación) tiene que salir de ahí para no
    # informar más paradas de las que el itinerario final realmente muestra.
    cubiertas = [p for dia in dias for p in dia.paradas]
    urgentes_cubiertas = sum(1 for p in cubiertas if p.urgente)

    return Viaje(
        tecnico=nombre_tecnico,
        plantilla=plantilla,
        base=base,
        dias=dias,
        horas_totales=sum(d.horas_usadas for d in dias),
        km_totales=_distancia_ruta_km([base, *cubiertas, base]),
        urgentes_cubiertas=urgentes_cubiertas,
        no_urgentes_cubiertas=len(cubiertas) - urgentes_cubiertas,
        urgentes_pendientes_fuera=len(urgentes) - urgentes_cubiertas,
        horas_individual=_costo_individual(base, cubiertas),
    )


def simular_proximos_viajes(
    df_viv_tecnico: pd.DataFrame,
    departamentos: str,
    nombre_tecnico: str,
    plantilla: dict,
    modo: str = MODO_MEZCLA,
    max_viajes: int = 3,
) -> list[Viaje]:
    """
    Encadena varios viajes seguidos sobre el mismo backlog: cada viaje excluye las
    obras que ya cubrió el anterior, simulando "¿cuántos viajes como este necesito
    para vaciar la cola de pendientes de hoy?". Para en cuanto no quedan
    pendientes o se llega a `max_viajes`.
    """
    pendientes = df_viv_tecnico.copy()
    viajes = []
    for _ in range(max_viajes):
        candidatos = candidatos_viaje(pendientes)
        if candidatos.empty:
            break
        viaje = armar_viaje(pendientes, departamentos, nombre_tecnico, plantilla, modo)
        if not viaje.paradas:
            break   # nada entró en el presupuesto del viaje (caso borde: sin candidatos alcanzables)
        viajes.append(viaje)
        cubiertas_ids = {p.num_exp for p in viaje.paradas}
        pendientes = pendientes[~pendientes["num_exp"].isin(cubiertas_ids)]
    return viajes
