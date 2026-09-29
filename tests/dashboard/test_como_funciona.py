def test_render_no_rompe_y_muestra_el_glosario(tmp_path):
    from streamlit.testing.v1 import AppTest

    ruta = tmp_path / "prueba_como_funciona.py"
    ruta.write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.append(str(Path(__file__).resolve().parent.parent.parent))\n"
        "from dashboard.paginas_datos_reales import como_funciona\n"
        "como_funciona.render()\n",
        encoding="utf-8")
    at = AppTest.from_file(str(ruta)).run()
    assert not at.exception
    assert len(at.sidebar.expander) == 1   # el glosario


def test_el_ejemplo_no_usa_datos_reales():
    from dashboard.paginas_datos_reales.como_funciona import _EJEMPLO_NOMBRE
    # El nombre de ejemplo tiene que ser inventado, no uno de los archivos reales del área.
    assert _EJEMPLO_NOMBRE not in ("", None)
    assert "lugones" not in _EJEMPLO_NOMBRE.lower()
