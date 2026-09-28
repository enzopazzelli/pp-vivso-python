"""Fichas de los reportes del sistema antiguo, en lenguaje llano.

Es la fuente de verdad: `sembrar_catalogos` las copia a la tabla `tipo_reporte`. Cuando el área
confirma o desmiente algo, se edita acá (y se actualiza `revisado_en`).
"""
from datetime import date

FICHAS = {
    "visoc_por_solicitante": {
        "sistema_origen": "VISOC",
        "nombre": "VISOC · Por Solicitante",
        "unidad": "organizacion",
        "que_mide": (
            "Para cada organización solicitante y en el período indicado: cuántas solicitudes tiene, "
            "cuántos beneficiarios, cuántas están activadas y cuántas llegaron a fin de obra. Al pie "
            "trae los totales por categoría (cooperativa, asociación/ONG, comisionado e intendencia)."
        ),
        "que_no_mide": (
            "No trae fechas por registro, números de expediente ni datos de cada vivienda. Las tres "
            "consultas (solicitadas, activadas y finalizadas) tienen la misma cabecera: se distinguen "
            "solo por sus datos."
        ),
        "limites": [
            "El TOTAL GRAL del reporte de activadas suma también el reporte de solicitadas.",
            "El reporte de solicitadas trae activadas propias, así que no todas son pendientes.",
            "No se sabe qué fecha filtra cada consulta (solicitud, activación o fin de obra).",
            "«Activadas» es el paso previo al acta de finalización (según el área), por eso está cerca de «finalizadas».",
            "VISOC acumula solicitudes de años anteriores que recién ahora se activan o finalizan, así que no "
            "se puede trazar a los expedientes de un año puntual.",
        ],
        "confianza": "inferido",
        "revisado_en": date(2026, 9, 26),
    },
    "visoc_viviendas_segun_solicitante": {
        "sistema_origen": "VISOC",
        "nombre": "VISOC · Viviendas Según Solicitante",
        "unidad": "vivienda",
        "que_mide": (
            "Una fila por vivienda de un solicitante: fecha de solicitud, expediente, tipo (urbana, "
            "rural o ecológica), dormitorios, clasificación, departamento, reclamo, acta digital, "
            "activación, avance de obra y fin de obra. Al final trae los totales de solicitadas, "
            "finalizadas, desaprobadas y sin finalizar."
        ),
        "que_no_mide": (
            "No trae avance por rubro, visitas técnicas ni coordenadas. En el ejemplo que tenemos el "
            "avance de obra es solo 0 o 100."
        ),
        "limites": [
            "Según el área (audio del 02/09/26), «activar» es el paso previo al Acta de Finalización: cuando el "
            "técnico certifica el 100 % de la obra, el área activa el expediente (pone fecha y calcula los "
            "dormitorios que corresponden) para que el técnico pueda emitir el acta. La orden de pago es un "
            "paso anterior y este reporte no la muestra.",
            "Solo tenemos el ejemplo de un solicitante (Comisión Municipal Lugones, 31/10/2025).",
            "En ese ejemplo, 64 de 107 filas comparten su número de expediente con otra (hay 66 distintos). "
            "Un expediente no debería repetirse: puede ser un dato todavía sin registrar. A confirmar con el área.",
            "La marca DES de las viviendas desaprobadas no está explicada.",
            "El dashboard de PP1 contó 8 viviendas con reclamo; la columna de reclamo del PDF muestra otra cantidad.",
        ],
        "confianza": "inferido",
        "revisado_en": date(2026, 9, 26),
    },
}
