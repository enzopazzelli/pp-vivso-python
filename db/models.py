from sqlalchemy import Column, String, Integer, Float, Date, Text, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Vivienda(Base):
    __tablename__ = "vivienda"

    num_exp          = Column(String(50), primary_key=True)
    departamento     = Column(String(100), nullable=False)
    localidad        = Column(String(100), nullable=False)
    barrio           = Column(String(100))
    direccion        = Column(String(200))
    superficie       = Column(Float)
    fecha_inic       = Column(String(10), nullable=False)   # dd-MM-yyyy
    fecha_fin        = Column(String(10))
    estado           = Column(String(20), nullable=False)   # Iniciada/Avanzada/Finalizada/Adjudicada
    lat              = Column(Float)
    lng              = Column(Float)
    avance_obra      = Column(Integer, default=0)
    # Sistema completo de clasificaciones del programa (15 códigos del sistema legacy)
    clasificacion    = Column(String(10))   # 1a/2a/2b/3a/4a/4b/4c/5a/5b/5c/5d/5e/5f/5g/OT
    criterio         = Column(String(15))   # Inclusion / Exclusion / Otro
    tipo_vivienda    = Column(String(20))                   # Urbana/Rural/Económica
    cant_dormitorios = Column(Integer)
    observacion      = Column(Text)
    id_familia       = Column(Integer, ForeignKey("familia.id"))
    representante    = Column(String(200))
    cuit_org         = Column(String(20), ForeignKey("organizacion.cuit"))

    # Columnas calculadas por el pipeline Python
    # El equipo Java puede leerlas si comparten la misma DB
    nivel_riesgo     = Column(String(10))   # alto / medio / bajo / null
    cluster          = Column(Integer)      # grupo asignado por K-Means
    dias_activa      = Column(Integer)      # calculado en ETL


class Familia(Base):
    __tablename__ = "familia"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    representante = Column(String(200))
    cuit_org      = Column(String(20), ForeignKey("organizacion.cuit"))
    integrantes   = relationship("IntegranteFamilia", back_populates="familia")


class IntegranteFamilia(Base):
    __tablename__ = "integrante_familia"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    dni                = Column(String(15), nullable=False)
    nombre             = Column(String(100))
    apellido           = Column(String(100))
    condicion_especial = Column(String(200))
    id_familia         = Column(Integer, ForeignKey("familia.id"))
    familia            = relationship("Familia", back_populates="integrantes")


class Organizacion(Base):
    __tablename__ = "organizacion"

    cuit           = Column(String(20), primary_key=True)
    nombre         = Column(String(300), nullable=False)
    tipo           = Column(String(100))
    dom_legal      = Column(String(300))
    contacto       = Column(String(100))
    cpe            = Column(String(50))
    presidente     = Column(String(200))
    dni_presidente = Column(String(15))
    estado         = Column(String(20), default="ACTIVA")   # ACTIVA/FINALIZADA/SUSPENDIDA


class AvanceObra(Base):
    __tablename__ = "avance_obra"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    vivienda_id = Column(String(50), ForeignKey("vivienda.num_exp"), nullable=False)
    cuit_org    = Column(String(20), ForeignKey("organizacion.cuit"))
    fecha       = Column(String(10))
    etapa       = Column(String(20))   # INICIO/CIMIENTOS/ESTRUCTURA/TECHOS/TERMINACIONES/FINALIZADA
    porcentaje  = Column(Integer)
    descripcion = Column(Text)


class RubroObra(Base):
    """Catálogo fijo de los rubros que componen el AFO (suma de pesos = 100)."""
    __tablename__ = "rubro_obra"

    id          = Column(Integer, primary_key=True)
    nombre      = Column(String(200), nullable=False)
    descripcion = Column(Text)
    peso_pct    = Column(Integer, nullable=False)   # contribución al AFO total
    orden       = Column(Integer, nullable=False)   # secuencia típica de ejecución


class AvanceRubro(Base):
    """AFO desagregado: avance de cada rubro por vivienda."""
    __tablename__ = "avance_rubro"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    vivienda_id         = Column(String(50), ForeignKey("vivienda.num_exp"), nullable=False)
    rubro_id            = Column(Integer,    ForeignKey("rubro_obra.id"),     nullable=False)
    avance_pct          = Column(Integer, default=0)   # 0–100 para este rubro
    fecha_actualizacion = Column(String(10))           # dd-MM-yyyy


class Tecnico(Base):
    __tablename__ = "tecnico"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    nombre           = Column(String(100), nullable=False)
    apellido         = Column(String(100), nullable=False)
    dni              = Column(String(15))
    email            = Column(String(200))
    telefono         = Column(String(30))
    # Departamentos que cubre — lista separada por comas para SQLite
    departamentos    = Column(String(500))
    activo           = Column(Integer, default=1)   # 1=True, 0=False


class AsignacionTecnico(Base):
    """Qué viviendas tiene asignadas cada técnico."""
    __tablename__ = "asignacion_tecnico"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    tecnico_id      = Column(Integer, ForeignKey("tecnico.id"), nullable=False)
    vivienda_id     = Column(String(50), ForeignKey("vivienda.num_exp"), nullable=False)
    fecha_asignacion = Column(String(10))


class Visita(Base):
    """Registro de cada visita técnica a una vivienda."""
    __tablename__ = "visita"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    vivienda_id       = Column(String(50), ForeignKey("vivienda.num_exp"), nullable=False)
    tecnico_id        = Column(Integer, ForeignKey("tecnico.id"), nullable=False)
    fecha             = Column(String(10), nullable=False)
    # Tipo: 'primera' | 'segunda' | 'supervision'
    tipo              = Column(String(20), default="primera")
    avance_verificado = Column(Integer)     # % verificado in situ por el técnico
    estado_relevado   = Column(String(20))  # estado que el técnico observó
    observacion       = Column(Text)
    # Diferencia entre lo que reportó la ONG y lo que verificó el técnico
    # Positivo = ONG reportó más avance del real (sobreestimación)
    diferencia_ong    = Column(Integer)
