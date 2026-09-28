import pytest

from datos.modelo import OrganizacionAlias
from datos.organizaciones import cuit_provisional, obtener_o_crear_organizacion
from db.models import Organizacion


def test_una_organizacion_nueva_recibe_cuit_provisional_y_tipo(sesion):
    org = obtener_o_crear_organizacion(sesion, "MUNICIPALIDAD DE VILLA EJEMPLO", origen="visoc_por_solicitante")
    sesion.commit()
    assert org.cuit.startswith("PROV-") and org.cuit_provisional is True
    assert org.tipo_gestora == "Municipio" and org.estado == "ACTIVA"
    assert org.cuit == cuit_provisional("MUNICIPALIDAD DE VILLA EJEMPLO")


def test_el_tipo_de_gestora_se_puede_indicar(sesion):
    org = obtener_o_crear_organizacion(sesion, "LUGONES", origen="x", tipo_gestora="Comisión Municipal")
    assert org.tipo_gestora == "Comisión Municipal"


def test_variantes_del_mismo_nombre_dan_una_sola_organizacion(sesion):
    a = obtener_o_crear_organizacion(sesion, "ASOC. CIV. DE FOM. VEC. FUERZAS UNIDAS", origen="a")
    b = obtener_o_crear_organizacion(sesion, "Asociación Civil de Fomento Vecinal Fuerzas Unidas", origen="b")
    sesion.commit()
    assert a.cuit == b.cuit
    assert sesion.query(Organizacion).count() == 1


def test_un_nombre_parecido_pero_distinto_crea_otra_y_queda_pendiente_de_revision(sesion):
    obtener_o_crear_organizacion(sesion, "ASOCIACION CIVIL ESPERANZA VIVA", origen="a")
    obtener_o_crear_organizacion(sesion, "ASOCIACION CIVIL ESPERANZA VIVAS", origen="a")
    obtener_o_crear_organizacion(sesion, "COOPERATIVA DE TRABAJO LOS PINOS", origen="a")
    sesion.commit()
    assert sesion.query(Organizacion).count() == 3
    pendientes = sesion.query(OrganizacionAlias).filter_by(pendiente_revision=True).all()
    assert [p.alias for p in pendientes] == ["ASOCIACION CIVIL ESPERANZA VIVAS"]


def test_un_nombre_vacio_se_rechaza(sesion):
    with pytest.raises(ValueError):
        obtener_o_crear_organizacion(sesion, "  ...  ", origen="x")
