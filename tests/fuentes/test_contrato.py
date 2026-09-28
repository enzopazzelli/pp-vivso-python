"""Las tres fuentes cumplen el mismo contrato: mismas columnas, misma forma de capacidades()."""
from datetime import datetime

import pytest

from datos.fuentes.estructura import (
    COLUMNAS_EXPEDIENTE, COLUMNAS_MEDIDA, COLUMNAS_MEDIDA_CATEGORIA, COLUMNAS_ORGANIZACION, COLUMNAS_RECLAMO,
    COLUMNAS_VIVIENDA,
)
from datos.fuentes.json_prueba import FuenteJSON
from datos.fuentes.propia import FuentePropia
from datos.fuentes.simulada import FuenteSimulada
from datos.importadores.visoc_por_solicitante import VisocPorSolicitante
from datos.importadores.visoc_viviendas import VisocViviendasSegunSolicitante
from datos.modelo import Importacion
from tests.fixtures_visoc import LINEAS_PS, LINEAS_V


@pytest.fixture
def fuente_propia_poblada(sesion, anon):
    def _importacion(codigo):
        imp = Importacion(tipo_reporte=codigo, archivo_nombre="x", archivo_huella=codigo.ljust(64, "0"),
                          estado="leida", importado_en=datetime.now())
        sesion.add(imp)
        sesion.flush()
        return imp

    ps = VisocPorSolicitante()
    ps.mapear(ps.lectura_desde_lineas(LINEAS_PS), sesion, _importacion(ps.codigo))
    v = VisocViviendasSegunSolicitante()
    v.mapear(v.lectura_desde_lineas(LINEAS_V, anon), sesion, _importacion(v.codigo))
    sesion.commit()
    return FuentePropia(sesion=sesion)


@pytest.fixture(params=["propia", "simulada", "json_prueba"])
def fuente(request, fuente_propia_poblada):
    return {"propia": fuente_propia_poblada, "simulada": FuenteSimulada(), "json_prueba": FuenteJSON()}[request.param]


def test_las_tres_fuentes_devuelven_las_mismas_columnas_en_el_mismo_orden(fuente):
    assert list(fuente.viviendas().columns) == COLUMNAS_VIVIENDA
    assert list(fuente.organizaciones().columns) == COLUMNAS_ORGANIZACION
    assert list(fuente.medidas().columns) == COLUMNAS_MEDIDA
    assert list(fuente.expedientes().columns) == COLUMNAS_EXPEDIENTE
    assert list(fuente.reclamos().columns) == COLUMNAS_RECLAMO
    assert list(fuente.medidas_categoria().columns) == COLUMNAS_MEDIDA_CATEGORIA


def test_las_tres_fuentes_tienen_capacidades_con_las_6_colecciones(fuente):
    assert set(fuente.capacidades()) == {"viviendas", "organizaciones", "medidas", "expedientes", "reclamos",
                                         "medidas_categoria"}


def test_el_catalogo_de_reportes_es_igual_sin_importar_la_fuente(fuente):
    assert fuente.catalogo_reportes() == FuenteJSON().catalogo_reportes()


def test_cada_fuente_declara_viviendas_y_organizaciones_disponibles(fuente):
    capacidades = fuente.capacidades()
    assert capacidades["viviendas"]["disponible"] is True
    assert capacidades["organizaciones"]["disponible"] is True
