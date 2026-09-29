"""Importación de un archivo: reconocer, leer, anonimizar, guardar crudo, validar y mapear.

`previsualizar()` hace todo lo que no escribe (reconocer, leer, validar); `confirmar()` hace lo que sí
escribe (guardar el crudo y, si valida, mapear). `importar_archivo()` las compone para quien no
necesita el paso intermedio (la línea de comandos, la API) — su comportamiento no cambió.

Uso desde la línea de comandos (desde vivso-python/):
    python -m datos.importar ruta/al/reporte.pdf [--consulta solicitadas|activadas|finalizadas] [--forzar]
"""
import argparse
import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path, PureWindowsPath

from sqlalchemy.orm import Session

from datos.anonimizador import Anonimizador
from datos.config import ConfiguracionFaltante, anon_secret
from datos.importadores.base import Importador, Lectura, Validacion
from datos.importadores.registro import elegir, sonda
from datos.modelo import Importacion, RegistroCrudo
from datos.sesion import crear_engine, migrar, sembrar_catalogos

_SALIDA = {"ok": 0, "con_advertencias": 0, "duplicada": 0, "rechazada": 1, "sin_importador": 2}


@dataclass
class Resultado:
    estado: str          # ok / con_advertencias / rechazada / sin_importador / duplicada
    importacion_id: int | None
    tipo_reporte: str | None
    filas_leidas: int
    chequeos: list[dict] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)


@dataclass
class Previa:
    """Lo que se sabe de un archivo antes de decidir si guardarlo. `previsualizar()` no escribe nada
    en la sesión: toda esta información ya está lista para mostrarse antes de confirmar."""
    huella: str
    duplicada: Importacion | None      # la importación anterior de este mismo archivo, si existe
    importador: Importador | None      # None si no se reconoce el formato
    sonda: dict | None                 # solo si `importador` es None: la "forma" del archivo
    lectura: Lectura | None            # None si no se reconoce, o si `leer()` falló
    error_lectura: str | None          # el nombre del tipo de excepción si `leer()` falló
    validacion: Validacion | None      # None si no hay `lectura`


def huella_archivo(ruta) -> str:
    """sha256 del archivo: identifica un mismo reporte aunque cambie de nombre."""
    resumen = hashlib.sha256()
    with open(ruta, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def nombre_archivo_seguro(nombre: str | None) -> str:
    """El nombre que manda quien sube un archivo no es confiable: una ruta absoluta o con `..` uniría
    con `Path` fuera de la carpeta que corresponde (path traversal). Acá se queda solo con el nombre de
    archivo final, sin ningún componente de carpeta ni unidad — `PureWindowsPath` porque este proyecto
    corre en Windows y entiende tanto `/` como `\\` como separador, a diferencia de `PurePosixPath`."""
    base = PureWindowsPath(nombre or "").name
    return base if base not in ("", ".", "..") else "archivo"


def _json_seguro(valor):
    """Las fechas se guardan como texto ISO; el resto ya es serializable."""
    if isinstance(valor, dict):
        return {k: _json_seguro(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_json_seguro(v) for v in valor]
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    return valor


def _buscar_duplicada(sesion: Session, huella: str) -> Importacion | None:
    return (sesion.query(Importacion)
            .filter(Importacion.archivo_huella == huella, Importacion.estado.in_(("ok", "con_advertencias")))
            .first())


def previsualizar(ruta, sesion: Session, anonimizar, importador: Importador | None = None,
                  opciones: dict | None = None) -> Previa:
    """Reconoce, lee (ya anonimizado) y valida. No escribe nada en la sesión ni en la base."""
    ruta = Path(ruta)
    huella = huella_archivo(ruta)
    duplicada = _buscar_duplicada(sesion, huella)

    importador = importador or elegir(ruta)
    if importador is None:
        return Previa(huella, duplicada, None, sonda(ruta), None, None, None)

    try:
        lectura = importador.leer(ruta, anonimizar, opciones)
    except Exception as error:
        # El mensaje de una falla de lectura puede traer texto del archivo (un nombre real, aún sin
        # anonimizar): solo se guarda el tipo de error.
        return Previa(huella, duplicada, importador, None, None, type(error).__name__, None)

    validacion = importador.validar(lectura)
    return Previa(huella, duplicada, importador, None, lectura, None, validacion)


def confirmar(previa: Previa, ruta, sesion: Session, forzar: bool = False) -> Resultado:
    """Guarda el crudo y, si `previa.validacion.ok`, mapea al modelo. Commitea."""
    ruta = Path(ruta)

    if previa.duplicada is not None and not forzar:
        return Resultado("duplicada", previa.duplicada.id, previa.duplicada.tipo_reporte,
                         previa.duplicada.filas_leidas, [],
                         [f"Este archivo ya se importó el {previa.duplicada.importado_en:%d/%m/%Y}."])

    if previa.importador is None:
        importacion = Importacion(archivo_nombre=f"[nombre omitido]{ruta.suffix.lower()}",
                                  archivo_huella=previa.huella, estado="sin_importador",
                                  parametros={"sonda": previa.sonda}, importado_en=datetime.now())
        sesion.add(importacion)
        sesion.commit()
        return Resultado("sin_importador", importacion.id, None, 0, [], ["No hay un importador para este formato."])

    if previa.lectura is None:
        motivo = f"No se pudo leer el archivo ({previa.error_lectura})."
        importacion = Importacion(
            tipo_reporte=previa.importador.codigo, archivo_nombre=ruta.name, archivo_huella=previa.huella,
            estado="rechazada", validacion={"error": motivo}, filas_leidas=0,
            version_importador=previa.importador.version, importado_en=datetime.now())
        sesion.add(importacion)
        sesion.commit()
        return Resultado("rechazada", importacion.id, previa.importador.codigo, 0, [], [motivo])

    lectura = previa.lectura
    importacion = Importacion(
        tipo_reporte=previa.importador.codigo, archivo_nombre=ruta.name, archivo_huella=previa.huella,
        fecha_reporte=lectura.fecha_reporte, parametros=_json_seguro(lectura.parametros), estado="leida",
        filas_leidas=len(lectura.filas), version_importador=previa.importador.version, importado_en=datetime.now())
    sesion.add(importacion)
    sesion.flush()
    for numero, fila in enumerate(lectura.filas, start=1):
        sesion.add(RegistroCrudo(importacion_id=importacion.id, fila_numero=numero, datos=_json_seguro(fila)))
    sesion.commit()      # el crudo queda guardado pase lo que pase con la validación

    validacion = previa.validacion
    chequeos = [{"nombre": c.nombre, "ok": c.ok, "detalle": c.detalle} for c in validacion.chequeos]
    importacion.validacion = {"chequeos": chequeos, "advertencias": lectura.advertencias}
    if not validacion.ok:
        importacion.estado = "rechazada"
        sesion.commit()
        return Resultado("rechazada", importacion.id, previa.importador.codigo, len(lectura.filas), chequeos,
                         lectura.advertencias)

    identificador = importacion.id
    try:
        previa.importador.mapear(lectura, sesion, importacion)
        importacion.estado = "con_advertencias" if lectura.advertencias else "ok"
        sesion.commit()
    except Exception as error:        # se deshace solo el mapeo; el crudo ya estaba guardado
        sesion.rollback()
        sesion.info.pop("nombres_organizacion", None)   # la memoria de nombres no debe conservar lo deshecho
        importacion = sesion.get(Importacion, identificador)
        importacion.estado = "rechazada"
        importacion.validacion = {"chequeos": chequeos, "advertencias": lectura.advertencias,
                                  "error": f"{type(error).__name__}: {error}"}
        sesion.commit()
        return Resultado("rechazada", identificador, previa.importador.codigo, len(lectura.filas), chequeos,
                         lectura.advertencias + [f"Falló al guardar en el modelo: {error}"])
    return Resultado(importacion.estado, importacion.id, previa.importador.codigo, len(lectura.filas), chequeos,
                     lectura.advertencias)


def importar_archivo(ruta, sesion: Session, anonimizar, importador=None, forzar: bool = False,
                     opciones: dict | None = None) -> Resultado:
    """Sin cambios de comportamiento respecto de antes de este plan: sigue haciendo todo de un tirón,
    para quien no necesita el paso de vista previa (la línea de comandos, la API del Plan 4)."""
    ruta = Path(ruta)
    if not forzar:
        # Cortar acá, antes de leer nada, es la misma optimización de siempre: no tiene sentido
        # reconocer ni parsear un archivo que ya sabemos que no hace falta.
        duplicada = _buscar_duplicada(sesion, huella_archivo(ruta))
        if duplicada is not None:
            return Resultado("duplicada", duplicada.id, duplicada.tipo_reporte, duplicada.filas_leidas, [],
                             [f"Este archivo ya se importó el {duplicada.importado_en:%d/%m/%Y}."])
    previa = previsualizar(ruta, sesion, anonimizar, importador, opciones)
    return confirmar(previa, ruta, sesion, forzar)


def _imprimir(resultado: Resultado, archivo: str) -> None:
    print(f"Archivo: {archivo}")
    print(f"Formato: {resultado.tipo_reporte or 'no reconocido'}")
    print(f"Estado: {resultado.estado}")
    print(f"Filas leídas: {resultado.filas_leidas}")
    for chequeo in resultado.chequeos:
        print(f"  {'OK   ' if chequeo['ok'] else 'FALLA'} {chequeo['nombre']}: {chequeo['detalle']}")
    for aviso in resultado.advertencias:
        print(f"  AVISO {aviso}")


def main(argv=None) -> int:
    analizador = argparse.ArgumentParser(prog="python -m datos.importar", description="Importa un reporte de VISOC.")
    analizador.add_argument("archivo")
    analizador.add_argument("--consulta", choices=["solicitadas", "activadas", "finalizadas"],
                            help="Solo para «Por Solicitante»: si no se indica, se infiere por los datos.")
    analizador.add_argument("--forzar", action="store_true", help="Importar aunque el archivo ya se haya importado.")
    args = analizador.parse_args(argv)

    try:
        anonimizador = Anonimizador(anon_secret())
    except ConfiguracionFaltante as error:
        print(f"Falta configurar: {error}")
        return 3

    migrar()
    engine = crear_engine()
    with Session(engine) as sesion:
        sembrar_catalogos(sesion)
        resultado = importar_archivo(args.archivo, sesion, anonimizador, forzar=args.forzar,
                                     opciones={"consulta": args.consulta})
    _imprimir(resultado, args.archivo)
    return _SALIDA[resultado.estado]


if __name__ == "__main__":
    raise SystemExit(main())
