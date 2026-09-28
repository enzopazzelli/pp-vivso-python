"""Entorno de Alembic: toma los modelos de db.models y la dirección de la base del entorno."""
from alembic import context
from sqlalchemy import create_engine, pool

import datos.modelo  # noqa: F401  (registra las tablas nuevas en Base.metadata)
from datos.config import db_url
from db.models import Base

config = context.config
target_metadata = Base.metadata


def _url() -> str:
    return config.get_main_option("sqlalchemy.url") or db_url()


def correr_sin_conexion() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def correr_con_conexion() -> None:
    engine = create_engine(_url(), poolclass=pool.NullPool)
    with engine.connect() as conexion:
        context.configure(connection=conexion, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    correr_sin_conexion()
else:
    correr_con_conexion()
