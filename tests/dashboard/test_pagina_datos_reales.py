from pathlib import Path

RUTA_PAGINA = str(Path(__file__).resolve().parent.parent.parent / "dashboard" / "pages" / "09_datos_reales.py")

# El default de AppTest (3 s) resultó frágil en las Tareas 8 y 9 al importar streamlit/pandas/plotly
# más los 6 módulos de este orquestador en frío — se le da más margen a cada `.run()`.
_TIMEOUT = 20


def test_con_la_fuente_simulada_las_6_pestanias_rendericen_sin_excepcion():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(RUTA_PAGINA).run(timeout=_TIMEOUT)
    at.radio[0].set_value("simulada").run(timeout=_TIMEOUT)
    assert not at.exception
    assert len(at.tabs) == 6


def test_con_json_prueba_las_6_pestanias_rendericen_sin_excepcion():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(RUTA_PAGINA).run(timeout=_TIMEOUT)
    at.radio[0].set_value("json_prueba").run(timeout=_TIMEOUT)
    assert not at.exception


def test_como_en_el_deploy_publico_ninguna_fuente_rompe_la_pagina(monkeypatch, tmp_path):
    # El deploy público (Streamlit Cloud) no instala requirements-datos.txt: no hay pdfplumber ni
    # alembic, ni base propia. La página tiene que abrir igual con cualquier fuente, y la pestaña
    # «Importar» explicar que la importación es solo local en vez de romper.
    import sys
    monkeypatch.setitem(sys.modules, "pdfplumber", None)
    monkeypatch.setitem(sys.modules, "alembic", None)
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'no_existe.db').as_posix()}")
    from streamlit.testing.v1 import AppTest
    for fuente in ("propia", "simulada", "json_prueba"):
        at = AppTest.from_file(RUTA_PAGINA).run(timeout=_TIMEOUT)
        at.radio[0].set_value(fuente).run(timeout=_TIMEOUT)
        assert not at.exception, fuente
        assert len(at.tabs) == 6, fuente
        assert any("copia local" in i.value for i in at.info), fuente


def test_con_propia_sin_migrar_muestra_el_aviso_y_no_rompe(monkeypatch, tmp_path):
    # Encontrado en la revisión final: "propia" es la fuente por defecto, así que sin base migrada
    # (instalación nueva) el usuario no técnico veía SOLO el aviso, sin ninguna pestaña — ni siquiera
    # "Importar", que es justo la que le permitiría arreglarlo. Las 6 pestañas tienen que seguir
    # accesibles; el aviso aparece solo en las que dependen de la fuente.
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'no_existe.db').as_posix()}")
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(RUTA_PAGINA).run(timeout=_TIMEOUT)
    at.radio[0].set_value("propia").run(timeout=_TIMEOUT)
    assert not at.exception
    assert len(at.tabs) == 6
    assert any("no está migrada" in i.value or "no existe" in i.value for i in at.info)


def test_con_propia_migrada_pero_vacia_no_rompe_ninguna_pestania(monkeypatch, tmp_path):
    # Review Focus 5: la base propia recién migrada, sin ninguna importación todavía, es un estado
    # normal (no un error) — distinto del caso de arriba (base ni siquiera migrada). Las 6 pestañas
    # tienen que rendericen igual, con los indicadores en "no_disponible" en vez de romper.
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'vacia_migrada.db').as_posix()}")
    from datos.sesion import migrar
    migrar()

    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(RUTA_PAGINA).run(timeout=_TIMEOUT)
    at.radio[0].set_value("propia").run(timeout=_TIMEOUT)
    assert not at.exception
    assert len(at.tabs) == 6
    assert any("Todavía no se importó" in i.value for i in at.info)
