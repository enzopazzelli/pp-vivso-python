from dashboard.paginas_datos_reales.mapa_de_datos import _conteos, _diagrama


def test_conteos_da_un_numero_por_coleccion():
    from datos.fuentes.json_prueba import FuenteJSON
    conteos = _conteos(FuenteJSON())
    assert set(conteos) == {"viviendas", "organizaciones", "medidas", "expedientes", "reclamos",
                            "medidas_categoria"}
    assert all(isinstance(n, int) for n in conteos.values())


def test_diagrama_con_todo_en_cero_no_rompe():
    diagrama = _diagrama({"viviendas": 0, "organizaciones": 0, "medidas": 0, "expedientes": 0,
                          "reclamos": 0, "medidas_categoria": 0})
    assert "digraph" in diagrama and "viviendas" in diagrama


def test_render_con_la_fuente_simulada_no_rompe(tmp_path):
    from streamlit.testing.v1 import AppTest

    ruta = tmp_path / "prueba_mapa_de_datos.py"
    ruta.write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.append(str(Path(__file__).resolve().parent.parent.parent))\n"
        "from dashboard.paginas_datos_reales import mapa_de_datos\n"
        "from datos.fuentes.simulada import FuenteSimulada\n"
        "mapa_de_datos.render(FuenteSimulada())\n",
        encoding="utf-8")
    at = AppTest.from_file(str(ruta)).run()
    assert not at.exception
