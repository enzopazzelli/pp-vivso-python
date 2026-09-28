import pytest
from fastapi.testclient import TestClient

from datos.api.app import app


@pytest.fixture
def cliente():
    return TestClient(app)


def test_lista_los_6_indicadores(cliente):
    respuesta = cliente.get("/indicadores", params={"fuente": "simulada"})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 6
    assert {"codigo", "pregunta", "explicacion", "como_leerlo", "confianza", "capacidad", "valor",
           "reportes"} <= set(cuerpo[0])


def test_un_indicador_por_codigo(cliente):
    respuesta = cliente.get("/indicadores/viviendas_por_clasificacion_tipo_dormitorios",
                            params={"fuente": "simulada"})
    assert respuesta.status_code == 200
    assert respuesta.json()["codigo"] == "viviendas_por_clasificacion_tipo_dormitorios"


def test_un_codigo_que_no_existe_da_404(cliente):
    respuesta = cliente.get("/indicadores/no-existe", params={"fuente": "simulada"})
    assert respuesta.status_code == 404


def test_capacidades_trae_colecciones_e_indicadores(cliente):
    respuesta = cliente.get("/capacidades", params={"fuente": "simulada"})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert "colecciones" in cuerpo and "indicadores" in cuerpo
    assert "viviendas" in cuerpo["colecciones"]
    assert "peso_tipo_solicitante" in cuerpo["indicadores"]


@pytest.mark.parametrize("ruta", ["/indicadores", "/indicadores/viviendas_por_clasificacion_tipo_dormitorios",
                                  "/capacidades"])
def test_propia_sin_base_da_503_no_500(cliente, ruta):
    # Mismo mecanismo que la Tarea 2: `calcular_todos`/`capacidades_indicadores`/`fuente.capacidades()`
    # llaman a `fuente.viviendas()` etc., que con una `FuentePropia` sin tablas tira `RuntimeError`
    # (Plan 3). Sin un manejo explícito acá, eso se cuela como 500 con traceback crudo.
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from datos.api.dependencias import fuente_actual
    from datos.fuentes.propia import FuentePropia

    sesion_sin_tablas = Session(create_engine("sqlite:///:memory:"))
    app.dependency_overrides[fuente_actual] = lambda: FuentePropia(sesion=sesion_sin_tablas)
    try:
        respuesta = cliente.get(ruta)
    finally:
        app.dependency_overrides.clear()
    assert respuesta.status_code == 503
