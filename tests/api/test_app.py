import pytest
from fastapi.testclient import TestClient

from datos.api.app import app


@pytest.fixture
def cliente():
    return TestClient(app)


def test_la_raiz_responde_ok(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


def test_un_query_param_desconocido_no_rompe_la_raiz(cliente):
    # La raíz no depende de `fuente_actual`; esto solo confirma que un query param de más no rompe nada.
    respuesta = cliente.get("/", params={"fuente": "inventada"})
    assert respuesta.status_code == 200
