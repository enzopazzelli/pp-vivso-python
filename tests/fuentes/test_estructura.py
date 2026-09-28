from datos.fuentes.estructura import (
    COLUMNAS_EXPEDIENTE, COLUMNAS_MEDIDA, COLUMNAS_ORGANIZACION, COLUMNAS_RECLAMO, COLUMNAS_VIVIENDA,
    marco_vacio,
)


def test_las_5_colecciones_tienen_sus_columnas():
    assert "num_exp" in COLUMNAS_VIVIENDA and "titular_seudonimo" in COLUMNAS_VIVIENDA
    assert "cuit" in COLUMNAS_ORGANIZACION and "tipo_solicitante" in COLUMNAS_ORGANIZACION
    assert COLUMNAS_MEDIDA == ["cuit", "nombre_organizacion", "tipo_reporte", "consulta", "metrica",
                               "valor", "periodo_desde", "periodo_hasta", "fecha_reporte"]
    assert COLUMNAS_EXPEDIENTE == ["id", "vivienda_num_exp", "numero", "formato", "tipo", "fecha_reporte"]
    assert COLUMNAS_RECLAMO == ["id", "cuit", "expediente_id", "fecha", "estado"]


def test_marco_vacio_tiene_las_columnas_pedidas_y_ninguna_fila():
    marco = marco_vacio(["a", "b"])
    assert list(marco.columns) == ["a", "b"] and len(marco) == 0


def test_medida_categoria_tiene_sus_columnas():
    from datos.fuentes.estructura import COLUMNAS_MEDIDA_CATEGORIA
    assert COLUMNAS_MEDIDA_CATEGORIA == ["tipo_solicitante", "consulta", "metrica", "valor",
                                        "periodo_desde", "periodo_hasta", "fecha_reporte"]


def test_vivienda_tiene_fecha_activacion():
    assert "fecha_activacion" in COLUMNAS_VIVIENDA
