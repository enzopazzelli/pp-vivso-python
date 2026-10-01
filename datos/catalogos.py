"""Catálogos fijos: departamentos, clasificaciones de vivienda y códigos de solicitante de VISOC."""
from datos.normalizacion import normalizar_texto

# Los 27 departamentos de Santiago del Estero (la Ficha del proyecto y PP1 hablan de 27;
# el dataset simulado de PP2 usa solo 18).
DEPARTAMENTOS = [
    "Aguirre", "Alberdi", "Atamisqui", "Avellaneda", "Banda", "Belgrano", "Capital", "Choya",
    "Copo", "Figueroa", "General Taboada", "Guasayán", "Jiménez", "Juan F. Ibarra", "Loreto",
    "Mitre", "Moreno", "Ojo de Agua", "Pellegrini", "Quebrachos", "Río Hondo", "Rivadavia",
    "Robles", "Salavina", "San Martín", "Sarmiento", "Silípica",
]

# Las 15 clasificaciones de VISOC (docs/visoc/capturas/tipos.jpeg): código → (criterio, descripción).
# Es la misma tabla que usa synthetic/generate.py.
CLASIFICACIONES = {
    "1a": ("Inclusion", "Vivienda Rancho"),
    "2a": ("Inclusion", "Vivienda Precaria"),
    "2b": ("Inclusion", "Vivienda c/ riesgo de derrumbe"),
    "3a": ("Inclusion", "Vivienda c/ integrantes discapacitados"),
    "4a": ("Otro", "Viviendas Mixtas (rancho y hab. c/ material)"),
    "4b": ("Otro", "Unidad de Material c/ Techo de Chapa/Losa"),
    "4c": ("Otro", "Vivienda de Material con techo de chapa/losa"),
    "5a": ("Exclusion", "Viviendas Abandonadas"),
    "5b": ("Exclusion", "Viviendas precarias sin antigüedad"),
    "5c": ("Exclusion", "Viviendas precarias con conflicto de titularidad"),
    "5d": ("Exclusion", "Asentamientos espontáneos"),
    "5e": ("Exclusion", "Rancho ya posee vivienda del gobierno"),
    "5f": ("Otro", "No posee Vivienda / tiene terreno para la vivienda"),
    "5g": ("Exclusion", "Vivienda Rechazada"),
    "OT": ("Otro", "Otro"),
}

# Códigos de «Solicitante Tipo» que trae el reporte «Viviendas Según Solicitante».
# Solo se conoce COM (Comisión Municipal); el resto se completa cuando aparezcan.
TIPO_SOLICITANTE_VISOC = {"COM": "Comisión Municipal"}

_DEPARTAMENTOS_POR_CLAVE = {normalizar_texto(nombre): nombre for nombre in DEPARTAMENTOS}


def departamento_canonico(nombre: str) -> str | None:
    """El nombre oficial del departamento, o None si no se reconoce."""
    return _DEPARTAMENTOS_POR_CLAVE.get(normalizar_texto(nombre))


# Categorías del PIE del reporte «Por Solicitante» (visoc_por_solicitante.CATEGORIAS + EXTERNA).
# No confundir con TIPO_SOLICITANTE_VISOC (los códigos de «Solicitante Tipo» de «Viviendas Según
# Solicitante», otro reporte, otra clasificación) ni con el OG/ONG del informe (que se deduce del
# texto de GDE, ver informe_ong_og_2026/procesar_informe.py). El grupo de EXTERNA no se conoce.
TIPO_SOLICITANTE = [
    {"codigo": "COOPERATIVA", "nombre": "COOPERATIVA", "grupo": "ONG"},
    {"codigo": "ASOCIACION_ONG", "nombre": "ASOCIACION/ONG", "grupo": "ONG"},
    {"codigo": "COMISIONADO", "nombre": "COMISIONADO", "grupo": "OG"},
    {"codigo": "INTENDENCIA", "nombre": "INTENDENCIA", "grupo": "OG"},
    {"codigo": "EXTERNA", "nombre": "EXTERNA", "grupo": None},
]

# Traducción de los 3 códigos de VISOC a como ya se guardan las viviendas (mismas 3 palabras que
# usa PP2). Antes vivía como diccionario privado dentro de visoc_viviendas.py.
TIPO_VIVIENDA = {"URB": "Urbana", "RUR": "Rural", "ECO": "Económica"}

# Tipos de documento vistos hasta ahora: Acta Digital y Reclamo (de «Viviendas Según Solicitante»)
# y Orden de Pago (circuito de GDE, ver informe_ong_og_2026/DECISIONES.md punto 20). Catálogo
# abierto: se completa cuando aparezcan otros documentos en un export nuevo.
TIPO_DOCUMENTO = {
    "ACTA_DIGITAL": "Acta Digital",
    "RECLAMO": "Reclamo",
    "ORDEN_PAGO": "Orden de Pago",
}

# Las fuentes externas que menciona la especificación (sección 7): arrancan sin conexión.
# Un esqueleto de cada una se construye en un plan posterior.
SISTEMAS_EXTERNOS = [
    {"codigo": "vivso_api", "nombre": "API de VIVSO (Java Spring Boot)", "tipo_conexion": "api", "disponible": False},
    {"codigo": "vivso_mysql", "nombre": "Base MySQL de VIVSO", "tipo_conexion": "mysql", "disponible": False},
    {"codigo": "visoc_db", "nombre": "Base de VISOC (esqueleto)", "tipo_conexion": "desconocido", "disponible": False},
]
