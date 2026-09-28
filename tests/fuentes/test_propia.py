from datetime import datetime

import pytest

from datos.fuentes.estructura import COLUMNAS_EXPEDIENTE, COLUMNAS_MEDIDA, COLUMNAS_ORGANIZACION, COLUMNAS_VIVIENDA
from datos.fuentes.propia import FuentePropia
from datos.importadores.visoc_por_solicitante import VisocPorSolicitante
from datos.importadores.visoc_viviendas import VisocViviendasSegunSolicitante
from datos.modelo import Importacion
from tests.fixtures_visoc import LINEAS_PS, LINEAS_V


def _importacion(sesion, codigo):
    imp = Importacion(tipo_reporte=codigo, archivo_nombre="x", archivo_huella=codigo.ljust(64, "0"),
                      estado="leida", importado_en=datetime.now())
    sesion.add(imp)
    sesion.flush()
    return imp


def test_no_toca_la_base_hasta_que_se_le_pide_un_dato(sesion, anon, monkeypatch):
    # Si el constructor abriera una conexión real, esto fallaría al no existir esa carpeta.
    monkeypatch.setenv("DATOS_DB_URL", "sqlite:////ruta/que/no/existe/x.db")
    FuentePropia()   # no debe lanzar


def test_viviendas_y_organizaciones_traen_lo_que_importaron_los_importadores(sesion, anon):
    ps = VisocPorSolicitante()
    ps.mapear(ps.lectura_desde_lineas(LINEAS_PS), sesion, _importacion(sesion, ps.codigo))
    v = VisocViviendasSegunSolicitante()
    v.mapear(v.lectura_desde_lineas(LINEAS_V, anon), sesion, _importacion(sesion, v.codigo))
    sesion.commit()

    fuente = FuentePropia(sesion=sesion)
    viviendas = fuente.viviendas()
    assert list(viviendas.columns) == COLUMNAS_VIVIENDA and len(viviendas) == 5
    assert viviendas["localidad"].isna().all()   # VISOC no la trae

    organizaciones = fuente.organizaciones()
    assert list(organizaciones.columns) == COLUMNAS_ORGANIZACION
    assert len(organizaciones) == 4   # 3 de Por Solicitante + 1 de Viviendas (no se repiten)


def test_medidas_trae_lo_que_importo_por_solicitante(sesion, anon):
    ps = VisocPorSolicitante()
    ps.mapear(ps.lectura_desde_lineas(LINEAS_PS), sesion, _importacion(sesion, ps.codigo))
    sesion.commit()

    medidas = FuentePropia(sesion=sesion).medidas()
    assert list(medidas.columns) == COLUMNAS_MEDIDA and len(medidas) == 12
    assert medidas["tipo_reporte"].eq("visoc_por_solicitante").all()
    assert medidas["nombre_organizacion"].notna().all()


def test_expedientes_trae_lo_que_registro_viviendas_segun_solicitante(sesion, anon):
    v = VisocViviendasSegunSolicitante()
    v.mapear(v.lectura_desde_lineas(LINEAS_V, anon), sesion, _importacion(sesion, v.codigo))
    sesion.commit()

    expedientes = FuentePropia(sesion=sesion).expedientes()
    assert list(expedientes.columns) == COLUMNAS_EXPEDIENTE
    assert (expedientes["tipo"] == "solicitud").sum() == 5
    assert (expedientes["tipo"] == "acta").sum() == 1


def test_sin_datos_devuelve_marcos_vacios_con_las_columnas_correctas(sesion):
    fuente = FuentePropia(sesion=sesion)
    assert fuente.viviendas().empty and list(fuente.viviendas().columns) == COLUMNAS_VIVIENDA
    assert fuente.medidas().empty and fuente.reclamos().empty


def test_una_base_sin_ninguna_tabla_da_un_error_claro():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    with Session(create_engine("sqlite:///:memory:")) as sesion_vacia:   # sin crear_tablas ni migrar
        with pytest.raises(RuntimeError, match="no está migrada|no existe"):
            FuentePropia(sesion=sesion_vacia).viviendas()


def test_una_base_migrada_solo_hasta_el_plan_1_da_un_error_claro_al_pedir_algo_del_plan_2(tmp_path):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from datos.config import RAIZ

    url = f"sqlite:///{(tmp_path / 'solo_0001.db').as_posix()}"
    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "db" / "migraciones"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "0001")   # se queda antes de la migración que agrega tipo_solicitante

    with Session(create_engine(url)) as sesion_plan1:
        with pytest.raises(RuntimeError, match="no está migrada|no existe"):
            FuentePropia(sesion=sesion_plan1).organizaciones()


def test_medidas_categoria_trae_el_pie_de_por_solicitante(sesion, anon):
    ps = VisocPorSolicitante()
    ps.mapear(ps.lectura_desde_lineas(LINEAS_PS), sesion, _importacion(sesion, ps.codigo))
    sesion.commit()

    from datos.fuentes.estructura import COLUMNAS_MEDIDA_CATEGORIA
    medidas_categoria = FuentePropia(sesion=sesion).medidas_categoria()
    assert list(medidas_categoria.columns) == COLUMNAS_MEDIDA_CATEGORIA
    assert len(medidas_categoria) == 20   # 5 categorías x 4 métricas
    coop = medidas_categoria[(medidas_categoria["tipo_solicitante"] == "COOPERATIVA")
                             & (medidas_categoria["metrica"] == "solicitudes")]
    assert coop["valor"].iloc[0] == 2


def test_fecha_activacion_es_la_de_la_foto_mas_reciente(sesion, anon):
    v = VisocViviendasSegunSolicitante()
    v.mapear(v.lectura_desde_lineas(LINEAS_V, anon), sesion, _importacion(sesion, v.codigo))
    sesion.commit()

    viviendas = FuentePropia(sesion=sesion).viviendas()
    con_activacion = viviendas[viviendas["fecha_activacion"].notna()]
    # De las 5 filas de LINEAS_V, solo PEDRO MUESTRA (2128857-2022, «Iniciada») no trae activación
    assert len(con_activacion) == 4
