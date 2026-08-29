"""
Supuestos de diseño del generador de rutas, como constantes nombradas.

Mismo criterio que vision/rubrica.py: este componente es un plus que excede la
obligación de PP3 (docs/supuestos-abiertos.md §1), así que se construye sobre
supuestos sin consultarlos antes con el área. La condición que lo sostiene es la
misma — cada supuesto vive acá arriba, nombrado, para que refinarlo sea cambiar
un renglón y no reescribir código.

Convención `[R#]` (Rutas), paralela a los `[S#]` del dataset y los `[V#]` de
verificación fotográfica.
"""

# [R1] Velocidad promedio de viaje en rutas provinciales y caminos rurales de
#      Santiago del Estero — no autopista: incluye tramos de tierra y paradas.
VELOCIDAD_PROMEDIO_KMH = 55.0

# [R2] No hay red vial real disponible (sin OSRM ni datos de caminos), así que la
#      distancia se aproxima con línea recta (haversine) corregida por este factor:
#      los caminos no son rectos. 1.35 es una corrección moderada para una provincia
#      con trama vial dispersa, no una grilla urbana densa.
FACTOR_RUTA = 1.35

# [R3] Tiempo que insume una visita técnica en el lugar: inspección de obra +
#      planilla. No es el tiempo de viaje, es el tiempo parado en la obra.
TIEMPO_POR_VISITA_HORAS = 1.0

# [R4] Horas de trabajo de una jornada completa en terreno.
HORAS_JORNADA = 8.0

# [R5] En el día de salida y en el de regreso de un viaje, no se dispone de la
#      jornada completa: una parte del día se va en el traslado inicial o final
#      entre la base y la zona de trabajo. Se modela como una fracción fija de la
#      jornada, no como un cálculo de traslado aparte, para mantener la plantilla
#      simple y explicable.
FRACCION_DIA_PARCIAL = 0.5

# [R6] Umbral para "aprovechar" una parada no urgente en modo mezcla: se admite si
#      el desvío marginal que agrega a la ruta no supera esta fracción del
#      presupuesto horario TOTAL del viaje. Se mide contra el total del viaje (no
#      contra lo ya recorrido) para que el umbral tenga sentido incluso cuando la
#      ruta todavía no tiene ninguna parada urgente cargada.
UMBRAL_DESVIO_FRACCION_VIAJE = 0.10

# [R7] Modos de selección — mapean directo a lo que pidió el equipo: "mezclando
#      algunas de urgencia y otras no" o "todas de urgencia".
MODO_MEZCLA         = "mezcla"
MODO_SOLO_URGENTES  = "solo_urgentes"

# [R7] Plantillas de viaje: "N noches" define cuántos días dura el viaje y cuántos
#      son jornada completa. días_totales = noches + 1; de esos, el primero y el
#      último son parciales (viaje de ida/vuelta) y el resto son jornada completa.
#      "2 y 1" → 2 noches, 1 día completo (salida parcial, 1 completo, regreso parcial).
#      "3 y 2" → 3 noches, 2 días completos.
VIAJE_CORTO = {"nombre": "2 y 1", "noches": 2}
VIAJE_LARGO = {"nombre": "3 y 2", "noches": 3}
PLANTILLAS  = [VIAJE_CORTO, VIAJE_LARGO]

# [R8] Base de un técnico: la cabecera del PRIMER departamento de su zona de
#      cobertura (tecnico.departamentos, ej. "Capital,Banda,Silípica" → Capital).
#      Es un supuesto de conveniencia: el dataset no tiene domicilio real del
#      técnico. Ver rutas/geografia.py:base_tecnico().
