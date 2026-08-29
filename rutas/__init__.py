"""
Generador de rutas para viajes de técnicos — componente extra de Ciencia de Datos,
fuera de la obligación de PP3 (ver docs/supuestos-abiertos.md §1).

Un técnico visita obras en varios departamentos, muy separados entre sí. En vez de
un viaje de ida y vuelta por cada obra, este módulo arma un único viaje de varios
días ("2 y 1" o "3 y 2") que encadena varias visitas pendientes en una ruta
eficiente — priorizando las urgentes, y aprovechando el trayecto para sumar
pendientes no urgentes que queden de paso.

Arquitectura, mismo criterio que vision/: regla transparente, no caja negra.

    prioridad.py     →  qué obras son candidatas a viaje, cuáles son urgentes
    geografia.py     →  distancias, tiempos de viaje, base del técnico
    ruteo.py         →  arma la ruta (vecino más cercano + inserción más barata)
                         y la reparte en días
    planificador.py  →  orquesta todo: arma un viaje, o encadena varios

Los supuestos de diseño `[R#]` viven en parametros.py, como constantes nombradas.
Corre entero con el dataset existente — no necesita datos nuevos ni una API externa.
Ver `python -m rutas.demo`.
"""
from rutas.parametros import MODO_MEZCLA, MODO_SOLO_URGENTES, PLANTILLAS, VIAJE_CORTO, VIAJE_LARGO
from rutas.planificador import Viaje, armar_viaje, simular_proximos_viajes

__all__ = [
    "MODO_MEZCLA", "MODO_SOLO_URGENTES", "PLANTILLAS", "VIAJE_CORTO", "VIAJE_LARGO",
    "Viaje", "armar_viaje", "simular_proximos_viajes",
]
