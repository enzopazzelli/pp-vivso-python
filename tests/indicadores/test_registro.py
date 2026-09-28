from datos.fuentes.json_prueba import FuenteJSON
from datos.fuentes.simulada import FuenteSimulada
from datos.indicadores.registro import TODOS, calcular_todos, capacidades_indicadores


def test_todos_tiene_los_6_indicadores():
    assert len(TODOS) == 6


def test_calcular_todos_no_se_cae_con_ninguna_fuente():
    for fuente in (FuenteSimulada(), FuenteJSON()):
        indicadores = calcular_todos(fuente)
        assert len(indicadores) == 6
        for indicador in indicadores:
            assert indicador.explicacion and indicador.como_leerlo
            assert indicador.capacidad in ("disponible", "parcial", "no_disponible")
            assert indicador.reportes   # de qué tipo_reporte sale (sección 8 de la especificación)


def test_capacidades_indicadores_tiene_una_entrada_por_indicador():
    capacidades = capacidades_indicadores(FuenteSimulada())
    assert len(capacidades) == 6
    assert capacidades["viviendas_por_clasificacion_tipo_dormitorios"] == "disponible"
    assert capacidades["peso_tipo_solicitante"] == "no_disponible"   # PP2 no lo modela
