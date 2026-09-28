import pandas as pd
import pytest

from datos.fuentes.base import FuenteDeDatos
from datos.fuentes.estructura import COLUMNAS_ORGANIZACION, COLUMNAS_VIVIENDA, marco_vacio


class _FuenteDeEjemplo(FuenteDeDatos):
    nombre = "ejemplo"

    def viviendas(self):
        fila = {c: None for c in COLUMNAS_VIVIENDA}
        fila.update(num_exp="v1", departamento="Avellaneda")
        return pd.DataFrame([fila])[COLUMNAS_VIVIENDA]

    def organizaciones(self):
        return marco_vacio(COLUMNAS_ORGANIZACION)

    def medidas(self):
        from datos.fuentes.estructura import COLUMNAS_MEDIDA
        return marco_vacio(COLUMNAS_MEDIDA)

    def expedientes(self):
        from datos.fuentes.estructura import COLUMNAS_EXPEDIENTE
        return marco_vacio(COLUMNAS_EXPEDIENTE)

    def reclamos(self):
        from datos.fuentes.estructura import COLUMNAS_RECLAMO
        return marco_vacio(COLUMNAS_RECLAMO)

    def medidas_categoria(self):
        from datos.fuentes.estructura import COLUMNAS_MEDIDA_CATEGORIA
        return marco_vacio(COLUMNAS_MEDIDA_CATEGORIA)


def test_no_se_puede_instanciar_sin_implementar_los_metodos_abstractos():
    with pytest.raises(TypeError):
        FuenteDeDatos()


def test_catalogo_de_reportes_no_depende_de_la_fuente():
    from datos.catalogo_reportes import FICHAS
    fichas = _FuenteDeEjemplo().catalogo_reportes()
    assert len(fichas) == len(FICHAS)
    assert {f["codigo"] for f in fichas} == set(FICHAS)
    assert all("que_mide" in f and "confianza" in f for f in fichas)


def test_capacidades_declara_viviendas_disponible_con_su_campo_poblado():
    capacidades = _FuenteDeEjemplo().capacidades()
    assert set(capacidades) == {"viviendas", "organizaciones", "medidas", "expedientes", "reclamos",
                                "medidas_categoria"}
    assert capacidades["viviendas"]["disponible"] is True
    assert capacidades["viviendas"]["campos"]["departamento"] is True
    assert capacidades["viviendas"]["campos"]["lat"] is False   # nunca se pobló


def test_capacidades_declara_no_disponible_una_coleccion_vacia():
    capacidades = _FuenteDeEjemplo().capacidades()
    assert capacidades["organizaciones"]["disponible"] is False
    assert capacidades["medidas"] == {"disponible": False}


def test_capacidades_incluye_medidas_categoria():
    assert "medidas_categoria" in _FuenteDeEjemplo().capacidades()
