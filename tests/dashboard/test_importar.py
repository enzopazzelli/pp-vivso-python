from streamlit.testing.v1 import AppTest


def _script(tmp_path) -> str:
    ruta = tmp_path / "prueba_importar.py"
    ruta.write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.append(str(Path(__file__).resolve().parent.parent.parent))\n"
        "from dashboard.paginas_datos_reales import importar\n"
        "importar.render()\n",
        encoding="utf-8")
    return str(ruta)


# `render()` corre `migrar()` (una migración real de Alembic) cada vez que aparece un archivo nuevo,
# además de en la carga inicial de la página — encontrado al correr esta tarea: el timeout por
# defecto de AppTest (3 s) no le alcanza cuando varias pruebas de este archivo corren seguidas en el
# mismo proceso. Se le da más margen a cada `.run()`.
_TIMEOUT = 15


def test_sin_archivo_subido_no_rompe(monkeypatch, tmp_path):
    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'datos.db').as_posix()}")
    at = AppTest.from_file(_script(tmp_path)).run(timeout=_TIMEOUT)
    assert not at.exception


def test_subir_un_reporte_reconocido_muestra_la_vista_previa_sin_guardar_nada(monkeypatch, tmp_path):
    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'datos.db').as_posix()}")
    from tests.fixtures_visoc import LINEAS_PS
    monkeypatch.setattr("datos.importadores.visoc_por_solicitante.leer_lineas_texto",
                        lambda ruta, max_paginas=None: LINEAS_PS)

    at = AppTest.from_file(_script(tmp_path)).run(timeout=_TIMEOUT)
    at.file_uploader[0].upload("reporte.pdf", b"%PDF-falso", "application/pdf").run(timeout=_TIMEOUT)

    assert not at.exception
    assert any("visoc_por_solicitante" in s.value for s in at.success)
    assert any("Confirmar e importar" in b.label for b in at.button)

    from sqlalchemy import create_engine, inspect
    url = f"sqlite:///{(tmp_path / 'datos.db').as_posix()}"
    tablas = inspect(create_engine(url)).get_table_names()
    if "importacion" in tablas:
        from sqlalchemy.orm import Session
        from datos.modelo import Importacion
        with Session(create_engine(url)) as sesion:
            assert sesion.query(Importacion).count() == 0


def test_confirmar_guarda_y_subir_de_nuevo_lo_marca_duplicado(monkeypatch, tmp_path):
    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'datos2.db').as_posix()}")
    from tests.fixtures_visoc import LINEAS_PS
    monkeypatch.setattr("datos.importadores.visoc_por_solicitante.leer_lineas_texto",
                        lambda ruta, max_paginas=None: LINEAS_PS)

    at = AppTest.from_file(_script(tmp_path)).run(timeout=_TIMEOUT)
    at.file_uploader[0].upload("reporte.pdf", b"%PDF-falso", "application/pdf").run(timeout=_TIMEOUT)
    boton_confirmar = next(b for b in at.button if b.label == "Confirmar e importar")
    boton_confirmar.click().run(timeout=_TIMEOUT)
    assert not at.exception
    assert any("se guardó" in s.value for s in at.success)

    at2 = AppTest.from_file(_script(tmp_path)).run(timeout=_TIMEOUT)
    at2.file_uploader[0].upload("reporte.pdf", b"%PDF-falso", "application/pdf").run(timeout=_TIMEOUT)
    assert any("ya se importó" in i.value for i in at2.info)
    boton_confirmar_2 = next(b for b in at2.button if b.label == "Confirmar e importar")
    assert boton_confirmar_2.disabled


def test_un_nombre_de_archivo_con_traversal_se_sanea(monkeypatch, tmp_path):
    # El widget st.file_uploader(..., type=["pdf"]) rechaza cualquier nombre que no termine en
    # ".pdf" antes de que el script llegue a correr (encontrado al ejecutar la Tarea 8:
    # StreamlitAPIException con "../../evil.txt"). El nombre malicioso tiene que terminar en ".pdf"
    # para pasar ese filtro del widget — el contenido sigue sin ser un PDF válido, así que ningún
    # importador lo reconoce igual.
    #
    # Encontrado en la revisión final: la prueba original solo comprobaba que no rompiera, no que el
    # nombre realmente se saneara — un archivo temporal real solo existe durante `previsualizar()`
    # ahora (ver Importante 5), así que la prueba correcta es comprobar el nombre que queda en
    # `session_state`, no el sistema de archivos.
    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'datos3.db').as_posix()}")
    at = AppTest.from_file(_script(tmp_path)).run(timeout=_TIMEOUT)
    at.file_uploader[0].upload("../../evil.pdf", b"hola", "application/pdf").run(timeout=_TIMEOUT)
    assert not at.exception
    # "evil.pdf" no es un PDF real (pdfminer no lo abre): la vista previa debe avisarlo, no romper.
    assert any("No se reconoce" in w.value for w in at.warning)
    nombre_guardado = at.session_state["_importar_nombre_seguro"]
    assert nombre_guardado == "evil.pdf"
    assert "/" not in nombre_guardado and "\\" not in nombre_guardado and ".." not in nombre_guardado


def test_confirmar_siembra_catalogos_antes_de_mapear(monkeypatch, tmp_path):
    # Encontrado en la revisión final: la Tarea 6 del Plan 4 ya había corregido este mismo bug en
    # `POST /importar` (sin sembrar_catalogos, un Organizacion/Vivienda con FK a un catálogo — ej.
    # Clasificacion — queda con esos campos en None), pero el tablero no lo heredó porque se escribió
    # aparte. Se prueba con el importador de viviendas, que sí completa `criterio` desde el catálogo.
    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'datos4.db').as_posix()}")
    from tests.fixtures_visoc import LINEAS_V
    monkeypatch.setattr("datos.importadores.visoc_viviendas.leer_lineas_tokens",
                        lambda ruta, max_paginas=None: LINEAS_V)

    at = AppTest.from_file(_script(tmp_path)).run(timeout=_TIMEOUT)
    at.file_uploader[0].upload("viviendas.pdf", b"%PDF-falso", "application/pdf").run(timeout=_TIMEOUT)
    boton_confirmar = next(b for b in at.button if b.label == "Confirmar e importar")
    boton_confirmar.click().run(timeout=_TIMEOUT)
    assert not at.exception
    assert any("se guardó" in s.value for s in at.success)

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from db.models import Vivienda
    url = f"sqlite:///{(tmp_path / 'datos4.db').as_posix()}"
    with Session(create_engine(url)) as sesion:
        viviendas = sesion.query(Vivienda).all()
        assert viviendas and all(v.criterio is not None for v in viviendas)


def test_un_reporte_que_no_valida_se_puede_registrar_como_rechazado(monkeypatch, tmp_path):
    # Encontrado en la revisión final: antes, el botón "Confirmar e importar" quedaba habilitado con
    # una validación fallida (chequeos en rojo) sin ninguna advertencia — spec §6.4 permite registrar
    # el rechazo, pero el usuario no técnico tiene que saber qué va a pasar antes de tocar el botón.
    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'datos5.db').as_posix()}")
    from tests.fixtures_visoc import LINEAS_PS
    sin_una_fila = [l for l in LINEAS_PS if "COOP.DE TRABAJO" not in l]
    monkeypatch.setattr("datos.importadores.visoc_por_solicitante.leer_lineas_texto",
                        lambda ruta, max_paginas=None: sin_una_fila)

    at = AppTest.from_file(_script(tmp_path)).run(timeout=_TIMEOUT)
    at.file_uploader[0].upload("reporte.pdf", b"%PDF-falso", "application/pdf").run(timeout=_TIMEOUT)
    assert not at.exception
    assert any("no coincide con sus propios totales" in w.value for w in at.warning)
    boton = next(b for b in at.button if b.label == "Registrar como rechazado")
    assert not boton.disabled

    boton.click().run(timeout=_TIMEOUT)
    assert not at.exception
    assert any("quedó rechazado" in e.value for e in at.error)
