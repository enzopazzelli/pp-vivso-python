def test_render_muestra_una_ficha_por_reporte(tmp_path):
    from streamlit.testing.v1 import AppTest

    ruta = tmp_path / "prueba_catalogo_reportes.py"
    ruta.write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.append(str(Path(__file__).resolve().parent.parent.parent))\n"
        "from dashboard.paginas_datos_reales import catalogo_reportes\n"
        "from datos.fuentes.simulada import FuenteSimulada\n"
        "catalogo_reportes.render(FuenteSimulada())\n",
        encoding="utf-8")
    # timeout explícito: el default de AppTest (3 s) resultó frágil al importar pandas/plotly/streamlit
    # en frío para este script — encontrado al ejecutar esta tarea (ver ruling en el ledger).
    at = AppTest.from_file(str(ruta)).run(timeout=15)
    assert not at.exception
    from datos.catalogo_reportes import FICHAS
    encabezados = " ".join(m.value for m in at.markdown)
    assert all(ficha["nombre"] in encabezados for ficha in FICHAS.values())
