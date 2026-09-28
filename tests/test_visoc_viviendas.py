import json
from copy import deepcopy
from datetime import date, datetime

from datos.importadores.visoc_viviendas import (
    VisocViviendasSegunSolicitante, parsear_viviendas, reconoce_lineas,
)
from datos.modelo import Importacion, ViviendaFoto
from db.models import Organizacion, Vivienda
from tests.fixtures_visoc import CABECERA_V, LINEAS_V, NOMBRES_INVENTADOS, fila, linea


def _totales(solicitadas, finalizadas, desaprobadas, sin_finalizar):
    return linea("TOTALES", "COMISION", "EJEMPLO:", "Cantidad", "Solicitadas:", str(solicitadas), "Cantidad",
                 "Finalizadas:", str(finalizadas), "Cantidad", "Desaprobadas:", str(desaprobadas), "Cantidad",
                 "Sin", f"Finalizar:{sin_finalizar}")


def _vivienda(sesion, anon, expediente, titular):
    """La vivienda de ese expediente y ese titular (la clave real incluye la huella del titular)."""
    return sesion.query(Vivienda).filter_by(expediente=expediente, titular_seudonimo=anon(titular)).one()


def _importacion(sesion):
    imp = Importacion(tipo_reporte="visoc_viviendas_segun_solicitante", archivo_nombre="x.pdf",
                      archivo_huella="0" * 64, estado="leida", importado_en=datetime.now())
    sesion.add(imp)
    sesion.flush()
    return imp


def _lectura(anon, lineas=None):
    return VisocViviendasSegunSolicitante().lectura_desde_lineas(lineas or LINEAS_V, anon)


def test_parsear_lee_parametros_totales_y_filas(anon):
    parametros, filas, declarados, advertencias = parsear_viviendas(LINEAS_V, anon)
    assert parametros == {"fecha_reporte": "2025-10-31", "solicitante_tipo": "COM",
                          "solicitante_nombre": "COMISION MUNICIPAL EJEMPLO"}
    assert declarados == {"solicitadas": 5, "finalizadas": 2, "desaprobadas": 1, "sin_finalizar": 2}
    assert len(filas) == 5 and advertencias == []


def test_una_vivienda_finalizada_trae_activacion_avance_y_fin(anon):
    _, filas, _, _ = parsear_viviendas(LINEAS_V, anon)
    f = filas[0]
    assert f["expediente"] == "2128915-2022" and f["tipo"] == "URB" and f["dormitorios"] == 2
    assert f["clasificacion"] == "1A" and f["departamento"] == "AVELLANEDA"
    assert f["fecha_solicitud"] == date(2022, 6, 7)
    assert f["fecha_activacion"] == date(2023, 12, 4) and f["fecha_fin_obra"] == date(2023, 12, 6)
    assert f["avance_obra"] == 100.0 and f["desaprobada"] is False
    assert f["exp_acta"] == ["2022-00798757"] and f["exp_reclamo"] == []


def test_las_columnas_reclamo_y_acta_se_distinguen_por_posicion(anon):
    _, filas, _, _ = parsear_viviendas(LINEAS_V, anon)
    con_reclamo = filas[4]
    assert con_reclamo["exp_reclamo"] == ["6503"] and con_reclamo["exp_acta"] == []


def test_estados_sin_finalizar_y_desaprobada(anon):
    _, filas, _, _ = parsear_viviendas(LINEAS_V, anon)
    sin_activar, activada, desaprobada = filas[1], filas[2], filas[3]
    assert sin_activar["fecha_activacion"] is None and sin_activar["avance_obra"] == 0.0
    assert activada["fecha_activacion"] == date(2018, 9, 3) and activada["fecha_fin_obra"] is None
    assert desaprobada["desaprobada"] is True and desaprobada["avance_obra"] == 0.0


def test_los_expedientes_de_todos_los_formatos_se_leen(anon):
    _, filas, _, _ = parsear_viviendas(LINEAS_V, anon)
    assert [f["expediente"] for f in filas] == [
        "2128915-2022", "2128857-2022", "2569802-2022", "447699-2023", "8721-54-2015"]


def test_los_nombres_de_titulares_nunca_salen_de_la_lectura(anon):
    _, filas, _, _ = parsear_viviendas(LINEAS_V, anon)
    volcado = json.dumps(filas, default=str, ensure_ascii=False).upper()
    assert not any(nombre in volcado for nombre in NOMBRES_INVENTADOS)
    assert all(f["titular_seudonimo"] for f in filas)


def test_reconoce_por_el_titulo(anon):
    assert reconoce_lineas(LINEAS_V) == 0.95
    assert reconoce_lineas([[("Por", 1.0), ("Solicitante", 2.0)]]) == 0.0
    assert reconoce_lineas([]) == 0.0


def test_la_validacion_cierra_con_los_totales_del_reporte(anon):
    importador = VisocViviendasSegunSolicitante()
    validacion = importador.validar(_lectura(anon))
    assert validacion.ok, [c for c in validacion.chequeos if not c.ok]


def test_una_vivienda_perdida_hace_fallar_la_validacion(anon):
    lineas = [l for i, l in enumerate(LINEAS_V) if i != 9]    # se pierde la 2ª vivienda
    validacion = VisocViviendasSegunSolicitante().validar(_lectura(anon, lineas))
    assert not validacion.ok
    assert "filas_vs_solicitadas" in [c.nombre for c in validacion.chequeos if not c.ok]


def test_un_reporte_sin_totales_no_se_puede_validar(anon):
    lineas = LINEAS_V[:-1]
    validacion = VisocViviendasSegunSolicitante().validar(_lectura(anon, lineas))
    assert not validacion.ok and validacion.chequeos[0].nombre == "totales_presentes"


def test_una_fila_duplicada_por_error_hace_fallar_los_totales(anon):
    lineas = LINEAS_V[:-1] + [LINEAS_V[9]] + [LINEAS_V[-1]]     # 6 filas, el reporte declara 5
    validacion = VisocViviendasSegunSolicitante().validar(_lectura(anon, lineas))
    assert "filas_vs_solicitadas" in [c.nombre for c in validacion.chequeos if not c.ok]


def _lineas_con_expediente_repetido():
    """Una 6ª vivienda con el MISMO expediente que la primera y otro titular."""
    return LINEAS_V[:-1] + [
        fila("07/06/22", "SOFIA NUEVA MUESTRA", "2128915-2022", "URB", "2", "1A", "AVELLANEDA"),
        _totales(6, 2, 1, 3),
    ]


def test_un_expediente_repetido_no_rechaza_el_reporte_pero_se_advierte(anon):
    importador = VisocViviendasSegunSolicitante()
    lectura = _lectura(anon, _lineas_con_expediente_repetido())
    assert importador.validar(lectura).ok
    assert len(lectura.advertencias) == 1
    assert "2 filas" in lectura.advertencias[0] and "sin registrar" in lectura.advertencias[0]


def test_un_reporte_sin_expedientes_repetidos_no_trae_esa_advertencia(anon):
    assert _lectura(anon).advertencias == []


def test_dos_filas_con_el_mismo_expediente_son_dos_viviendas_distintas(sesion, anon):
    importador = VisocViviendasSegunSolicitante()
    importador.mapear(_lectura(anon, _lineas_con_expediente_repetido()), sesion, _importacion(sesion))
    sesion.commit()
    del_expediente = sesion.query(Vivienda).filter_by(expediente="2128915-2022").all()
    assert len(del_expediente) == 2 and sesion.query(Vivienda).count() == 6
    assert len({v.num_exp for v in del_expediente}) == 2
    assert all(v.num_exp.startswith("2128915-2022#") for v in del_expediente)


def test_dos_filas_totalmente_identicas_se_conservan_con_claves_distintas(sesion, anon):
    lineas = LINEAS_V[:-1] + [LINEAS_V[8], _totales(6, 3, 1, 2)]
    importador = VisocViviendasSegunSolicitante()
    lectura = _lectura(anon, lineas)
    assert importador.validar(lectura).ok
    importador.mapear(lectura, sesion, _importacion(sesion))
    sesion.commit()
    claves = sorted(v.num_exp for v in sesion.query(Vivienda).filter_by(expediente="2128915-2022"))
    assert len(claves) == 2 and claves[1] == claves[0] + ".2"


def test_mapear_crea_viviendas_fotos_y_organizacion(sesion, anon):
    importador = VisocViviendasSegunSolicitante()
    importador.mapear(_lectura(anon), sesion, _importacion(sesion))
    sesion.commit()

    assert sesion.query(Vivienda).count() == 5 and sesion.query(ViviendaFoto).count() == 5
    v = _vivienda(sesion, anon, "2128915-2022", "JUANA EJEMPLO PEREZ")
    assert v.num_exp.startswith("2128915-2022#")
    assert v.estado == "Finalizada" and v.tipo_vivienda == "Urbana" and v.clasificacion == "1a"
    assert v.criterio == "Inclusion" and v.departamento == "Avellaneda" and v.avance_obra == 100
    assert v.fecha_fin == "06-12-2023" and v.fecha_solicitud == date(2022, 6, 7)
    assert _vivienda(sesion, anon, "447699-2023", "LUIS DEMO").estado == "Desaprobada"
    assert _vivienda(sesion, anon, "2128857-2022", "PEDRO MUESTRA").estado == "Iniciada"
    assert _vivienda(sesion, anon, "2569802-2022", "ANA PRUEBA").estado == "Avanzada"
    assert _vivienda(sesion, anon, "447699-2023", "LUIS DEMO").tipo_vivienda == "Económica"

    organizacion = sesion.query(Organizacion).one()
    assert organizacion.nombre == "COMISION MUNICIPAL EJEMPLO" and organizacion.tipo_gestora == "Comisión Municipal"
    assert v.cuit_org == organizacion.cuit

    con_reclamo = _vivienda(sesion, anon, "8721-54-2015", "MARTA FICTICIA")
    foto = sesion.query(ViviendaFoto).filter_by(vivienda_num_exp=con_reclamo.num_exp).one()
    assert foto.exp_reclamo == "6503" and foto.exp_acta is None
    assert sesion.query(ViviendaFoto).filter_by(vivienda_num_exp=v.num_exp).one().exp_acta == "2022-00798757"


def test_en_la_base_no_hay_nombres_reales_y_el_seudonimo_es_estable(sesion, anon):
    importador = VisocViviendasSegunSolicitante()
    importador.mapear(_lectura(anon), sesion, _importacion(sesion))
    sesion.commit()
    seudonimos = [v.titular_seudonimo for v in sesion.query(Vivienda).all()]
    assert not any(n in s.upper() for s in seudonimos for n in NOMBRES_INVENTADOS)
    assert _vivienda(sesion, anon, "2128915-2022", "JUANA EJEMPLO PEREZ").titular_seudonimo == anon("JUANA EJEMPLO PEREZ")


def test_un_reporte_mas_viejo_suma_historial_pero_no_pisa_el_estado_actual(sesion, anon):
    importador = VisocViviendasSegunSolicitante()
    nuevo = _lectura(anon)                                   # 31/10/2025: la 1ª vivienda está finalizada
    viejo = deepcopy(nuevo)
    viejo.fecha_reporte = date(2025, 9, 30)
    primera = viejo.filas[0]
    primera.update(avance_obra=0.0, fecha_fin_obra=None, fecha_activacion=None)   # antes no estaba terminada

    importador.mapear(nuevo, sesion, _importacion(sesion))
    importador.mapear(viejo, sesion, _importacion(sesion))
    sesion.commit()

    v = _vivienda(sesion, anon, "2128915-2022", "JUANA EJEMPLO PEREZ")   # .one(): la misma vivienda en ambos reportes
    assert v.estado == "Finalizada" and v.avance_obra == 100          # sigue mandando el más nuevo
    fotos = sesion.query(ViviendaFoto).filter_by(vivienda_num_exp=v.num_exp).all()
    assert len(fotos) == 2                                            # pero queda el historial


def test_real_lugones_cierra_con_su_resumen(real, anon):
    from datos.importadores.pdf import leer_lineas_tokens
    importador = VisocViviendasSegunSolicitante()
    lectura = importador.lectura_desde_lineas(leer_lineas_tokens(real("lugones")), anon)
    assert len(lectura.filas) == 107
    assert lectura.totales_declarados == {"solicitadas": 107, "finalizadas": 78, "desaprobadas": 2, "sin_finalizar": 27}
    assert lectura.parametros["solicitante_nombre"] == "COMISION MUNICIPAL LUGONES"
    assert importador.validar(lectura).ok
    # 66 expedientes distintos para 107 filas: el área debe confirmar si es un dato sin registrar
    assert any("64 filas" in aviso for aviso in lectura.advertencias)


# --- Correcciones tras la revisión final ------------------------------------------------------------

def test_un_reporte_mas_viejo_no_pisa_los_dormitorios_ni_la_clasificacion(sesion, anon):
    importador = VisocViviendasSegunSolicitante()
    nuevo = _lectura(anon)                                   # 31/10/2025: 2 dormitorios, clasificación 1A
    viejo = deepcopy(nuevo)
    viejo.fecha_reporte = date(2025, 1, 31)
    viejo.filas[0].update(dormitorios=0, clasificacion="2a", departamento="BANDA")   # antes de activar se cargaba distinto

    importador.mapear(nuevo, sesion, _importacion(sesion))
    importador.mapear(viejo, sesion, _importacion(sesion))
    sesion.commit()

    v = _vivienda(sesion, anon, "2128915-2022", "JUANA EJEMPLO PEREZ")
    assert (v.cant_dormitorios, v.clasificacion, v.departamento) == (2, "1a", "Avellaneda")


def test_una_obra_a_medio_avance_no_rechaza_el_reporte(sesion, anon):
    # el pie de VISOC cuenta como «sin finalizar» a toda obra que no llegó a 100
    lineas = list(LINEAS_V)
    lineas[10] = fila("08/07/22", "ANA PRUEBA", "2569802-2022", "URB", "0", "2a", "AVELLANEDA",
                      activacion="03/09/18", afo="50,00")
    importador = VisocViviendasSegunSolicitante()
    lectura = _lectura(anon, lineas)
    assert importador.validar(lectura).ok
    importador.mapear(lectura, sesion, _importacion(sesion))
    sesion.commit()
    v = _vivienda(sesion, anon, "2569802-2022", "ANA PRUEBA")
    assert v.estado == "Avanzada" and v.avance_obra == 50


def test_la_clasificacion_OT_conserva_su_criterio(sesion, anon):
    lineas = LINEAS_V[:-1] + [
        fila("01/02/23", "OSCAR OTRA MUESTRA", "555555-2023", "URB", "0", "OT", "AVELLANEDA"),
        _totales(6, 2, 1, 3),
    ]
    VisocViviendasSegunSolicitante().mapear(_lectura(anon, lineas), sesion, _importacion(sesion))
    sesion.commit()
    v = _vivienda(sesion, anon, "555555-2023", "OSCAR OTRA MUESTRA")
    assert v.clasificacion == "OT" and v.criterio == "Otro"


def test_una_desaprobada_sin_activacion_no_ensucia_el_departamento(anon):
    lineas = LINEAS_V[:-1] + [
        fila("01/02/23", "OSCAR OTRA MUESTRA", "555555-2023", "URB", "0", "5g", "AVELLANEDA", desaprobada=True),
        _totales(6, 2, 2, 2),
    ]
    lectura = _lectura(anon, lineas)
    nueva = lectura.filas[-1]
    assert nueva["desaprobada"] is True and nueva["departamento"] == "AVELLANEDA"
    assert VisocViviendasSegunSolicitante().validar(lectura).ok


def test_una_cabecera_repetida_en_otra_pagina_no_cambia_el_nombre_del_solicitante(anon):
    lineas = LINEAS_V[:-1] + [linea("Pagina", "2", "de", "3"), CABECERA_V, _totales(5, 2, 1, 2)]
    parametros, filas, _, _ = parsear_viviendas(lineas, anon)
    assert parametros["solicitante_nombre"] == "COMISION MUNICIPAL EJEMPLO" and len(filas) == 5


# --- Plan 2: registro de expedientes -----------------------------------------------------------------

def test_mapear_registra_el_expediente_de_solicitud_reclamo_y_acta(sesion, anon):
    from datos.modelo import Expediente
    importador = VisocViviendasSegunSolicitante()
    importador.mapear(_lectura(anon), sesion, _importacion(sesion))
    sesion.commit()

    con_acta = _vivienda(sesion, anon, "2128915-2022", "JUANA EJEMPLO PEREZ")
    solicitud = sesion.query(Expediente).filter_by(vivienda_num_exp=con_acta.num_exp, tipo="solicitud").one()
    assert solicitud.numero == "2128915-2022" and solicitud.formato == "NNNNNNN-AAAA"
    acta = sesion.query(Expediente).filter_by(vivienda_num_exp=con_acta.num_exp, tipo="acta").one()
    assert acta.numero == "2022-00798757"   # el formato de acta no se conoce: queda "desconocido"
    assert acta.formato == "desconocido"

    con_reclamo = _vivienda(sesion, anon, "8721-54-2015", "MARTA FICTICIA")
    reclamo = sesion.query(Expediente).filter_by(vivienda_num_exp=con_reclamo.num_exp, tipo="reclamo").one()
    assert reclamo.numero == "6503"


def test_importar_el_mismo_reporte_dos_veces_no_duplica_expedientes(sesion, anon):
    from datos.modelo import Expediente
    importador = VisocViviendasSegunSolicitante()
    lectura = _lectura(anon)
    importador.mapear(lectura, sesion, _importacion(sesion))
    importador.mapear(lectura, sesion, _importacion(sesion))
    sesion.commit()
    assert sesion.query(Expediente).count() == 7   # 5 de solicitud + 1 acta + 1 reclamo (no se duplican)


def test_real_lugones_registra_expedientes_de_solicitud_reclamo_y_acta(real, anon):
    from sqlalchemy import func
    from sqlalchemy.orm import Session

    from datos.importadores.pdf import leer_lineas_tokens
    from datos.modelo import Expediente
    from datos.sesion import crear_engine, crear_tablas, sembrar_catalogos

    engine = crear_engine("sqlite:///:memory:")
    crear_tablas(engine)
    with Session(engine) as s:
        sembrar_catalogos(s)
        importador = VisocViviendasSegunSolicitante()
        lectura = importador.lectura_desde_lineas(leer_lineas_tokens(real("lugones")), anon)
        importador.mapear(lectura, s, _importacion(s))
        s.commit()
        por_tipo = {t: n for t, n in s.query(Expediente.tipo, func.count()).group_by(Expediente.tipo)}
        assert por_tipo["solicitud"] == 107 and por_tipo.get("reclamo", 0) == 2 and por_tipo.get("acta", 0) == 27
