import pytest
from fastapi.testclient import TestClient

from datos.api.app import app


@pytest.fixture
def cliente():
    return TestClient(app)


def test_catalogo_de_reportes_es_igual_sin_importar_la_fuente(cliente):
    from datos.catalogo_reportes import FICHAS
    respuesta = cliente.get("/catalogo-reportes", params={"fuente": "simulada"})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == len(FICHAS)
    assert {f["codigo"] for f in cuerpo} == set(FICHAS)
    assert all(f["confianza"] in ("confirmado", "inferido", "sin_confirmar") for f in cuerpo)


def test_importaciones_da_lista_vacia_sin_una_base_real(cliente, tmp_path, monkeypatch):
    # `DATOS_DB_URL` sí funciona acá (a diferencia de parchear `datos.config.db_url` directamente):
    # `crear_engine`/`migrar` llaman a `db_url()` en cada pedido, y esa función lee la variable de
    # entorno fresca cada vez — no importa desde qué módulo se llame.
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'vacia.db').as_posix()}")
    respuesta = cliente.get("/importaciones")
    assert respuesta.status_code == 200 and respuesta.json() == []


def test_importaciones_lista_lo_que_hay_en_la_base_real(cliente, tmp_path, monkeypatch, sesion):
    from datetime import datetime

    from datos.modelo import Importacion
    sesion.add(Importacion(tipo_reporte="visoc_por_solicitante", archivo_nombre="x.pdf",
                           archivo_huella="0" * 64, estado="ok", filas_leidas=10,
                           importado_en=datetime(2026, 9, 1, 10, 0)))
    sesion.commit()

    def _sesion_de_prueba():
        return sesion

    import datos.api.reportes as modulo
    monkeypatch.setattr(modulo, "_abrir_sesion", _sesion_de_prueba)

    respuesta = cliente.get("/importaciones")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1 and cuerpo[0]["archivo_nombre"] == "x.pdf" and cuerpo[0]["filas_leidas"] == 10
