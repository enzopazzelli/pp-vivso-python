"""Alta y búsqueda de organizaciones a partir del nombre que trae cada reporte.

GDE y VISOC no comparten una clave, así que las organizaciones se unen por nombre normalizado
(tabla de alias). Un nombre muy parecido a uno conocido, pero no igual, crea una organización
nueva y queda marcado para revisión humana.
"""
import difflib
import hashlib

from datos.modelo import OrganizacionAlias
from datos.normalizacion import normalizar_organizacion, tipo_gestora_por_nombre
from db.models import Organizacion

UMBRAL_PARECIDO = 0.92


def cuit_provisional(clave: str) -> str:
    """CUIT provisional y estable, derivado del nombre normalizado, hasta conocer el real."""
    return "PROV-" + hashlib.sha1(clave.encode("utf-8")).hexdigest()[:10].upper()


def _nombres_conocidos(sesion) -> list[str]:
    """Nombres normalizados ya existentes; se guarda en la sesión para no consultarlos cada vez."""
    lista = sesion.info.get("nombres_organizacion")
    if lista is None:
        lista = [n for (n,) in sesion.query(Organizacion.nombre_normalizado).all() if n]
        sesion.info["nombres_organizacion"] = lista
    return lista


def obtener_o_crear_organizacion(sesion, nombre: str, origen: str, tipo_gestora: str | None = None) -> Organizacion:
    clave = normalizar_organizacion(nombre)
    if not clave:
        raise ValueError("El nombre de la organización está vacío")

    alias = sesion.query(OrganizacionAlias).filter_by(alias_normalizado=clave).first()
    if alias is not None:
        return sesion.get(Organizacion, alias.cuit)

    conocidos = _nombres_conocidos(sesion)
    parecidos = difflib.get_close_matches(clave, conocidos, n=1, cutoff=UMBRAL_PARECIDO)
    cuit = cuit_provisional(clave)
    organizacion = Organizacion(
        cuit=cuit, nombre=nombre.strip(), nombre_normalizado=clave,
        tipo_gestora=tipo_gestora or tipo_gestora_por_nombre(nombre),
        cuit_provisional=True, estado="ACTIVA",
    )
    sesion.add(organizacion)
    sesion.add(OrganizacionAlias(
        alias=nombre.strip(), alias_normalizado=clave, cuit=cuit, origen=origen,
        pendiente_revision=bool(parecidos),
    ))
    sesion.flush()
    conocidos.append(clave)
    return organizacion
