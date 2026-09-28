from sqlalchemy import inspect

from datos.modelo import Clasificacion, Departamento, TipoReporte
from datos.sesion import sembrar_catalogos
from db.models import Organizacion, Vivienda


def test_se_crean_las_tablas_nuevas_y_siguen_las_existentes(sesion):
    tablas = set(inspect(sesion.get_bind()).get_table_names())
    nuevas = {"departamento", "clasificacion", "tipo_reporte", "importacion", "registro_crudo",
              "organizacion_alias", "medida_organizacion", "vivienda_foto"}
    assert nuevas <= tablas
    assert {"vivienda", "organizacion", "familia", "visita"} <= tablas


def test_vivienda_admite_datos_reales_sin_localidad_ni_fecha_de_inicio(sesion):
    sesion.add(Vivienda(num_exp="123-45-2020", departamento="Avellaneda", estado="Iniciada"))
    sesion.commit()
    vivienda = sesion.get(Vivienda, "123-45-2020")
    assert vivienda.localidad is None and vivienda.fecha_inic is None
    assert vivienda.titular_seudonimo is None and vivienda.fecha_solicitud is None


def test_organizacion_guarda_el_cuit_provisional(sesion):
    sesion.add(Organizacion(cuit="PROV-ABC", nombre="Asoc. X", nombre_normalizado="ASOCIACION X",
                            cuit_provisional=True))
    sesion.commit()
    organizacion = sesion.get(Organizacion, "PROV-ABC")
    assert organizacion.cuit_provisional is True and organizacion.nombre_normalizado == "ASOCIACION X"


def test_sembrar_catalogos_es_idempotente_y_completo(sesion):
    sembrar_catalogos(sesion)
    sembrar_catalogos(sesion)
    assert sesion.query(Departamento).count() == 27
    assert sesion.query(Clasificacion).count() == 15
    assert sesion.query(TipoReporte).count() == 2


def test_las_fichas_de_reportes_estan_completas(sesion):
    for ficha in sesion.query(TipoReporte).all():
        assert ficha.confianza in {"confirmado", "inferido", "sin_confirmar"}
        assert ficha.que_mide and ficha.que_no_mide
        assert isinstance(ficha.limites, list) and ficha.limites
        assert ficha.revisado_en is not None


def test_sembrar_catalogos_incluye_los_catalogos_del_plan_2(sesion):
    from datos.modelo import TipoDocumento, TipoSolicitante, TipoViviendaCatalogo
    from db.models import RubroObra

    sembrar_catalogos(sesion)
    assert sesion.query(TipoSolicitante).count() == 5
    assert sesion.query(TipoViviendaCatalogo).count() == 3
    assert sesion.query(TipoDocumento).count() >= 3
    assert sesion.query(RubroObra).count() == 15   # RUBROS_CATALOGO de db/setup.py


def test_se_crean_las_tablas_del_plan_2(sesion):
    tablas = set(inspect(sesion.get_bind()).get_table_names())
    nuevas = {"localidad", "expediente", "reclamo", "precio_referencia", "documento_expediente",
              "notificacion", "historial_cambios", "log_sincronizacion"}
    assert nuevas <= tablas


def test_organizacion_admite_tipo_solicitante(sesion):
    sesion.add(Organizacion(cuit="PROV-X2", nombre="X", tipo_solicitante="COMISIONADO"))
    sesion.commit()
    assert sesion.get(Organizacion, "PROV-X2").tipo_solicitante == "COMISIONADO"


def test_expediente_guarda_su_formato_clasificado(sesion):
    from datos.modelo import Expediente
    sesion.add(Vivienda(num_exp="v1", departamento="Avellaneda", estado="Iniciada"))
    sesion.add(Expediente(vivienda_num_exp="v1", numero="2128915-2022", formato="NNNNNNN-AAAA", tipo="solicitud"))
    sesion.commit()
    exp = sesion.query(Expediente).one()
    assert exp.tipo == "solicitud" and exp.formato == "NNNNNNN-AAAA"
