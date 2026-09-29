def test_sin_ninguna_importacion_avisa_en_la_linea_de_tiempo(monkeypatch, tmp_path):
    # Con `simulada` los indicadores sí tienen datos (el mapa de calor no queda vacío); lo que está
    # vacío es la línea de tiempo, que siempre lee de la base propia — se apunta `DATOS_DB_URL` a un
    # archivo que no existe para simular "todavía no se importó nada".
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'vacia.db').as_posix()}")
    from streamlit.testing.v1 import AppTest

    ruta = tmp_path / "prueba_cobertura_confianza.py"
    ruta.write_text(
        "import sys\nfrom pathlib import Path\n"
        "sys.path.append(str(Path(__file__).resolve().parent.parent.parent))\n"
        "from dashboard.paginas_datos_reales import cobertura_confianza\n"
        "from datos.fuentes.simulada import FuenteSimulada\n"
        "cobertura_confianza.render(FuenteSimulada())\n",
        encoding="utf-8")
    at = AppTest.from_file(str(ruta)).run()
    assert not at.exception
    assert any("Todavía no se importó" in i.value for i in at.info)


def test_linea_de_tiempo_da_vacio_sin_base_real(monkeypatch, tmp_path):
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'otra_vacia.db').as_posix()}")
    from dashboard.paginas_datos_reales.cobertura_confianza import _linea_de_tiempo
    assert _linea_de_tiempo().empty


def test_la_figura_del_mapa_de_calor_fija_la_escala_de_0_a_3():
    # Encontrado en la revisión final: sin zmin/zmax explícito, Plotly estira los colores al rango
    # de valores presentes. Hoy las dos fichas de datos/catalogo_reportes.py son "inferido" (peso 2 de
    # 3) — sin este fijado, el mapa de calor pintaba "inferido" con el color de "confirmado" (el tope
    # de una escala 0-2 en vez de 0-3), mostrando más certeza de la que hay.
    from dashboard.paginas_datos_reales.cobertura_confianza import _figura_calor, _mapa_de_calor
    from datos.fuentes.simulada import FuenteSimulada
    fig = _figura_calor(_mapa_de_calor(FuenteSimulada()))
    assert fig.layout.coloraxis.cmin == 0 and fig.layout.coloraxis.cmax == 3
