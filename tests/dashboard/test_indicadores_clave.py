def test_render_con_json_prueba_no_rompe(tmp_path):
    # json_prueba es la fuente más chica: si algún indicador queda "no_disponible", tiene que
    # decirlo, no romper.
    from streamlit.testing.v1 import AppTest

    ruta = tmp_path / "prueba_indicadores_json.py"
    ruta.write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.append(str(Path(__file__).resolve().parent.parent.parent))\n"
        "from dashboard.paginas_datos_reales import indicadores_clave\n"
        "from datos.fuentes.json_prueba import FuenteJSON\n"
        "indicadores_clave.render(FuenteJSON())\n",
        encoding="utf-8")
    at = AppTest.from_file(str(ruta)).run()
    assert not at.exception


def test_render_con_simulada_no_rompe(tmp_path):
    from streamlit.testing.v1 import AppTest

    ruta = tmp_path / "prueba_indicadores_simulada.py"
    ruta.write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.append(str(Path(__file__).resolve().parent.parent.parent))\n"
        "from dashboard.paginas_datos_reales import indicadores_clave\n"
        "from datos.fuentes.simulada import FuenteSimulada\n"
        "indicadores_clave.render(FuenteSimulada())\n",
        encoding="utf-8")
    at = AppTest.from_file(str(ruta)).run()
    assert not at.exception


def test_no_disponible_explica_que_reporte_lo_habilitaria(monkeypatch, tmp_path):
    # Encontrado en la revisión final: la sección 10.2 de la especificación original pide que, si un
    # indicador no está disponible, la pantalla explique qué export lo habilitaría — antes solo decía
    # "No disponible con esta fuente." sin decir qué hacer. Con la base propia recién migrada (sin
    # ninguna importación todavía) los 6 indicadores quedan "no_disponible".
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'vacia_migrada.db').as_posix()}")
    from datos.sesion import migrar
    migrar()

    from streamlit.testing.v1 import AppTest
    ruta = tmp_path / "prueba_indicadores_no_disponible.py"
    ruta.write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.append(str(Path(__file__).resolve().parent.parent.parent))\n"
        "from dashboard.paginas_datos_reales import indicadores_clave\n"
        "from datos.fuentes.propia import FuentePropia\n"
        "indicadores_clave.render(FuentePropia())\n",
        encoding="utf-8")
    at = AppTest.from_file(str(ruta)).run(timeout=15)
    assert not at.exception
    assert any("Se habilita importando" in c.value for c in at.caption)
