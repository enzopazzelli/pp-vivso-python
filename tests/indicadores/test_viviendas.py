from datetime import date, datetime

from datos.fuentes.propia import FuentePropia
from datos.fuentes.simulada import FuenteSimulada
from datos.importadores.visoc_viviendas import VisocViviendasSegunSolicitante
from datos.indicadores.viviendas import (
    antiguedad_sin_terminar, por_clasificacion_tipo_dormitorios, terminadas_y_sin_terminar,
)
from datos.modelo import Importacion
from tests.fixtures_visoc import LINEAS_V


def _importacion(sesion):
    imp = Importacion(tipo_reporte="visoc_viviendas_segun_solicitante", archivo_nombre="x",
                      archivo_huella="0" * 64, estado="leida", importado_en=datetime.now())
    sesion.add(imp)
    sesion.flush()
    return imp


def test_sin_datos_queda_no_disponible(sesion):
    indicador = por_clasificacion_tipo_dormitorios(FuentePropia(sesion=sesion))
    assert indicador.capacidad == "no_disponible"
    assert indicador.explicacion and indicador.como_leerlo


def test_con_las_5_viviendas_de_ejemplo_cuenta_bien(sesion, anon):
    VisocViviendasSegunSolicitante().mapear(
        VisocViviendasSegunSolicitante().lectura_desde_lineas(LINEAS_V, anon), sesion, _importacion(sesion))
    sesion.commit()

    indicador = por_clasificacion_tipo_dormitorios(FuentePropia(sesion=sesion))
    assert indicador.capacidad == "disponible" and indicador.confianza == "inferido"
    assert indicador.valor["por_tipo"] == {"Urbana": 3, "Rural": 1, "Económica": 1}
    assert indicador.valor["por_clasificacion"] == {"1a": 3, "2a": 1, "5f": 1}
    assert indicador.valor["por_dormitorios"] == {0: 3, 2: 2}


def test_real_lugones_cuenta_54_urbana_51_rural_2_economica(real, anon):
    from datos.importadores.pdf import leer_lineas_tokens
    from datos.sesion import crear_engine, crear_tablas, sembrar_catalogos
    from sqlalchemy.orm import Session

    engine = crear_engine("sqlite:///:memory:")
    crear_tablas(engine)
    with Session(engine) as s:
        sembrar_catalogos(s)
        importador = VisocViviendasSegunSolicitante()
        lectura = importador.lectura_desde_lineas(leer_lineas_tokens(real("lugones")), anon)
        importador.mapear(lectura, s, _importacion(s))
        s.commit()
        indicador = por_clasificacion_tipo_dormitorios(FuentePropia(sesion=s))
        assert indicador.valor["por_tipo"] == {"Urbana": 54, "Rural": 51, "Económica": 2}


def test_con_datos_simulados_tambien_funciona():
    indicador = por_clasificacion_tipo_dormitorios(FuenteSimulada())
    assert indicador.capacidad == "disponible"
    assert sum(indicador.valor["por_tipo"].values()) == 5000


def test_terminadas_y_sin_terminar_excluye_las_desaprobadas(sesion, anon):
    VisocViviendasSegunSolicitante().mapear(
        VisocViviendasSegunSolicitante().lectura_desde_lineas(LINEAS_V, anon), sesion, _importacion(sesion))
    sesion.commit()

    indicador = terminadas_y_sin_terminar(FuentePropia(sesion=sesion))
    assert indicador.valor["terminadas"] == 2 and indicador.valor["sin_terminar"] == 2
    assert indicador.valor["desaprobadas"] == 1
    assert indicador.valor["terminadas"] + indicador.valor["sin_terminar"] + indicador.valor["desaprobadas"] == 5


def test_real_lugones_da_27_sin_terminar_como_declara_el_propio_reporte(real, anon):
    from datos.importadores.pdf import leer_lineas_tokens
    from datos.sesion import crear_engine, crear_tablas, sembrar_catalogos
    from sqlalchemy.orm import Session

    engine = crear_engine("sqlite:///:memory:")
    crear_tablas(engine)
    with Session(engine) as s:
        sembrar_catalogos(s)
        importador = VisocViviendasSegunSolicitante()
        lectura = importador.lectura_desde_lineas(leer_lineas_tokens(real("lugones")), anon)
        importador.mapear(lectura, s, _importacion(s))
        s.commit()
        indicador = terminadas_y_sin_terminar(FuentePropia(sesion=s))
        assert indicador.valor["sin_terminar"] == 27 and indicador.valor["terminadas"] == 78
        assert indicador.valor["desaprobadas"] == 2
        assert indicador.valor["finalizadas_por_anio"][2016] == 26


def test_real_antiguedad_en_lugones_coincide_con_lo_verificado(real, anon):
    from datos.importadores.pdf import leer_lineas_tokens
    from datos.sesion import crear_engine, crear_tablas, sembrar_catalogos
    from sqlalchemy.orm import Session

    engine = crear_engine("sqlite:///:memory:")
    crear_tablas(engine)
    with Session(engine) as s:
        sembrar_catalogos(s)
        importador = VisocViviendasSegunSolicitante()
        lectura = importador.lectura_desde_lineas(leer_lineas_tokens(real("lugones")), anon)
        importador.mapear(lectura, s, _importacion(s))
        s.commit()
        indicador = antiguedad_sin_terminar(FuentePropia(sesion=s), hoy=date(2026, 9, 28))
        assert indicador.valor["cantidad"] == 27
        assert indicador.valor["dias_minimo"] == 1347
        assert indicador.valor["dias_mediana"] == 2610
        assert indicador.valor["dias_maximo"] == 3177


def test_antiguedad_sin_datos_queda_no_disponible(sesion):
    indicador = antiguedad_sin_terminar(FuentePropia(sesion=sesion))
    assert indicador.capacidad == "no_disponible"


def test_terminadas_y_sin_terminar_cuenta_adjudicada_como_terminada():
    # PP2 usa un cuarto estado, "Adjudicada", que synthetic/generate.py y el tablero (dashboard/app.py)
    # tratan como obra terminada (avance 100). Si el indicador no lo suma, desaparecen del total.
    indicador = terminadas_y_sin_terminar(FuenteSimulada())
    total = (indicador.valor["terminadas"] + indicador.valor["sin_terminar"] + indicador.valor["desaprobadas"])
    assert total == 5000
