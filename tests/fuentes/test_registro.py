import pytest

from datos.fuentes.json_prueba import FuenteJSON
from datos.fuentes.propia import FuentePropia
from datos.fuentes.registro import obtener_fuente
from datos.fuentes.simulada import FuenteSimulada


def test_por_defecto_es_la_fuente_propia(monkeypatch):
    monkeypatch.delenv("FUENTE", raising=False)
    assert isinstance(obtener_fuente(), FuentePropia)


def test_lee_la_variable_de_entorno_fuente(monkeypatch):
    monkeypatch.setenv("FUENTE", "simulada")
    assert isinstance(obtener_fuente(), FuenteSimulada)


def test_un_nombre_explicito_ignora_la_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("FUENTE", "simulada")
    assert isinstance(obtener_fuente("json_prueba"), FuenteJSON)


def test_no_distingue_mayusculas_ni_espacios(monkeypatch):
    monkeypatch.setenv("FUENTE", "  SIMULADA  ")
    assert isinstance(obtener_fuente(), FuenteSimulada)


def test_una_fuente_desconocida_da_un_error_claro():
    with pytest.raises(ValueError, match="inventada"):
        obtener_fuente("inventada")


def test_lee_fuente_desde_el_archivo_env_aunque_nadie_lo_haya_cargado_antes(monkeypatch, tmp_path):
    # No alcanza con que algún otro módulo ya haya cargado el .env antes en el proceso: el interruptor
    # tiene que cargarlo él mismo, para no depender del orden en que se importan las cosas.
    monkeypatch.delenv("FUENTE", raising=False)
    (tmp_path / ".env").write_text("FUENTE=simulada\n", encoding="utf-8")
    monkeypatch.setattr("datos.config.RAIZ", tmp_path)
    assert isinstance(obtener_fuente(), FuenteSimulada)
