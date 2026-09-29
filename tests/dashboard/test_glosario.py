import streamlit as st
from streamlit.testing.v1 import AppTest


def test_terminos_no_esta_vacio():
    from dashboard.components.glosario import TERMINOS
    assert len(TERMINOS) >= 5
    assert all(explicacion.strip() for explicacion in TERMINOS.values())


def test_mostrar_glosario_no_rompe(tmp_path):
    ruta = tmp_path / "prueba_glosario.py"
    ruta.write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.append(str(Path(__file__).resolve().parent.parent.parent))\n"
        "from dashboard.components.glosario import mostrar_glosario\n"
        "mostrar_glosario()\n",
        encoding="utf-8")
    at = AppTest.from_file(str(ruta)).run()
    assert not at.exception
    assert len(at.sidebar.expander) == 1
