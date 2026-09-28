"""Estructura común que entrega cualquier fuente de datos (sección 7 de la especificación).

Cada fuente traduce lo suyo a estas columnas. Un dato que esa fuente no tiene queda en `None`/`NaN`
en vez de faltar la columna, así el código de arriba (indicadores, interfaz, API) no necesita saber
de qué fuente vienen los datos.
"""
import pandas as pd

COLUMNAS_VIVIENDA = [
    "num_exp", "expediente", "departamento", "localidad", "barrio", "direccion", "superficie",
    "fecha_inic", "fecha_solicitud", "fecha_activacion", "fecha_fin", "estado", "lat", "lng", "avance_obra",
    "clasificacion", "criterio", "tipo_vivienda", "cant_dormitorios", "observacion", "id_familia",
    "representante", "titular_seudonimo", "cuit_org", "nivel_riesgo", "cluster", "dias_activa",
]

COLUMNAS_ORGANIZACION = [
    "cuit", "nombre", "tipo", "tipo_gestora", "tipo_solicitante", "dom_legal", "contacto", "cpe",
    "presidente", "dni_presidente", "estado", "nombre_normalizado", "cuit_provisional",
]

COLUMNAS_MEDIDA = [
    "cuit", "nombre_organizacion", "tipo_reporte", "consulta", "metrica", "valor",
    "periodo_desde", "periodo_hasta", "fecha_reporte",
]

COLUMNAS_EXPEDIENTE = ["id", "vivienda_num_exp", "numero", "formato", "tipo", "fecha_reporte"]

COLUMNAS_RECLAMO = ["id", "cuit", "expediente_id", "fecha", "estado"]

COLUMNAS_MEDIDA_CATEGORIA = ["tipo_solicitante", "consulta", "metrica", "valor",
                             "periodo_desde", "periodo_hasta", "fecha_reporte"]


def marco_vacio(columnas: list[str]) -> pd.DataFrame:
    """Un DataFrame con las columnas pedidas y ninguna fila. Para cuando una fuente no tiene esa colección."""
    return pd.DataFrame(columns=columnas)
