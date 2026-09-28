from datos.catalogos import (
    CLASIFICACIONES, DEPARTAMENTOS, TIPO_DOCUMENTO, TIPO_SOLICITANTE, TIPO_SOLICITANTE_VISOC, TIPO_VIVIENDA,
    departamento_canonico,
)
from datos.normalizacion import (
    clasificar_formato_expediente, normalizar_expediente, normalizar_organizacion, normalizar_texto,
    tipo_gestora_por_nombre,
)


def test_hay_27_departamentos_y_15_clasificaciones():
    assert len(DEPARTAMENTOS) == 27 and len(set(DEPARTAMENTOS)) == 27
    assert len(CLASIFICACIONES) == 15
    assert {criterio for criterio, _ in CLASIFICACIONES.values()} == {"Inclusion", "Exclusion", "Otro"}


def test_el_codigo_com_de_visoc_es_comision_municipal():
    assert TIPO_SOLICITANTE_VISOC["COM"] == "Comisión Municipal"


def test_departamento_canonico_ignora_mayusculas_y_tildes():
    assert departamento_canonico("AVELLANEDA") == "Avellaneda"
    assert departamento_canonico("guasayan") == "Guasayán"
    assert departamento_canonico("Lugar inexistente") is None
    assert departamento_canonico("") is None


def test_normalizar_texto_saca_tildes_puntuacion_y_espacios():
    assert normalizar_texto("Coop.de Trabajo «Los Pinos» (M.N.72458)") == "COOP DE TRABAJO LOS PINOS M N 72458"


def test_variantes_de_una_misma_organizacion_se_unifican():
    a = normalizar_organizacion("ASOC. CIV. DE FOM. VEC. FUERZAS UNIDAS")
    b = normalizar_organizacion("Asociación Civil de Fomento Vecinal Fuerzas Unidas")
    assert a == b


def test_tipo_gestora_por_nombre():
    assert tipo_gestora_por_nombre("COMISION MUNICIPAL POZO BETBEDER") == "Comisión Municipal"
    assert tipo_gestora_por_nombre("COM. MUN. DE LA CAPITAL") == "Comisión Municipal"
    assert tipo_gestora_por_nombre("MUNICIPALIDAD DE VILLA OJO DE AGUA") == "Municipio"
    # «COMUN.DE» contiene «MUN.DE» como subcadena, pero no es un municipio
    assert tipo_gestora_por_nombre("ASOC.CIV.SOC.COMUN.DE ACCION Y TRABAJOS") == "ONG"
    assert tipo_gestora_por_nombre("ASOC. CIVIL ESPERANZA") == "ONG"


def test_normalizar_expediente():
    assert normalizar_expediente("  2128915-2022 ") == "2128915-2022"
    assert normalizar_expediente("ex-2026-123") == "EX-2026-123"


def test_tipo_solicitante_tiene_las_5_categorias_del_pie_de_por_solicitante():
    codigos = {t["codigo"] for t in TIPO_SOLICITANTE}
    assert codigos == {"COOPERATIVA", "ASOCIACION_ONG", "COMISIONADO", "INTENDENCIA", "EXTERNA"}
    grupos = {t["codigo"]: t["grupo"] for t in TIPO_SOLICITANTE}
    assert grupos["COOPERATIVA"] == "ONG" and grupos["ASOCIACION_ONG"] == "ONG"
    assert grupos["COMISIONADO"] == "OG" and grupos["INTENDENCIA"] == "OG"
    assert grupos["EXTERNA"] is None   # no se sabe a qué grupo pertenece; no se inventa


def test_tipo_vivienda_traduce_los_3_codigos_de_visoc():
    assert TIPO_VIVIENDA == {"URB": "Urbana", "RUR": "Rural", "ECO": "Económica"}


def test_tipo_documento_incluye_lo_que_ya_vimos_en_los_reportes():
    assert set(TIPO_DOCUMENTO) >= {"ACTA_DIGITAL", "RECLAMO", "ORDEN_PAGO"}


def test_clasificar_formato_expediente_reconoce_los_formatos_conocidos():
    # Los dos primeros son expedientes reales de Lugones (ver tests/fixtures_visoc.py)
    assert clasificar_formato_expediente("8721-54-2015") == "NNNNN-NN-NNNN"
    assert clasificar_formato_expediente("2128915-2022") == "NNNNNNN-AAAA"
    assert clasificar_formato_expediente("EX-2026-000123") == "EX-AAAA-…"
    assert clasificar_formato_expediente("6503") == "desconocido"   # un número de reclamo, no de expediente
