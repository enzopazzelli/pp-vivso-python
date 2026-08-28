"""
Capa de decisión: convierte evidencia física en rubro alcanzado, AFO y grado de
respaldo del reporte de la gestora.

Es determinista y no aprende nada. Toda la inteligencia estadística vive en la capa
de percepción; acá solo se aplican el catálogo oficial de pesos y dos restricciones
del dominio (secuencialidad y monotonía condicional). Esa separación es lo que
permite que el técnico vea "muros con encadenado y sin revoque → rubro 5 → AFO 33%"
en vez de un número salido de una caja negra — el mismo criterio con el que se
defendió el modelo de riesgo en Hito 3.
"""
from dataclasses import dataclass

from vision.rubrica import (
    CONFIRMA_RUBRO,
    NO_DETERMINABLE,
    ORDEN_RUBROS,
    RUBROS_POR_ID,
    V5_TOLERANCIA_RUBROS,
    peso_acumulado,
    tolerancia_puntos,
)


# ── Grados de respaldo documental del reporte ─────────────────────────────
# Son la salida del sistema: no se aprueba nada, se pondera lo que declaró la gestora.
RESPALDADO         = "respaldado"
SOBRE_REPORTE      = "contradicho_sobre_reporte"
SUB_REPORTE        = "contradicho_sub_reporte"
AVANCE_RECHAZADO   = "contradicho_avance_rechazado"
RETROCESO_SIN_EXPL = "retroceso_sin_explicacion"
SIN_RESPALDO       = "sin_respaldo"
NO_DETERMINABLE_G  = "no_determinable"

ETIQUETA_GRADO = {
    RESPALDADO:         "Respaldado",
    SOBRE_REPORTE:      "Contradicho — sobre-reporte",
    SUB_REPORTE:        "Contradicho — sub-reporte",
    AVANCE_RECHAZADO:   "Contradicho — avance rechazado",
    RETROCESO_SIN_EXPL: "Retroceso sin explicación",
    SIN_RESPALDO:       "Sin respaldo",
    NO_DETERMINABLE_G:  "No determinable",
}


@dataclass
class Lectura:
    """Resultado de leer una evidencia contra el catálogo de rubros."""
    rubro_alcanzado: int      # 0 = la foto no confirma ni el primer rubro
    afo_estimado: int
    determinable: bool        # False si la lectura se cortó por falta de evidencia
    motivo_corte: str

    @property
    def rubro_en_curso(self) -> int | None:
        """El primer rubro que la foto no confirma: la etapa donde está la obra."""
        siguientes = [r for r in ORDEN_RUBROS if r > self.rubro_alcanzado]
        return siguientes[0] if siguientes else None


def coherencia(evidencia: dict) -> tuple[bool, str]:
    """
    ¿La evidencia es físicamente posible? Devuelve (es_coherente, motivo).

    La secuencialidad del AFO no es solo una regla administrativa: es física. No hay
    encadenado sin muros, ni revoque exterior sin mampostería. Si la lectura reporta un
    elemento tardío mientras falta uno anterior, el modelo se equivocó en algún lado y
    no sabemos en cuál — así que el sistema no tiene que elegir a cuál creerle.

    Este chequeo importa más de lo que parece: como la cadena se corta en el primer
    rubro no confirmado, un error sobre `muros` colapsa la estimación entera y produce
    una contradicción enorme y muy convincente. Sin esta verificación, esos errores
    catastróficos encabezan la cola de revisión y desplazan a los sobre-reportes reales.
    Detectarlos y abstenerse es lo que hace utilizable a la cola.
    """
    confirmados: dict[int, bool | None] = {}
    for rid in ORDEN_RUBROS:
        campo, valores_ok = CONFIRMA_RUBRO[rid]
        if campo is None:
            continue
        valor = evidencia.get(campo, NO_DETERMINABLE)
        # None = no se sabe. Un hueco no es una contradicción: eso es abstención.
        confirmados[rid] = None if valor == NO_DETERMINABLE else valor in valores_ok

    positivos = [r for r, v in confirmados.items() if v is True]
    if not positivos:
        return True, ""

    ultimo_confirmado = max(positivos)
    faltantes = [r for r in ORDEN_RUBROS
                 if r < ultimo_confirmado and confirmados.get(r) is False]
    if faltantes:
        nombre_tarde = RUBROS_POR_ID[ultimo_confirmado]["nombre"]
        nombre_falta = RUBROS_POR_ID[faltantes[0]]["nombre"]
        return False, (
            f"Evidencia incoherente: se ve «{nombre_tarde}» (rubro {ultimo_confirmado}) "
            f"pero no «{nombre_falta}» (rubro {faltantes[0]}), que va antes"
        )
    return True, ""


def leer_evidencia(evidencia: dict) -> Lectura:
    """
    Recorre los rubros en orden y se detiene en el primero que la evidencia no confirma.

    Aprovecha la secuencialidad del AFO: como el rubro N exige el N-1 terminado, el
    avance queda determinado por dónde se corta la cadena. No hace falta que el modelo
    acierte los 15 campos — alcanza con que acierte alrededor del corte, que es lo que
    vuelve utilizable a un clasificador apenas decente.

    No alcanza con cortar en el primer rubro que la foto no confirma, y el motivo es
    físico: parte de la evidencia **queda enterrada**. La capa aisladora del rubro 2 se
    tapa al rellenar la excavación, así que en una obra avanzada nunca se la puede ver
    — pero un muro completo prueba que los cimientos existen. La secuencialidad funciona
    en los dos sentidos: confirmar un rubro implica todos los anteriores.

    De ahí la lectura en dos límites:
      · **piso**  = el rubro más alto confirmado (e, por implicación, todos los previos).
      · **techo** = el rubro anterior al primero que la foto descarta.
    Si piso y techo coinciden, la lectura es exacta. Si queda un rango de duda mayor a
    la tolerancia [V5], el sistema se abstiene en vez de elegir un número.
    """
    es_coherente, motivo_incoherencia = coherencia(evidencia)
    if not es_coherente:
        return Lectura(0, 0, False, motivo_incoherencia)

    confirmados, contradichos = [], []
    for rid in ORDEN_RUBROS:
        campo, valores_ok = CONFIRMA_RUBRO[rid]
        # Rubro sin evidencia observable propia ([V2], hoy el 15): nunca se confirma
        # ni se descarta por foto. No es un fallo: es un límite conocido.
        if campo is None:
            continue
        valor = evidencia.get(campo, NO_DETERMINABLE)
        if valor == NO_DETERMINABLE:
            continue                      # hueco: ni confirma ni descarta
        (confirmados if valor in valores_ok else contradichos).append(rid)

    piso = max(confirmados) if confirmados else 0
    techo = (min(contradichos) - 1) if contradichos else ORDEN_RUBROS[-1]
    duda = techo - piso

    if duda > V5_TOLERANCIA_RUBROS:
        faltante = piso + 1
        campo_faltante = CONFIRMA_RUBRO.get(faltante, (None, None))[0]
        motivo = (f"La foto confirma hasta el rubro {piso} y no descarta hasta el {techo}: "
                  f"{duda} rubros de incertidumbre")
        if campo_faltante:
            motivo += f" (falta ver '{campo_faltante}')"
        return Lectura(piso, peso_acumulado(piso), False, motivo)

    # Dentro de la tolerancia se reporta el piso: lo que la foto realmente sostiene.
    # Ser conservador acá es deliberado — inflar el estimado inventaría sub-reportes.
    if duda == 0:
        motivo = f"Confirmado hasta el rubro {piso}, descartado el {piso + 1}"
    else:
        motivo = f"Confirmado hasta el rubro {piso}; el {techo} no pudo verificarse"
    return Lectura(piso, peso_acumulado(piso), True, motivo)


def explicar(lectura: Lectura) -> str:
    """Frase que ve el técnico. Es el producto real del sistema: un motivo, no un número."""
    if lectura.rubro_alcanzado <= 0:
        return f"La foto no confirma ningún rubro terminado. {lectura.motivo_corte}."
    nombre = RUBROS_POR_ID[lectura.rubro_alcanzado]["nombre"]
    frase = (f"La foto confirma hasta «{nombre}» (rubro {lectura.rubro_alcanzado}) "
             f"→ AFO {lectura.afo_estimado}%")
    if lectura.rubro_en_curso:
        en_curso = RUBROS_POR_ID[lectura.rubro_en_curso]["nombre"]
        frase += f", con «{en_curso}» en curso"
    return frase + f". {lectura.motivo_corte}."


def grado_de_respaldo(
    lectura: Lectura,
    afo_declarado: int | None,
    rubro_verificado_previo: int | None = None,
    rechazo_vigente: bool = False,
) -> tuple[str, str]:
    """
    Pondera el reporte de la gestora contra la evidencia. Devuelve (grado, motivo).

    El sistema no aprueba ni rechaza: le pone un grado de respaldo documental a lo que
    declaró la gestora, y el técnico decide. Las dos filas que hacen honesto al sistema
    son SIN_RESPALDO y NO_DETERMINABLE: separan "está sobre-reportando" de "no tengo
    cómo saberlo", que es justo lo que hoy el índice de confiabilidad no puede distinguir.
    """
    if afo_declarado is None:
        return SIN_RESPALDO, "La gestora no reportó avance para este período"

    if not lectura.determinable:
        return NO_DETERMINABLE_G, lectura.motivo_corte

    diferencia = afo_declarado - lectura.afo_estimado
    margen = tolerancia_puntos(lectura.rubro_alcanzado)

    # Monotonía condicional: una obra no retrocede, SALVO que haya un rechazo
    # registrado. Sin esa distinción el sistema marcaría como error de lectura a la
    # gestora que está corrigiendo — ver docs/vision-afo.md §4.1.
    if rubro_verificado_previo is not None and lectura.rubro_alcanzado < rubro_verificado_previo:
        if not rechazo_vigente:
            return RETROCESO_SIN_EXPL, (
                f"La foto muestra menos que la verificación anterior "
                f"(rubro {rubro_verificado_previo} → {lectura.rubro_alcanzado}) "
                f"y no hay rechazo registrado"
            )
        # Con rechazo, el retroceso es esperable. Lo grave es que el reporte no lo
        # descuente: computar como avance un trabajo que fue rechazado.
        if diferencia > margen:
            return AVANCE_RECHAZADO, (
                f"Hay un rechazo registrado sobre esta obra, pero el reporte sigue "
                f"declarando {afo_declarado}% cuando la foto muestra {lectura.afo_estimado}%"
            )

    if diferencia > margen:
        return SOBRE_REPORTE, (
            f"Declarado {afo_declarado}% · foto {lectura.afo_estimado}% "
            f"— {diferencia} puntos por encima (margen {margen})"
        )
    if diferencia < -margen:
        return SUB_REPORTE, (
            f"Declarado {afo_declarado}% · foto {lectura.afo_estimado}% "
            f"— la obra está más avanzada de lo reportado"
        )
    return RESPALDADO, (
        f"Declarado {afo_declarado}% · foto {lectura.afo_estimado}% — dentro del margen "
        f"de {margen} puntos"
    )
