from datos.fuentes.estructura import COLUMNAS_EXPEDIENTE, COLUMNAS_ORGANIZACION, COLUMNAS_VIVIENDA
from datos.fuentes.json_prueba import FuenteJSON


def test_lee_el_json_de_prueba_del_repositorio():
    fuente = FuenteJSON()
    assert list(fuente.viviendas().columns) == COLUMNAS_VIVIENDA
    assert len(fuente.viviendas()) == 2
    assert list(fuente.organizaciones().columns) == COLUMNAS_ORGANIZACION
    assert len(fuente.reclamos()) == 1


def test_un_archivo_propio_se_puede_indicar(tmp_path):
    ruta = tmp_path / "mini.json"
    ruta.write_text('{"viviendas": [], "organizaciones": [], "medidas": [], "expedientes": [], "reclamos": []}',
                    encoding="utf-8")
    fuente = FuenteJSON(ruta)
    assert fuente.viviendas().empty and list(fuente.viviendas().columns) == COLUMNAS_VIVIENDA


def test_un_archivo_inexistente_da_todo_vacio(tmp_path):
    fuente = FuenteJSON(tmp_path / "no_existe.json")
    assert fuente.viviendas().empty and fuente.organizaciones().empty


def test_un_registro_al_que_le_faltan_columnas_se_completa_con_none(tmp_path):
    # Un archivo «mínimo» de verdad no tiene por qué traer las 26 columnas de vivienda.
    ruta = tmp_path / "minimo.json"
    ruta.write_text('{"viviendas": [{"num_exp": "1", "departamento": "Capital", "estado": "Iniciada"}]}',
                    encoding="utf-8")
    viviendas = FuenteJSON(ruta).viviendas()
    assert list(viviendas.columns) == COLUMNAS_VIVIENDA
    assert viviendas["num_exp"].iloc[0] == "1"
    assert viviendas["lat"].isna().all()


def test_la_ruta_se_puede_pasar_como_texto(tmp_path):
    ruta = tmp_path / "mini.json"
    ruta.write_text('{"viviendas": [], "organizaciones": [], "medidas": [], "expedientes": [], "reclamos": []}',
                    encoding="utf-8")
    assert FuenteJSON(str(ruta)).viviendas().empty
