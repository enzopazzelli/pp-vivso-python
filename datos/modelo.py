"""Tablas nuevas de la capa de datos: catálogos y trazabilidad de las importaciones.

Se registran sobre el mismo `Base` de db/models.py, así conviven con las tablas del prototipo.
"""
from sqlalchemy import (
    JSON, Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint,
)

from db.models import Base


class Departamento(Base):
    __tablename__ = "departamento"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    nombre             = Column(String(100), nullable=False, unique=True)
    nombre_normalizado = Column(String(100), nullable=False, unique=True)


class Clasificacion(Base):
    """Las 15 clasificaciones de VISOC y su criterio (Inclusion, Exclusion u Otro)."""
    __tablename__ = "clasificacion"

    codigo      = Column(String(5), primary_key=True)
    criterio    = Column(String(15), nullable=False)
    descripcion = Column(String(200), nullable=False)


class TipoSolicitante(Base):
    """Las categorías del pie de «Por Solicitante», con su grupo OG/ONG cuando se conoce."""
    __tablename__ = "tipo_solicitante"

    codigo = Column(String(30), primary_key=True)
    nombre = Column(String(60), nullable=False)
    grupo  = Column(String(10))   # OG / ONG / None


class TipoViviendaCatalogo(Base):
    """Traduce los 3 códigos de VISOC (URB/RUR/ECO). No reemplaza la columna `vivienda.tipo_vivienda`,
    que ya guarda la palabra completa; es la referencia para no repetir la traducción en cada lugar."""
    __tablename__ = "tipo_vivienda"

    codigo = Column(String(5), primary_key=True)
    nombre = Column(String(20), nullable=False)


class TipoDocumento(Base):
    __tablename__ = "tipo_documento"

    codigo = Column(String(30), primary_key=True)
    nombre = Column(String(60), nullable=False)


class SistemaExterno(Base):
    """Las fuentes externas de la sección 7 de la especificación (API y MySQL de VIVSO, base de
    VISOC). Arrancan sin conexión; un plan posterior construye el esqueleto de cada una."""
    __tablename__ = "sistema_externo"

    codigo        = Column(String(30), primary_key=True)
    nombre        = Column(String(100), nullable=False)
    tipo_conexion = Column(String(20))
    disponible    = Column(Boolean, default=False)


class Localidad(Base):
    """Catálogo vacío por ahora: no tenemos todavía un export con localidades reales para sembrarlo
    (a diferencia de `departamento`, que sí es una lista oficial de 27). Se llena cuando llegue uno."""
    __tablename__ = "localidad"
    __table_args__ = (UniqueConstraint("nombre", "departamento_id"),)

    id              = Column(Integer, primary_key=True, autoincrement=True)
    nombre          = Column(String(100), nullable=False)
    departamento_id = Column(Integer, ForeignKey("departamento.id"))


class Expediente(Base):
    """Cada número de expediente asociado a una vivienda: el de la solicitud, y los de reclamo o
    acta digital que traiga «Viviendas Según Solicitante». Un expediente puede repetirse entre
    reportes; no se duplica (ver `datos/importadores/visoc_viviendas.py::_registrar_expedientes`)."""
    __tablename__ = "expediente"
    __table_args__ = (UniqueConstraint("vivienda_num_exp", "numero", "tipo"),)

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    vivienda_num_exp      = Column(String(50), ForeignKey("vivienda.num_exp"), nullable=False, index=True)
    numero                = Column(String(50), nullable=False)
    formato               = Column(String(20))   # NNNNN-NN-NNNN / NNNNNNN-AAAA / EX-AAAA-… / desconocido
    tipo                  = Column(String(20), nullable=False)   # solicitud / reclamo / acta
    origen_importacion_id = Column(Integer, ForeignKey("importacion.id"))


class Reclamo(Base):
    """Vacía hasta que se importe `gde_reclamos` (Plan 4): hoy no tenemos ese export."""
    __tablename__ = "reclamo"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    cuit                  = Column(String(20), ForeignKey("organizacion.cuit"))
    expediente_id         = Column(Integer, ForeignKey("expediente.id"))
    fecha                 = Column(Date)
    estado                = Column(String(30))
    origen_importacion_id = Column(Integer, ForeignKey("importacion.id"))


class PrecioReferencia(Base):
    """Vacía hasta que se importe `precios_vigentes` (Plan 4). La forma sigue la de
    informe_ong_og_2026/procesar_informe.py: por vigencia, tipo de vivienda, dormitorios, grupo
    (OG/ONG) y rubro (total, materiales, mano de obra, herramientas)."""
    __tablename__ = "precio_referencia"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    vigente_desde         = Column(Date, nullable=False)
    tipo_vivienda         = Column(String(20), nullable=False)
    dormitorios           = Column(Integer)
    grupo                 = Column(String(10))   # OG / ONG
    rubro                 = Column(String(30))   # total / materiales / mano_obra / herramientas
    monto                 = Column(Integer, nullable=False)
    origen_importacion_id = Column(Integer, ForeignKey("importacion.id"))


class DocumentoExpediente(Base):
    """Capa 3 (seguimiento): vacía hasta que un export traiga estos datos."""
    __tablename__ = "documento_expediente"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    expediente_id   = Column(Integer, ForeignKey("expediente.id"), nullable=False)
    tipo_documento  = Column(String(30), ForeignKey("tipo_documento.codigo"))
    fecha           = Column(Date)
    descripcion     = Column(Text)


class Notificacion(Base):
    """Capa 3 (seguimiento): vacía hasta que un export traiga estos datos."""
    __tablename__ = "notificacion"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    vivienda_num_exp = Column(String(50), ForeignKey("vivienda.num_exp"))
    tipo             = Column(String(30))
    fecha            = Column(Date)
    mensaje          = Column(Text)


class HistorialCambios(Base):
    """Capa 3 (seguimiento): vacía hasta que un export traiga estos datos."""
    __tablename__ = "historial_cambios"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    tabla          = Column(String(50), nullable=False)
    registro_id    = Column(String(80), nullable=False)
    campo          = Column(String(50))
    valor_anterior = Column(Text)
    valor_nuevo    = Column(Text)
    fecha          = Column(DateTime)


class LogSincronizacion(Base):
    """Capa 4: vacía hasta que exista una fuente externa conectada (Plan posterior)."""
    __tablename__ = "log_sincronizacion"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    sistema_externo  = Column(String(30), ForeignKey("sistema_externo.codigo"), nullable=False)
    inicio           = Column(DateTime, nullable=False)
    fin              = Column(DateTime)
    resultado        = Column(String(20))   # ok / error / no_disponible
    detalle          = Column(Text)


class TipoReporte(Base):
    """Ficha de un formato de reporte: qué es, qué mide, qué no mide, sus límites y su confianza."""
    __tablename__ = "tipo_reporte"

    codigo         = Column(String(60), primary_key=True)
    sistema_origen = Column(String(30), nullable=False)
    nombre         = Column(String(120), nullable=False)
    unidad         = Column(String(20), nullable=False)    # organizacion / vivienda / expediente
    que_mide       = Column(Text, nullable=False)
    que_no_mide    = Column(Text, nullable=False)
    limites        = Column(JSON, nullable=False, default=list)
    confianza      = Column(String(20), nullable=False)    # confirmado / inferido / sin_confirmar
    revisado_en    = Column(Date)


class Importacion(Base):
    """Cada archivo cargado, con su resultado. Es la base de la trazabilidad."""
    __tablename__ = "importacion"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    tipo_reporte       = Column(String(60), ForeignKey("tipo_reporte.codigo"))   # vacío si no hay importador
    archivo_nombre     = Column(String(300), nullable=False)
    archivo_huella     = Column(String(64), nullable=False, index=True)          # sha256 del archivo
    fecha_reporte      = Column(Date)
    parametros         = Column(JSON, default=dict)
    estado             = Column(String(20), nullable=False)   # leida / ok / con_advertencias / rechazada / sin_importador
    validacion         = Column(JSON, default=dict)
    filas_leidas       = Column(Integer, default=0)
    version_importador = Column(String(20))
    importado_en       = Column(DateTime, nullable=False)


class RegistroCrudo(Base):
    """Las filas leídas tal cual, ya anonimizadas. Permiten reprocesar sin volver al archivo."""
    __tablename__ = "registro_crudo"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    importacion_id = Column(Integer, ForeignKey("importacion.id"), nullable=False, index=True)
    fila_numero    = Column(Integer, nullable=False)
    datos          = Column(JSON, nullable=False)


class OrganizacionAlias(Base):
    """Cada forma en que un reporte escribe el nombre de una organización."""
    __tablename__ = "organizacion_alias"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    alias              = Column(String(300), nullable=False)
    alias_normalizado  = Column(String(300), nullable=False, unique=True)
    cuit               = Column(String(20), ForeignKey("organizacion.cuit"), nullable=False)
    origen             = Column(String(60))
    pendiente_revision = Column(Boolean, default=False)   # nombre muy parecido a otro ya conocido


class MedidaOrganizacion(Base):
    """Totales de los reportes «Por Solicitante», en formato largo: una fila por métrica."""
    __tablename__ = "medida_organizacion"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    importacion_id = Column(Integer, ForeignKey("importacion.id"), nullable=False, index=True)
    cuit           = Column(String(20), ForeignKey("organizacion.cuit"), nullable=False, index=True)
    consulta       = Column(String(20), nullable=False)   # solicitadas / activadas / finalizadas
    metrica        = Column(String(30), nullable=False)   # solicitudes / beneficiarios / activadas / fin_obras
    valor          = Column(Integer, nullable=False)
    periodo_desde  = Column(Date)
    periodo_hasta  = Column(Date)


class MedidaCategoria(Base):
    """Los totales que cada reporte «Por Solicitante» trae al pie, por categoría (no por organización).
    Antes se usaban solo para validar y se descartaban; ahora quedan disponibles para indicadores
    agregados (por ejemplo, «peso de cada tipo de solicitante»)."""
    __tablename__ = "medida_categoria"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    importacion_id   = Column(Integer, ForeignKey("importacion.id"), nullable=False, index=True)
    tipo_solicitante = Column(String(30), ForeignKey("tipo_solicitante.codigo"), nullable=False, index=True)
    consulta         = Column(String(20), nullable=False)
    metrica          = Column(String(30), nullable=False)
    valor            = Column(Integer, nullable=False)
    periodo_desde    = Column(Date)
    periodo_hasta    = Column(Date)


class ViviendaFoto(Base):
    """Estado de una vivienda según un reporte. Una fila por vivienda y por importación."""
    __tablename__ = "vivienda_foto"
    __table_args__ = (UniqueConstraint("vivienda_num_exp", "importacion_id"),)

    id               = Column(Integer, primary_key=True, autoincrement=True)
    vivienda_num_exp = Column(String(50), ForeignKey("vivienda.num_exp"), nullable=False, index=True)
    importacion_id   = Column(Integer, ForeignKey("importacion.id"), nullable=False, index=True)
    fecha_reporte    = Column(Date)
    fecha_activacion = Column(Date)
    avance_obra      = Column(Float)
    fecha_fin_obra   = Column(Date)
    desaprobada      = Column(Boolean, default=False)
    exp_reclamo      = Column(String(200))   # números separados por coma
    exp_acta         = Column(String(200))
