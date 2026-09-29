import pytest
from fastapi.testclient import TestClient

from datos.api.app import app


@pytest.fixture
def cliente():
    return TestClient(app)


def test_sin_anon_secret_da_503(cliente, tmp_path, monkeypatch):
    # Encontrado en la revisión final: la prueba original solo miraba el código de estado. El Review
    # Focus 5 del plan pide además que "no intente escribir nada" — se aísla la base en un archivo que
    # todavía no existe y se confirma que sigue sin existir después del pedido.
    monkeypatch.delenv("ANON_SECRET", raising=False)
    base = tmp_path / "no_deberia_crearse.db"
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{base.as_posix()}")
    respuesta = cliente.post("/importar", files={"archivo": ("x.txt", b"hola", "text/plain")})
    assert respuesta.status_code == 503
    assert not base.exists()


def test_un_archivo_no_reconocido_queda_sin_importador(cliente, tmp_path, monkeypatch):
    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    # `DATOS_DB_URL`, no `datos.config.db_url` parchado directo: ver la nota de la Tarea 5.
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'datos.db').as_posix()}")
    respuesta = cliente.post("/importar", files={"archivo": ("raro.txt", b"hola", "text/plain")})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "sin_importador"


def test_por_solicitante_de_punta_a_punta(cliente, tmp_path, monkeypatch):
    from tests.fixtures_visoc import LINEAS_PS

    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'datos2.db').as_posix()}")
    monkeypatch.setattr("datos.importadores.visoc_por_solicitante.leer_lineas_texto",
                        lambda ruta, max_paginas=None: LINEAS_PS)

    respuesta = cliente.post("/importar", files={"archivo": ("reporte.pdf", b"%PDF-falso", "application/pdf")})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "ok" and cuerpo["tipo_reporte"] == "visoc_por_solicitante"
    assert cuerpo["filas_leidas"] == 3


def test_un_archivo_con_nombre_malicioso_no_rompe_el_pedido(cliente, tmp_path, monkeypatch):
    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'datos4.db').as_posix()}")
    respuesta = cliente.post("/importar", files={"archivo": ("../../evil.txt", b"hola", "text/plain")})
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "sin_importador"


def test_un_archivo_demasiado_grande_da_413(cliente, monkeypatch):
    # Encontrado en la revisión final: sin tope, un archivo enorme se lee entero en memoria antes de
    # hacer nada más. El límite real es generoso (Lugones, un reporte real, pesa 40 KB); acá se achica
    # con monkeypatch para no tener que generar un archivo grande en la prueba.
    import datos.api.importar as modulo
    monkeypatch.setattr(modulo, "TAMANO_MAXIMO_BYTES", 10)
    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    respuesta = cliente.post("/importar", files={"archivo": ("x.txt", b"esto-tiene-mas-de-diez-bytes", "text/plain")})
    assert respuesta.status_code == 413


def test_un_error_de_base_de_datos_no_se_expone_crudo_por_http(cliente, tmp_path, monkeypatch):
    # Encontrado en la revisión final: `importar_archivo` (Plan 1) mete el texto crudo de la excepción
    # de SQLAlchemy (sentencia, parámetros) en una advertencia cuando falla el mapeo — pensado para la
    # consola local. Por HTTP eso expone detalles del esquema a cualquiera que llame al endpoint.
    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'datos5.db').as_posix()}")

    from datos.importar import Resultado
    crudo = ("Falló al guardar en el modelo: (sqlite3.IntegrityError) NOT NULL constraint failed: "
            "organizacion.cuit [SQL: INSERT INTO organizacion (cuit) VALUES (?)] "
            "[parameters: ('30-12345678-9',)]")
    resultado_falso = Resultado("rechazada", 1, "visoc_por_solicitante", 3, [], [crudo])
    monkeypatch.setattr("datos.importar.importar_archivo", lambda *a, **k: resultado_falso)

    respuesta = cliente.post("/importar", files={"archivo": ("reporte.pdf", b"%PDF-falso", "application/pdf")})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "rechazada"
    assert not any("IntegrityError" in a or "[SQL:" in a or "[parameters:" in a for a in cuerpo["advertencias"])
