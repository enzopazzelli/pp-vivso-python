"""Importación de un archivo: reconocer, leer, anonimizar, guardar crudo, validar y mapear.

Uso desde la línea de comandos (desde vivso-python/):
    python -m datos.importar ruta/al/reporte.pdf [--consulta solicitadas|activadas|finalizadas] [--forzar]
"""
import argparse
import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from datos.anonimizador import Anonimizador
from datos.config import ConfiguracionFaltante, anon_secret
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


def huella_archivo(ruta) -> str:
    """sha256 del archivo: identifica un mismo reporte aunque cambie de nombre."""
    resumen = hashlib.sha256()
    with open(ruta, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def _json_seguro(valor):
    """Las fechas se guardan como texto ISO; el resto ya es serializable."""
    if isinstance(valor, dict):
        return {k: _json_seguro(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_json_seguro(v) for v in valor]
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    return valor


def importar_archivo(ruta, sesion: Session, anonimizar, importador=None, forzar: bool = False,
                     opciones: dict | None = None) -> Resultado:
    ruta = Path(ruta)
    huella = huella_archivo(ruta)

    if not forzar:
        previa = (sesion.query(Importacion)
                  .filter(Importacion.archivo_huella == huella,
                          Importacion.estado.in_(("ok", "con_advertencias"))).first())
        if previa is not None:
            return Resultado("duplicada", previa.id, previa.tipo_reporte, previa.filas_leidas, [],
                             [f"Este archivo ya se importó el {previa.importado_en:%d/%m/%Y}."])

    importador = importador or elegir(ruta)
    if importador is None:
        # Si no se reconoce el formato no se sabe qué hay en el nombre del archivo (podría llevar el de una
        # persona): se guarda solo la extensión. La huella y la sonda alcanzan para identificarlo.
        importacion = Importacion(archivo_nombre=f"[nombre omitido]{ruta.suffix.lower()}", archivo_huella=huella,
                                  estado="sin_importador", parametros={"sonda": sonda(ruta)},
                                  importado_en=datetime.now())
        sesion.add(importacion)
        sesion.commit()
        return Resultado("sin_importador", importacion.id, None, 0, [], ["No hay un importador para este formato."])

    try:
        lectura = importador.leer(ruta, anonimizar, opciones)
    except Exception as error:
        # El mensaje de una falla de lectura puede traer texto del archivo (un nombre real, aún sin
        # anonimizar): solo se guarda y se muestra el tipo de error.
        motivo = f"No se pudo leer el archivo ({type(error).__name__})."
        importacion = Importacion(
            tipo_reporte=importador.codigo, archivo_nombre=ruta.name, archivo_huella=huella, estado="rechazada",
            validacion={"error": motivo}, filas_leidas=0, version_importador=importador.version,
            importado_en=datetime.now())
        sesion.add(importacion)
        sesion.commit()
        return Resultado("rechazada", importacion.id, importador.codigo, 0, [], [motivo])
    importacion = Importacion(
        tipo_reporte=importador.codigo, archivo_nombre=ruta.name, archivo_huella=huella,
        fecha_reporte=lectura.fecha_reporte, parametros=_json_seguro(lectura.parametros), estado="leida",
        filas_leidas=len(lectura.filas), version_importador=importador.version, importado_en=datetime.now())
    sesion.add(importacion)
    sesion.flush()
    for numero, fila in enumerate(lectura.filas, start=1):
        sesion.add(RegistroCrudo(importacion_id=importacion.id, fila_numero=numero, datos=_json_seguro(fila)))
    sesion.commit()      # el crudo queda guardado pase lo que pase con la validación

    validacion = importador.validar(lectura)
    chequeos = [{"nombre": c.nombre, "ok": c.ok, "detalle": c.detalle} for c in validacion.chequeos]
    importacion.validacion = {"chequeos": chequeos, "advertencias": lectura.advertencias}
    if not validacion.ok:
        importacion.estado = "rechazada"
        sesion.commit()
        return Resultado("rechazada", importacion.id, importador.codigo, len(lectura.filas), chequeos,
                         lectura.advertencias)

    identificador = importacion.id
    try:
        importador.mapear(lectura, sesion, importacion)
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
        return Resultado("rechazada", identificador, importador.codigo, len(lectura.filas), chequeos,
                         lectura.advertencias + [f"Falló al guardar en el modelo: {error}"])
    return Resultado(importacion.estado, importacion.id, importador.codigo, len(lectura.filas), chequeos,
                     lectura.advertencias)


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
