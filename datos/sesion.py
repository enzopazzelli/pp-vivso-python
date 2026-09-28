"""Motor de base de datos, creación de tablas y siembra de los catálogos."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from datos import modelo
from datos.catalogo_reportes import FICHAS
from datos.catalogos import (
    CLASIFICACIONES, DEPARTAMENTOS, SISTEMAS_EXTERNOS, TIPO_DOCUMENTO, TIPO_SOLICITANTE, TIPO_VIVIENDA,
)
from datos.config import db_url
from datos.normalizacion import normalizar_texto
from db.models import Base, RubroObra
from db.setup import RUBROS_CATALOGO


def crear_engine(url: str | None = None):
    """Motor sobre la base real (o la que se pida). En memoria comparte una sola conexión."""
    url = url or db_url()
    if url in ("sqlite://", "sqlite:///:memory:"):
        return create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(url)


def crear_tablas(engine) -> None:
    """Crea las tablas directamente desde los modelos. Solo para pruebas y bases en memoria: en una base
    real el esquema se crea con `migrar`, así queda registrada su versión."""
    Base.metadata.create_all(engine)


def migrar(url: str | None = None) -> None:
    """Crea o actualiza el esquema de la base con las migraciones de Alembic (db/migraciones)."""
    from alembic import command
    from alembic.config import Config

    from datos.config import RAIZ

    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "db" / "migraciones"))
    cfg.set_main_option("sqlalchemy.url", (url or db_url()).replace("%", "%%"))   # «%» se interpola en el .ini
    command.upgrade(cfg, "head")


def sembrar_catalogos(sesion: Session) -> None:
    """Carga (o actualiza) departamentos, clasificaciones y fichas de reportes. Se puede repetir."""
    for nombre in DEPARTAMENTOS:
        clave = normalizar_texto(nombre)
        if sesion.query(modelo.Departamento).filter_by(nombre_normalizado=clave).first() is None:
            sesion.add(modelo.Departamento(nombre=nombre, nombre_normalizado=clave))
    for codigo, (criterio, descripcion) in CLASIFICACIONES.items():
        if sesion.get(modelo.Clasificacion, codigo) is None:
            sesion.add(modelo.Clasificacion(codigo=codigo, criterio=criterio, descripcion=descripcion))
    for codigo, ficha in FICHAS.items():
        existente = sesion.get(modelo.TipoReporte, codigo)
        if existente is None:
            sesion.add(modelo.TipoReporte(codigo=codigo, **ficha))
        else:   # las fichas se editan en catalogo_reportes.py: el código manda
            for campo, valor in ficha.items():
                setattr(existente, campo, valor)
    for fila in TIPO_SOLICITANTE:
        if sesion.get(modelo.TipoSolicitante, fila["codigo"]) is None:
            sesion.add(modelo.TipoSolicitante(**fila))
    for codigo, nombre in TIPO_VIVIENDA.items():
        if sesion.get(modelo.TipoViviendaCatalogo, codigo) is None:
            sesion.add(modelo.TipoViviendaCatalogo(codigo=codigo, nombre=nombre))
    for codigo, nombre in TIPO_DOCUMENTO.items():
        if sesion.get(modelo.TipoDocumento, codigo) is None:
            sesion.add(modelo.TipoDocumento(codigo=codigo, nombre=nombre))
    for fila in SISTEMAS_EXTERNOS:
        if sesion.get(modelo.SistemaExterno, fila["codigo"]) is None:
            sesion.add(modelo.SistemaExterno(**fila))
    for rubro in RUBROS_CATALOGO:
        if sesion.get(RubroObra, rubro["id"]) is None:
            sesion.add(RubroObra(**rubro))
    sesion.commit()
