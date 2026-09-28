from datetime import date

import pytest

from datos.indicadores.base import Indicador, _a_fecha, confianza_minima


def test_confianza_minima_es_la_peor_de_las_recibidas():
    # visoc_por_solicitante y visoc_viviendas_segun_solicitante son "inferido" (Plan 1)
    assert confianza_minima(["visoc_por_solicitante"]) == "inferido"
    assert confianza_minima(["visoc_por_solicitante", "visoc_viviendas_segun_solicitante"]) == "inferido"


def test_un_indicador_sin_explicacion_o_sin_como_leerlo_no_se_puede_crear():
    with pytest.raises(ValueError):
        Indicador(codigo="x", pregunta="¿?", explicacion="", como_leerlo="algo",
                  confianza="inferido", capacidad="disponible", valor={})
    with pytest.raises(ValueError):
        Indicador(codigo="x", pregunta="¿?", explicacion="algo", como_leerlo="",
                  confianza="inferido", capacidad="disponible", valor={})


def test_un_indicador_sabe_de_que_reportes_sale():
    indicador = Indicador(codigo="x", pregunta="¿?", explicacion="algo", como_leerlo="algo",
                          confianza="inferido", capacidad="disponible", valor={},
                          reportes=["visoc_por_solicitante"])
    assert indicador.reportes == ["visoc_por_solicitante"]


def test_reportes_queda_vacio_por_defecto():
    indicador = Indicador(codigo="x", pregunta="¿?", explicacion="algo", como_leerlo="algo",
                          confianza="inferido", capacidad="disponible", valor={})
    assert indicador.reportes == []


def test_a_fecha_interpreta_date_iso_y_dd_mm_aaaa():
    assert _a_fecha(date(2024, 3, 1)) == date(2024, 3, 1)
    assert _a_fecha("2024-03-01") == date(2024, 3, 1)
    assert _a_fecha("01-03-2024") == date(2024, 3, 1)
    assert _a_fecha(None) is None
    assert _a_fecha("") is None
    assert _a_fecha("no es una fecha") is None


def test_a_fecha_tolera_los_vacios_de_pandas():
    import pandas as pd
    assert _a_fecha(pd.NaT) is None
    assert _a_fecha(pd.NA) is None
    assert _a_fecha(pd.Timestamp("2024-03-01")) == date(2024, 3, 1)
