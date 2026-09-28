import pytest
from fastapi.testclient import TestClient

from datos.api.app import app


@pytest.fixture
def cliente():
    return TestClient(app)


def test_viviendas_con_la_fuente_simulada(cliente):
    respuesta = cliente.get("/viviendas", params={"fuente": "simulada"})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 5000
    assert "num_exp" in cuerpo[0]


def test_viviendas_filtra_por_departamento(cliente):
    respuesta = cliente.get("/viviendas", params={"fuente": "simulada", "departamento": "Capital"})
    cuerpo = respuesta.json()
    assert len(cuerpo) > 0
    assert all(f["departamento"] == "Capital" for f in cuerpo)


def test_un_filtro_sin_coincidencias_da_lista_vacia_no_error(cliente):
    respuesta = cliente.get("/viviendas", params={"fuente": "simulada", "departamento": "No Existe"})
    assert respuesta.status_code == 200 and respuesta.json() == []


def test_organizaciones_medidas_expedientes_reclamos_medidas_categoria(cliente):
    for ruta in ("/organizaciones", "/medidas", "/expedientes", "/reclamos", "/medidas-categoria"):
        respuesta = cliente.get(ruta, params={"fuente": "json_prueba"})
        assert respuesta.status_code == 200, ruta
        assert isinstance(respuesta.json(), list), ruta


def test_una_fuente_invalida_da_400_en_cualquier_coleccion(cliente):
    respuesta = cliente.get("/viviendas", params={"fuente": "inventada"})
    assert respuesta.status_code == 400


def test_propia_sin_base_da_503_no_500(cliente):
    # `app.py` migra la base propia al arrancar (Tarea 1), así que llegar a este estado por HTTP
    # significaría primero deshacer esa migración — en cambio, se inyecta directamente una
    # `FuentePropia` apuntada a una sesión sin ninguna tabla, con el mecanismo propio de FastAPI para
    # reemplazar una dependencia en las pruebas. Así se prueba la conversión a 503 en sí (Tarea 2), no
    # el arranque de la app.
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from datos.api.dependencias import fuente_actual
    from datos.fuentes.propia import FuentePropia

    sesion_sin_tablas = Session(create_engine("sqlite:///:memory:"))
    app.dependency_overrides[fuente_actual] = lambda: FuentePropia(sesion=sesion_sin_tablas)
    try:
        respuesta = cliente.get("/viviendas")
    finally:
        app.dependency_overrides.clear()
    assert respuesta.status_code == 503
