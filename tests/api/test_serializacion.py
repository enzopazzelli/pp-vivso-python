import pandas as pd

from datos.api.serializacion import df_a_json


def test_convierte_filas_a_lista_de_dict():
    df = pd.DataFrame([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])
    assert df_a_json(df) == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]


def test_un_marco_vacio_da_una_lista_vacia():
    assert df_a_json(pd.DataFrame(columns=["a", "b"])) == []


def test_nan_se_convierte_en_null_no_en_texto_nan():
    df = pd.DataFrame([{"a": 1, "b": None}])
    assert df_a_json(df) == [{"a": 1, "b": None}]


def test_una_fecha_date_queda_en_iso():
    from datetime import date
    df = pd.DataFrame([{"a": date(2022, 6, 7)}])
    assert df_a_json(df)[0]["a"] == "2022-06-07T00:00:00.000"
