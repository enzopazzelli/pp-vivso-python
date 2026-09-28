from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

RAIZ = Path(__file__).resolve().parent.parent


def _configuracion(url: str) -> Config:
    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "db" / "migraciones"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def test_la_migracion_inicial_crea_y_borra_el_esquema(tmp_path):
    url = f"sqlite:///{(tmp_path / 'prueba.db').as_posix()}"
    cfg = _configuracion(url)

    command.upgrade(cfg, "head")
    tablas = set(inspect(create_engine(url)).get_table_names())
    assert {"alembic_version", "vivienda", "organizacion", "importacion", "vivienda_foto"} <= tablas

    command.downgrade(cfg, "base")
    assert "importacion" not in set(inspect(create_engine(url)).get_table_names())


def test_la_migracion_inicial_declara_las_tablas_sin_depender_de_los_modelos():
    # Con `create_all` la línea de base cambia cada vez que cambian los modelos y la migración siguiente falla
    fuente = (RAIZ / "db" / "migraciones" / "versions" / "0001_esquema_inicial.py").read_text(encoding="utf-8")
    assert "create_all" not in fuente and "op.create_table" in fuente


def test_la_migracion_0002_agrega_las_tablas_del_plan_2(tmp_path):
    url = f"sqlite:///{(tmp_path / 'prueba2.db').as_posix()}"
    cfg = _configuracion(url)
    command.upgrade(cfg, "head")
    tablas = set(inspect(create_engine(url)).get_table_names())
    assert {"expediente", "reclamo", "precio_referencia", "localidad", "sistema_externo"} <= tablas


def test_la_migracion_0003_agrega_medida_categoria(tmp_path):
    url = f"sqlite:///{(tmp_path / 'prueba3.db').as_posix()}"
    cfg = _configuracion(url)
    command.upgrade(cfg, "head")
    assert "medida_categoria" in set(inspect(create_engine(url)).get_table_names())


def test_las_migraciones_y_los_modelos_estan_alineados(tmp_path):
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    import datos.modelo  # noqa: F401
    from db.models import Base

    url = f"sqlite:///{(tmp_path / 'alineada.db').as_posix()}"
    command.upgrade(_configuracion(url), "head")
    with create_engine(url).connect() as conexion:
        diferencias = compare_metadata(MigrationContext.configure(conexion), Base.metadata)
    assert diferencias == [], diferencias
