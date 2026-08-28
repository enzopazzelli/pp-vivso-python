"""
Rúbrica de evidencia observable: qué se ve en una foto cuando cada rubro del AFO
está terminado.

Es el insumo central del componente de verificación fotográfica; el diseño completo,
con el porqué de cada decisión, está en docs/vision-afo.md.

Todos los supuestos [V#] viven acá arriba como constantes nombradas. Es una condición
del diseño y no una preferencia de estilo: este componente se construye sobre supuestos
sin consultarlos con el área (docs/supuestos-abiertos.md §1), y esa postura solo es
sostenible si refinar un supuesto cuesta cambiar un renglón. Si alguno de estos valores
termina hundido dentro de una función, el componente pierde su principal defensa.
"""
from db.setup import RUBROS_CATALOGO

# ═══════════════════════════════════════════════════════════════════════════
# SUPUESTOS DE DISEÑO [V#] — no confirmados con el área, a propósito
# ═══════════════════════════════════════════════════════════════════════════
# Cada uno tiene su costo documentado en docs/supuestos-abiertos.md §2. El peor
# caso de toda esa tabla es que el beneficio sea menor: ninguno invalida el trabajo.

# [V2] El rubro 15 ("Varios") no tiene una manifestación visible propia, así que
#      la foto nunca puede confirmarlo. Poner esto en False si el área indica que
#      sí hay algo observable: sube la cobertura fotográfica del 87% al 90%.
V2_RUBRO_15_SIN_EVIDENCIA = True

# [V5] Tolerancia con la que se acepta que la lectura coincida con lo declarado.
#      Se expresa en rubros, no en puntos, porque los pesos son desparejos (3 a 10):
#      errar por un rubro cuesta distinto según dónde esté la obra.
V5_TOLERANCIA_RUBROS = 1

# [V6] ¿El plazo de 90 días se extiende tras un rechazo? El diseño está hecho para
#      no depender de la respuesta (docs/vision-afo.md §4.4); esto solo alimenta el
#      cálculo de plazo_efectivo cuando se implemente.
V6_PLAZO_SE_EXTIENDE_TRAS_RECHAZO = True

# [V7] ¿Existe hoy un registro consultable de los rechazos? Asumimos que no y lo
#      modelamos nosotros. Si resulta que ya existe, se conecta: menos trabajo.
V7_EXISTE_REGISTRO_DE_RECHAZO = False

# [V9] ¿El tope de 2 visitas por obra aplica también a las resoluciones por app?
#      Asumimos que no, porque el tope es una restricción logística de campo.
V9_TOPE_VISITAS_APLICA_A_APP = False

# [V10] ¿Una aprobación remota certifica el AFO y habilita el pago? Si resultara
#       que no, el sistema vuelve a ser triage: el mismo código rindiendo menos.
V10_APROBACION_REMOTA_CERTIFICA = True

# Umbral a partir del cual se considera que un rubro está terminado. Es el mismo
# criterio que ya usa el análisis de etapa activa, para que ambos hablen de lo mismo.
UMBRAL_RUBRO_COMPLETO = 98


# ═══════════════════════════════════════════════════════════════════════════
# Campos de evidencia observable
# ═══════════════════════════════════════════════════════════════════════════
# El modelo de visión NO responde "qué rubro es" ni "qué porcentaje hay": responde
# este checklist de hechos físicos. La conversión a rubro y a AFO la hace decision.py
# con el catálogo oficial de pesos. Esa separación es lo que mantiene el sistema
# explicable ante una gestora — el mismo criterio del modelo de riesgo.
#
# Todos los campos admiten "no_determinable": un sistema que siempre responde algo
# es un sistema en el que el técnico deja de confiar la tercera vez que se equivoca
# con una foto mala. La tasa de abstención es una métrica, no un fracaso.

CAMPOS_EVIDENCIA = {
    "terreno":               ["sin_preparar", "despejado"],
    "capa_aisladora":        ["si", "no"],
    "muros":                 ["ninguno", "fundacion", "hasta_dintel", "completo"],
    "encadenado":            ["si", "no"],
    "revoque_int":           ["ninguno", "grueso", "fino"],
    "revoque_ext":           ["ninguno", "grueso", "fino"],
    "cielorraso":            ["ninguno", "estructura", "terminado"],
    "aberturas":             ["vanos_vacios", "parcial", "colocadas"],
    "tanque_agua":           ["si", "no"],
    "tablero_electrico":     ["ninguno", "sin_bocas", "completo"],
    "artefactos_sanitarios": ["ninguno", "parcial", "completos"],
    "revestimiento_ext":     ["ninguno", "parcial", "terminado"],
}

NO_DETERMINABLE = "no_determinable"

TIPOS_DE_TOMA = ["fachada_completa", "interior", "detalle", "no_util"]


# ═══════════════════════════════════════════════════════════════════════════
# Qué evidencia confirma cada rubro
# ═══════════════════════════════════════════════════════════════════════════
# Regla clave del dominio: el AFO no mide trabajo enterrado, mide hitos con
# manifestación visible. Las mangueras de agua y electricidad van vacías y embutidas
# durante la mampostería —ese trabajo está absorbido en otros rubros—; los rubros 11
# y 12 certifican lo posterior y visible: tanque y conexiones, cables y tablero.
# Por eso el catálogo resulta auditable por foto casi por diseño.
#
# Formato: rubro_id -> (campo de evidencia, valores que lo dan por terminado)

CONFIRMA_RUBRO = {
    1:  ("terreno",               {"despejado"}),
    2:  ("capa_aisladora",        {"si"}),
    3:  ("muros",                 {"hasta_dintel", "completo"}),
    4:  ("muros",                 {"completo"}),
    5:  ("encadenado",            {"si"}),
    6:  ("revoque_int",           {"fino"}),
    7:  ("revoque_ext",           {"fino"}),
    8:  ("cielorraso",            {"estructura", "terminado"}),
    9:  ("cielorraso",            {"terminado"}),
    10: ("aberturas",             {"colocadas"}),
    11: ("tanque_agua",           {"si"}),
    12: ("tablero_electrico",     {"completo"}),
    13: ("artefactos_sanitarios", {"completos"}),
    14: ("revestimiento_ext",     {"terminado"}),
    15: (None, set()),   # [V2] sin manifestación visible propia
}

# Rubros cuya evidencia solo se ve durante una ventana temporal: después queda tapada.
# No los vuelve inverificables, pero obliga a que el protocolo de carga pida la foto
# en el momento. Son 10 puntos de AFO que dependen del protocolo, no del modelo.
RUBROS_VENTANA_TEMPORAL = {
    2: "La capa aisladora se ve solo antes de rellenar la excavación.",
    8: "El aislante térmico se ve solo antes de cerrar el cielorraso (rubro 9).",
}

# Descripción en lenguaje natural de qué se ve. Alimenta el prompt del modelo de
# visión y también la interfaz, para que técnico y modelo lean el mismo criterio.
EVIDENCIA_OBSERVABLE = {
    1:  "Terreno despejado, replanteo marcado, sin escombros.",
    2:  "Zanjas de cimiento abiertas; capa aisladora colocada sobre el cimiento.",
    3:  "Muros de ladrillo hasta ~2,10 m, con dinteles colocados sobre los vanos.",
    4:  "Muros cerrados por encima del dintel, hasta la altura final.",
    5:  "Viga de hormigón armado en la corona del muro, con el encofrado retirado.",
    6:  "Paredes interiores con revoque grueso y fino; el ladrillo ya no se ve.",
    7:  "Fachada revocada, sin ladrillo a la vista.",
    8:  "Estructura de cielorraso montada, con el aislante térmico colocado.",
    9:  "Cielorraso cerrado, terminado y pintado.",
    10: "Puertas y ventanas colocadas (los vanos ya no están vacíos), herrería puesta.",
    11: "Tanque de agua colocado, canillas y conexiones finales resueltas.",
    12: "Tablero eléctrico instalado, llaves y tomacorrientes colocados.",
    13: "Artefactos sanitarios colocados: inodoro, lavatorio, ducha.",
    14: "Fachada terminada, con revestimiento y pintura exterior.",
    15: "Sin manifestación visible propia — no se puede confirmar por foto.",
}

# Índice por id para no repetir búsquedas sobre la lista del catálogo.
RUBROS_POR_ID = {r["id"]: r for r in RUBROS_CATALOGO}
ORDEN_RUBROS = [r["id"] for r in sorted(RUBROS_CATALOGO, key=lambda r: r["orden"])]


def peso_acumulado(rubro_id: int) -> int:
    """AFO que corresponde a tener terminados todos los rubros hasta `rubro_id`."""
    if rubro_id <= 0:
        return 0
    return sum(RUBROS_POR_ID[r]["peso_pct"] for r in ORDEN_RUBROS if r <= rubro_id)


def tolerancia_puntos(rubro_alcanzado: int) -> int:
    """
    Cuántos puntos de AFO de diferencia se aceptan antes de marcar contradicción.

    [V5] dice "un rubro de tolerancia", pero los pesos van de 3 a 10 puntos: convertir
    a puntos requiere saber en qué rubro está la obra. Se usa el peso del rubro que
    está en curso, que es exactamente el margen de error de leer mal por una etapa.
    """
    siguientes = [r for r in ORDEN_RUBROS if r > rubro_alcanzado]
    if not siguientes:
        return 0
    en_curso = siguientes[:V5_TOLERANCIA_RUBROS]
    return sum(RUBROS_POR_ID[r]["peso_pct"] for r in en_curso)


def prompt_sistema() -> str:
    """
    Construye el prompt del modelo de visión a partir del catálogo oficial.

    Se genera y no se escribe a mano para que la rúbrica no se duplique: si mañana
    cambia un rubro en db/setup.py, el prompt cambia solo. El modelo recibe el
    criterio completo pero se le pide únicamente el checklist de evidencia — nunca
    el porcentaje, que lo calcula decision.py.
    """
    lineas = [
        "Sos un asistente técnico que analiza fotos de obras de vivienda social en "
        "Santiago del Estero, Argentina.",
        "",
        "Tu tarea NO es estimar el porcentaje de avance. Tu tarea es reportar únicamente "
        "la EVIDENCIA FÍSICA OBSERVABLE en la foto, respetando el esquema de salida.",
        "",
        "El avance de obra (AFO) se compone de 15 rubros estrictamente secuenciales: el "
        "rubro N solo puede empezar cuando el N-1 está terminado. Este es el criterio de "
        "cada uno:",
        "",
    ]
    for rid in ORDEN_RUBROS:
        r = RUBROS_POR_ID[rid]
        nota = ""
        if rid in RUBROS_VENTANA_TEMPORAL:
            nota = f"  [Ventana temporal: {RUBROS_VENTANA_TEMPORAL[rid]}]"
        lineas.append(
            f"{rid:>2}. {r['nombre']} ({r['peso_pct']}%) — {EVIDENCIA_OBSERVABLE[rid]}{nota}"
        )

    lineas += [
        "",
        "Reglas de respuesta:",
        "- Reportá solo lo que se ve. Si un elemento no aparece en la foto o no se "
        "distingue, usá 'no_determinable'. Abstenerse es correcto; adivinar no.",
        "- Si la foto no muestra una vivienda en obra (es un detalle sin contexto, está "
        "muy oscura, o es de otra cosa), marcá tipo_toma = 'no_util'.",
        "- Una foto no distingue una obra construida por primera vez de una rehecha "
        "después de un rechazo. No intentes inferirlo: eso lo resuelve el registro.",
        "- En 'observaciones' podés señalar defectos visibles (fisuras, humedad, "
        "ejecución dudosa) como texto para el técnico. Nunca son un rechazo.",
    ]
    return "\n".join(lineas)
