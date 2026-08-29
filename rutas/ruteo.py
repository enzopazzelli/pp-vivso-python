"""
Construcción de la ruta y su reparto en días.

Regla transparente, no caja negra — mismo criterio que el modelo de riesgo y la
capa de decisión de vision/: dos heurísticas simples y explicables (vecino más
cercano + inserción más barata), no un solver de ruteo. Un técnico tiene que poder
mirar el resultado y entender por qué el sistema eligió ese orden.
"""
from dataclasses import dataclass, field
from typing import Callable, List

from rutas.parametros import (
    FRACCION_DIA_PARCIAL,
    HORAS_JORNADA,
    MODO_MEZCLA,
    TIEMPO_POR_VISITA_HORAS,
    UMBRAL_DESVIO_FRACCION_VIAJE,
)
from rutas.tipos import Punto

TiempoViajeFn = Callable[[Punto, Punto], float]


@dataclass
class Dia:
    numero: int
    paradas: List[Punto]
    horas_usadas: float
    presupuesto: float
    pernocta_en: Punto | None   # None en el último día: esa noche ya está en la base


def presupuesto_por_dia(plantilla: dict) -> list[float]:
    """
    Horas disponibles cada día del viaje, según [R5]: el primero y el último son
    parciales (viaje de ida/vuelta desde la base); el resto, jornada completa.

    "2 y 1" (2 días, 1 noche) → [parcial, parcial] = 0 días completos, solo ida y vuelta.
    "3 y 2" (3 días, 2 noches) → [parcial, completo, parcial] = 1 día completo.
    """
    dias_totales = plantilla["noches"] + 1
    parcial = HORAS_JORNADA * FRACCION_DIA_PARCIAL
    if dias_totales <= 1:
        return [HORAS_JORNADA]
    completos = dias_totales - 2
    return [parcial] + [HORAS_JORNADA] * completos + [parcial]


def _costo_insertar(ruta: list[Punto], pos: int, candidato: Punto,
                    tiempo_viaje: TiempoViajeFn) -> float:
    """
    Cuánto más larga queda la ruta cerrada si se inserta `candidato` justo después
    de `ruta[pos]`. `ruta` siempre es un ciclo cerrado [base, v1, ..., vk, base],
    así que esta misma fórmula sirve tanto para extender el final del viaje (vecino
    más cercano) como para insertar en el medio (aprovechar una parada de paso):
    la diferencia es solo qué posiciones se prueban.
    """
    antes, despues = ruta[pos], ruta[pos + 1]
    return (tiempo_viaje(antes, candidato) + tiempo_viaje(candidato, despues)
            - tiempo_viaje(antes, despues) + TIEMPO_POR_VISITA_HORAS)


def construir_ruta(
    base: Punto,
    urgentes: list[Punto],
    no_urgentes: list[Punto],
    horas_totales: float,
    modo: str,
    tiempo_viaje: TiempoViajeFn,
) -> tuple[list[Punto], float]:
    """
    Arma la ruta del viaje como un ciclo [base, ..., base].

    Fase 1 — vecino más cercano sobre las urgentes: en cada paso se agrega, al
    final del recorrido, la urgente que menos alargue el viaje completo (ida +
    vuelta a la base incluida). Para en cuanto agregar la siguiente no entraría en
    el presupuesto horario del viaje.

    Fase 2 — en modo mezcla, inserción más barata sobre las no urgentes: para cada
    una se busca la mejor posición para sumarla (no tiene que ir al final; puede
    colarse entre dos paradas ya planificadas si está de paso). Se acepta si el
    desvío que agrega es chico [R6] o si la ruta todavía está vacía — esto último
    para que el modo mezcla arme un viaje igual cuando el técnico no tiene ninguna
    urgente pendiente, en vez de no proponer nada.
    """
    ruta = [base, base]
    costo_total = 0.0
    urgentes, no_urgentes = list(urgentes), list(no_urgentes)

    while urgentes:
        pos = len(ruta) - 2
        candidato = min(urgentes, key=lambda c: _costo_insertar(ruta, pos, c, tiempo_viaje))
        costo = _costo_insertar(ruta, pos, candidato, tiempo_viaje)
        if costo_total + costo > horas_totales:
            break
        ruta.insert(pos + 1, candidato)
        costo_total += costo
        urgentes.remove(candidato)

    if modo == MODO_MEZCLA:
        agregado = True
        while agregado and no_urgentes:
            agregado = False
            mejor = min(
                ((c, pos, _costo_insertar(ruta, pos, c, tiempo_viaje))
                 for c in no_urgentes for pos in range(len(ruta) - 1)),
                key=lambda t: t[2],
            )
            candidato, pos, costo = mejor
            ruta_vacia = len(ruta) == 2
            desvio_chico = costo <= UMBRAL_DESVIO_FRACCION_VIAJE * horas_totales
            if costo_total + costo <= horas_totales and (ruta_vacia or desvio_chico):
                ruta.insert(pos + 1, candidato)
                costo_total += costo
                no_urgentes.remove(candidato)
                agregado = True

    return ruta, costo_total


def partir_en_dias(ruta: list[Punto], plantilla: dict, tiempo_viaje: TiempoViajeFn) -> list[Dia]:
    """
    Reparte una ruta ya armada en los días de la plantilla de viaje.

    Va acumulando paradas en el día actual hasta que la siguiente no entraría en
    su presupuesto horario, y recién ahí pasa al día siguiente — nunca dentro del
    mismo día. La primera parada de un día se agrega siempre, aunque exceda un
    poco el presupuesto: es preferible eso a un día vacío por una parada lejana.
    """
    base = ruta[0]
    paradas = ruta[1:-1]
    presupuestos = presupuesto_por_dia(plantilla)

    dias: list[Dia] = []
    idx = 0
    punto_actual = base
    for numero, presupuesto in enumerate(presupuestos, start=1):
        paradas_dia: list[Punto] = []
        horas_dia = 0.0
        while idx < len(paradas):
            siguiente = paradas[idx]
            costo = tiempo_viaje(punto_actual, siguiente) + TIEMPO_POR_VISITA_HORAS
            if paradas_dia and horas_dia + costo > presupuesto:
                break
            horas_dia += costo
            paradas_dia.append(siguiente)
            punto_actual = siguiente
            idx += 1
        dias.append(Dia(numero=numero, paradas=paradas_dia, horas_usadas=horas_dia,
                        presupuesto=presupuesto, pernocta_en=punto_actual))
        if idx >= len(paradas):
            break

    if dias:
        dias[-1].horas_usadas += tiempo_viaje(punto_actual, base)
        dias[-1].pernocta_en = None   # vuelve a la base ese mismo día

    return dias
