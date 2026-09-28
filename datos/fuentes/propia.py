"""Fuente propia: la base construida por los importadores del Plan 1 (`db/datos_reales.db`)."""
import pandas as pd
from sqlalchemy.exc import OperationalError

from datos.fuentes.base import FuenteDeDatos
from datos.fuentes.estructura import (
    COLUMNAS_EXPEDIENTE, COLUMNAS_MEDIDA, COLUMNAS_MEDIDA_CATEGORIA, COLUMNAS_ORGANIZACION, COLUMNAS_RECLAMO,
    COLUMNAS_VIVIENDA, marco_vacio,
)
from datos.modelo import Expediente, Importacion, MedidaCategoria, MedidaOrganizacion, Reclamo
from db.models import Organizacion, Vivienda


class FuentePropia(FuenteDeDatos):
    """No abre conexión hasta que se le pide un dato: instanciarla es siempre seguro."""

    nombre = "propia"

    def __init__(self, sesion=None):
        self._sesion_dada = sesion
        self._sesion_propia = None

    @property
    def _sesion(self):
        if self._sesion_dada is not None:
            return self._sesion_dada
        if self._sesion_propia is None:
            from sqlalchemy.orm import Session

            from datos.sesion import crear_engine
            self._sesion_propia = Session(crear_engine())
        return self._sesion_propia

    @staticmethod
    def _con_esquema(consulta):
        """Ejecuta la consulta, y convierte «la tabla/columna no existe» en un error que explica cómo
        resolverlo. Sin esto, pedirle un dato a una base sin crear o a medio migrar tira un error de
        SQL crudo (`no such table: vivienda`), que no dice qué hacer."""
        try:
            return consulta()
        except OperationalError as error:
            mensaje = str(error).lower()
            if "no such table" in mensaje or "no such column" in mensaje:
                raise RuntimeError(
                    "La base de datos propia no existe o no está migrada. Corré "
                    "`python -m datos.importar <archivo>` (crea y migra la base sola) para cargar un "
                    "reporte, o usá otra fuente mientras tanto (FUENTE=simulada / FUENTE=json_prueba)."
                ) from error
            raise

    def viviendas(self) -> pd.DataFrame:
        filas = self._con_esquema(lambda: self._sesion.query(Vivienda).all())
        if not filas:
            return marco_vacio(COLUMNAS_VIVIENDA)
        activaciones = self._con_esquema(self._fecha_activacion_por_vivienda)
        registros = []
        for v in filas:
            fila = {c: getattr(v, c) for c in COLUMNAS_VIVIENDA if c != "fecha_activacion"}
            fila["fecha_activacion"] = activaciones.get(v.num_exp)
            registros.append(fila)
        return pd.DataFrame(registros)[COLUMNAS_VIVIENDA]

    def _fecha_activacion_por_vivienda(self) -> dict:
        """Vivienda -> fecha de activación de su foto más reciente. Igual criterio que usa el
        importador para decidir qué reporte manda (Plan 1): el más nuevo por `fecha_reporte`."""
        from sqlalchemy import func

        from datos.modelo import ViviendaFoto
        subq = (self._sesion.query(ViviendaFoto.vivienda_num_exp,
                                    func.max(ViviendaFoto.fecha_reporte).label("max_fecha"))
                .group_by(ViviendaFoto.vivienda_num_exp).subquery())
        filas = (self._sesion.query(ViviendaFoto.vivienda_num_exp, ViviendaFoto.fecha_activacion)
                 .join(subq, (ViviendaFoto.vivienda_num_exp == subq.c.vivienda_num_exp)
                       & (ViviendaFoto.fecha_reporte == subq.c.max_fecha))
                 .all())
        return dict(filas)

    def organizaciones(self) -> pd.DataFrame:
        filas = self._con_esquema(lambda: self._sesion.query(Organizacion).all())
        if not filas:
            return marco_vacio(COLUMNAS_ORGANIZACION)
        return pd.DataFrame(
            [{c: getattr(o, c) for c in COLUMNAS_ORGANIZACION} for o in filas])[COLUMNAS_ORGANIZACION]

    def medidas(self) -> pd.DataFrame:
        filas = self._con_esquema(lambda: (
            self._sesion.query(MedidaOrganizacion, Organizacion.nombre, Importacion.tipo_reporte,
                               Importacion.fecha_reporte)
            .join(Organizacion, MedidaOrganizacion.cuit == Organizacion.cuit)
            .join(Importacion, MedidaOrganizacion.importacion_id == Importacion.id).all()))
        if not filas:
            return marco_vacio(COLUMNAS_MEDIDA)
        registros = [{
            "cuit": m.cuit, "nombre_organizacion": nombre, "tipo_reporte": tipo_reporte,
            "consulta": m.consulta, "metrica": m.metrica, "valor": m.valor,
            "periodo_desde": m.periodo_desde, "periodo_hasta": m.periodo_hasta, "fecha_reporte": fecha_reporte,
        } for m, nombre, tipo_reporte, fecha_reporte in filas]
        return pd.DataFrame(registros)[COLUMNAS_MEDIDA]

    def expedientes(self) -> pd.DataFrame:
        filas = self._con_esquema(lambda: (
            self._sesion.query(Expediente, Importacion.fecha_reporte)
            .outerjoin(Importacion, Expediente.origen_importacion_id == Importacion.id).all()))
        if not filas:
            return marco_vacio(COLUMNAS_EXPEDIENTE)
        registros = [{
            "id": e.id, "vivienda_num_exp": e.vivienda_num_exp, "numero": e.numero, "formato": e.formato,
            "tipo": e.tipo, "fecha_reporte": fecha_reporte,
        } for e, fecha_reporte in filas]
        return pd.DataFrame(registros)[COLUMNAS_EXPEDIENTE]

    def reclamos(self) -> pd.DataFrame:
        filas = self._con_esquema(lambda: self._sesion.query(Reclamo).all())
        if not filas:
            return marco_vacio(COLUMNAS_RECLAMO)
        registros = [{"id": r.id, "cuit": r.cuit, "expediente_id": r.expediente_id,
                     "fecha": r.fecha, "estado": r.estado} for r in filas]
        return pd.DataFrame(registros)[COLUMNAS_RECLAMO]

    def medidas_categoria(self) -> pd.DataFrame:
        filas = self._con_esquema(lambda: (
            self._sesion.query(MedidaCategoria, Importacion.fecha_reporte)
            .join(Importacion, MedidaCategoria.importacion_id == Importacion.id).all()))
        if not filas:
            return marco_vacio(COLUMNAS_MEDIDA_CATEGORIA)
        registros = [{
            "tipo_solicitante": m.tipo_solicitante, "consulta": m.consulta, "metrica": m.metrica,
            "valor": m.valor, "periodo_desde": m.periodo_desde, "periodo_hasta": m.periodo_hasta,
            "fecha_reporte": fecha_reporte,
        } for m, fecha_reporte in filas]
        return pd.DataFrame(registros)[COLUMNAS_MEDIDA_CATEGORIA]
