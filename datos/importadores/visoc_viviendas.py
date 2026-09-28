"""Importador del reporte «Viviendas Según Solicitante» de VISOC (PDF).

Una fila por vivienda de un solicitante, con esta forma:
    fecha · titular · expediente · tipo · dormitorios · clasificación · departamento ·
    [reclamo] [acta digital] [activación] [DES] avance [fin de obra]
Las columnas de reclamo y de acta digital pueden venir vacías, así que se distinguen por su posición
horizontal, tomada de la cabecera. Al final el reporte trae una línea con los totales.
"""
import hashlib
import re
from collections import Counter
from datetime import date
from pathlib import Path

from sqlalchemy import func

from datos.catalogos import CLASIFICACIONES, TIPO_SOLICITANTE_VISOC, TIPO_VIVIENDA, departamento_canonico
from datos.importadores.base import Chequeo, Importador, Lectura, Validacion, fecha_corta
from datos.importadores.pdf import leer_lineas_tokens
from datos.modelo import Clasificacion, Expediente, ViviendaFoto
from datos.normalizacion import clasificar_formato_expediente, normalizar_expediente
from datos.organizaciones import obtener_o_crear_organizacion
from db.models import Vivienda

_FECHA = re.compile(r"^\d{2}/\d{2}/\d{2}$")
_AFO = re.compile(r"^\d{1,3},\d{2}$")
# Expediente de solicitud: NNN-NN-NNNN, NNNNN-NN-NNNN o NNNNNNN-AAAA (conviven varios formatos)
_EXPEDIENTE = re.compile(r"^(\d{3,6}-\d{2}-\d{4}|\d{5,8}-\d{4})$")
_NUMERO = re.compile(r"^\d{2,9}(-\d{2,9})*$")
_PALABRA = re.compile(r"^[A-ZÁÉÍÓÚÑ.]+$")
_TIPOS = {"URB", "RUR", "ECO"}
_TOTALES = re.compile(
    r"Cantidad Solicitadas:\s*(\d+)\s*Cantidad Finalizadas:\s*(\d+)\s*"
    r"Cantidad Desaprobadas:\s*(\d+)\s*Cantidad Sin Finalizar:\s*(\d+)")
_CLASIFICACION_CANONICA = {codigo.lower(): codigo for codigo in CLASIFICACIONES}   # «1A» y «1a» → «1a»; «ot» → «OT»


def _x_columnas(lineas) -> tuple[float | None, float | None]:
    """Posición horizontal de las columnas Exp.Reclamo y Acta Digital, según la cabecera."""
    for tokens in lineas:
        textos = [t for t, _ in tokens]
        if "Titular" in textos and "Expediente" in textos:
            reclamo = next((x for t, x in tokens if "Reclamo" in t), None)
            acta = next((x for t, x in tokens if t == "Acta"), None)
            if reclamo is not None and acta is not None:
                return reclamo, acta
    return None, None


def parsear_viviendas(lineas, anonimizar) -> tuple[dict, list[dict], dict | None, list[str]]:
    """Devuelve (parámetros, filas, totales declarados o None, advertencias)."""
    x_reclamo, x_acta = _x_columnas(lineas)
    corte = None if x_reclamo is None else (x_reclamo + x_acta) / 2   # a la izquierda: reclamo; a la derecha: acta
    parametros: dict = {}
    filas: list[dict] = []
    declarados = None
    advertencias: list[str] = []
    previa = ""     # última línea de texto antes de la cabecera de columnas: es el nombre del solicitante

    for tokens in lineas:
        textos = [t for t, _ in tokens]
        linea = " ".join(textos)
        if "Titular" in textos and "Expediente" in textos:
            # Solo la primera cabecera: si se repitiera en cada página, la línea anterior podría ser
            # la continuación del nombre de un titular o un pie de página, no el solicitante.
            parametros.setdefault("solicitante_nombre", previa)
            continue
        if linea.startswith("Solicitante Tipo:"):
            parametros["solicitante_tipo"] = linea.split(":", 1)[1].strip()
        elif re.match(r"^\S+:\s*\d{2}/\d{2}/\d{2}$", linea) and "fecha_reporte" not in parametros:
            parametros["fecha_reporte"] = fecha_corta(linea.split(":", 1)[1].strip()).isoformat()
        coincide = _TOTALES.search(linea)
        if coincide:
            solicitadas, finalizadas, desaprobadas, sin_finalizar = (int(n) for n in coincide.groups())
            declarados = {"solicitadas": solicitadas, "finalizadas": finalizadas,
                          "desaprobadas": desaprobadas, "sin_finalizar": sin_finalizar}
            continue
        if not textos or not _FECHA.match(textos[0]):
            if textos and not linea.endswith(":"):
                previa = linea
            continue

        try:
            i = next(j for j in range(1, len(textos))
                     if _EXPEDIENTE.match(textos[j]) and j + 1 < len(textos) and textos[j + 1] in _TIPOS)
        except StopIteration:
            # Solo la forma de la línea: nunca su texto, que puede incluir un nombre.
            advertencias.append("Fila que empieza con fecha y no se pudo interpretar: "
                                + re.sub(r"\d", "9", re.sub(r"[^\W\d_]", "x", linea))[:60])
            continue

        cola = tokens[i + 4:]                        # lo que sigue a tipo, dormitorios y clasificación
        k = 0
        # «DES» (desaprobada) también son letras: sin esta guarda, una vivienda desaprobada sin
        # fecha de activación lo sumaría al nombre del departamento.
        while k < len(cola) and _PALABRA.match(cola[k][0]) and cola[k][0] != "DES":
            k += 1
        departamento = " ".join(t for t, _ in cola[:k])
        reclamos: list[str] = []
        actas: list[str] = []
        fechas: list[date] = []
        avance = None
        desaprobada = False
        for texto, x in cola[k:]:
            if _FECHA.match(texto):
                fechas.append(fecha_corta(texto))
            elif _AFO.match(texto):
                avance = float(texto.replace(",", "."))
            elif texto == "DES":
                desaprobada = True
            elif _NUMERO.match(texto):
                (reclamos if (corte is not None and x < corte) else actas).append(texto)

        filas.append({
            "fecha_solicitud": fecha_corta(textos[0]),
            "titular_seudonimo": anonimizar(" ".join(textos[1:i])),   # el nombre real NO sale de acá
            "expediente": textos[i],
            "tipo": textos[i + 1],
            "dormitorios": int(textos[i + 2]),
            "clasificacion": textos[i + 3],
            "departamento": departamento,
            "exp_reclamo": reclamos,
            "exp_acta": actas,
            "fecha_activacion": fechas[0] if fechas else None,
            "avance_obra": avance,
            "fecha_fin_obra": fechas[1] if len(fechas) > 1 else None,
            "desaprobada": desaprobada,
        })
    return parametros, filas, declarados, advertencias


def reconoce_lineas(lineas) -> float:
    if lineas and "Viviendas Segun Solicitante" in " ".join(t for t, _ in lineas[0]):
        return 0.95
    for tokens in lineas[:12]:
        textos = [t for t, _ in tokens]
        if "Titular" in textos and "Expediente" in textos and "Fin" in textos:
            return 0.6
    return 0.0


def clave_vivienda(expediente: str, titular_seudonimo: str, ocurrencia: int = 1) -> str:
    """Clave estable de una vivienda entre reportes: expediente + huella del titular ya anonimizado.
    En los reportes reales un mismo número de expediente aparece en más de una fila, así que el
    expediente solo no identifica a la vivienda. Si la misma pareja se repite dentro de un reporte,
    la segunda y siguientes reciben un sufijo `.n`."""
    huella = hashlib.sha1(titular_seudonimo.encode("utf-8")).hexdigest()[:6]
    base = f"{normalizar_expediente(expediente)}#{huella}"
    return base if ocurrencia == 1 else f"{base}.{ocurrencia}"


def _avisar_expedientes_repetidos(filas: list[dict]) -> list[str]:
    """Un expediente no debería repetirse. Se avisa, sin rechazar el reporte, para confirmarlo con el área."""
    conteo = Counter(normalizar_expediente(f["expediente"]) for f in filas)
    involucradas = sum(n for n in conteo.values() if n > 1)
    if not involucradas:
        return []
    return [f"{involucradas} filas (de {len(filas)}) comparten su número de expediente con otra fila. "
            "Un expediente no debería repetirse: puede ser un dato todavía sin registrar; "
            "conviene confirmarlo con el área."]


def _registrar_expedientes(sesion, num_exp: str, expediente: str, fila: dict, importacion_id: int) -> None:
    """Un expediente puede aparecer en varios reportes; no se duplica (misma vivienda + número + tipo)."""
    candidatos = [("solicitud", expediente)]
    candidatos += [("reclamo", normalizar_expediente(n)) for n in fila["exp_reclamo"]]
    candidatos += [("acta", normalizar_expediente(n)) for n in fila["exp_acta"]]
    for tipo, numero in candidatos:
        existe = sesion.query(Expediente).filter_by(vivienda_num_exp=num_exp, numero=numero, tipo=tipo).first()
        if existe is None:
            sesion.add(Expediente(vivienda_num_exp=num_exp, numero=numero, tipo=tipo,
                                  formato=clasificar_formato_expediente(numero),
                                  origen_importacion_id=importacion_id))


def _estado(fila: dict) -> str:
    """Iniciada = sin activar; Avanzada = activada pero sin acta de finalización (el técnico ya certificó
    la obra y el área activó el expediente para que pueda emitir el acta); Finalizada = avance 100."""
    if fila["desaprobada"]:
        return "Desaprobada"
    if fila["avance_obra"] == 100.0:
        return "Finalizada"
    if fila["fecha_activacion"] is not None:
        return "Avanzada"
    return "Iniciada"


class VisocViviendasSegunSolicitante(Importador):
    codigo = "visoc_viviendas_segun_solicitante"

    def reconoce(self, ruta: Path) -> float:
        if Path(ruta).suffix.lower() != ".pdf":
            return 0.0
        try:
            return reconoce_lineas(leer_lineas_tokens(ruta, max_paginas=1))
        except Exception:
            return 0.0

    def leer(self, ruta: Path, anonimizar, opciones: dict | None = None) -> Lectura:
        return self.lectura_desde_lineas(leer_lineas_tokens(ruta), anonimizar)

    def lectura_desde_lineas(self, lineas, anonimizar) -> Lectura:
        parametros, filas, declarados, advertencias = parsear_viviendas(lineas, anonimizar)
        fecha = date.fromisoformat(parametros["fecha_reporte"]) if "fecha_reporte" in parametros else None
        advertencias.extend(_avisar_expedientes_repetidos(filas))
        return Lectura(self.codigo, parametros, fecha, filas, declarados or {}, advertencias)

    def validar(self, lectura: Lectura) -> Validacion:
        declarados = lectura.totales_declarados
        if not declarados:
            return Validacion([Chequeo("totales_presentes", False, "El reporte no trae la línea de totales")])
        filas = lectura.filas
        finalizadas = sum(1 for f in filas if f["avance_obra"] == 100.0)
        desaprobadas = sum(1 for f in filas if f["desaprobada"])
        # El pie de VISOC cuenta como «sin finalizar» a toda obra que no llegó a 100 (no solo a las de 0).
        sin_finalizar = sum(1 for f in filas if (f["avance_obra"] or 0.0) < 100.0 and not f["desaprobada"])
        return Validacion([
            Chequeo("totales_presentes", True, "El reporte trae la línea de totales"),
            Chequeo("filas_vs_solicitadas", len(filas) == declarados["solicitadas"],
                    f"filas {len(filas)} · reporte {declarados['solicitadas']}"),
            Chequeo("finalizadas", finalizadas == declarados["finalizadas"],
                    f"filas {finalizadas} · reporte {declarados['finalizadas']}"),
            Chequeo("desaprobadas", desaprobadas == declarados["desaprobadas"],
                    f"filas {desaprobadas} · reporte {declarados['desaprobadas']}"),
            Chequeo("sin_finalizar", sin_finalizar == declarados["sin_finalizar"],
                    f"filas {sin_finalizar} · reporte {declarados['sin_finalizar']}"),
        ])

    def mapear(self, lectura: Lectura, sesion, importacion) -> None:
        p = lectura.parametros
        organizacion = None
        if p.get("solicitante_nombre"):
            organizacion = obtener_o_crear_organizacion(
                sesion, p["solicitante_nombre"], origen=self.codigo,
                tipo_gestora=TIPO_SOLICITANTE_VISOC.get(p.get("solicitante_tipo")))

        vistas: Counter = Counter()
        with sesion.no_autoflush:
            for fila in lectura.filas:
                expediente = normalizar_expediente(fila["expediente"])
                pareja = (expediente, fila["titular_seudonimo"])
                vistas[pareja] += 1
                num_exp = clave_vivienda(expediente, fila["titular_seudonimo"], vistas[pareja])
                mas_reciente = (sesion.query(func.max(ViviendaFoto.fecha_reporte))
                                .filter(ViviendaFoto.vivienda_num_exp == num_exp).scalar())
                # El catálogo usa mayúsculas para «OT» y minúsculas para el resto: se busca sin distinguir.
                clasificacion = _CLASIFICACION_CANONICA.get(fila["clasificacion"].lower(), fila["clasificacion"])
                catalogo = sesion.get(Clasificacion, clasificacion)

                vivienda = sesion.get(Vivienda, num_exp)
                es_nueva = vivienda is None
                if es_nueva:
                    vivienda = Vivienda(num_exp=num_exp, departamento="SIN DATO", estado=_estado(fila))
                    sesion.add(vivienda)
                # `vivienda` guarda el estado ACTUAL: un reporte más viejo suma historial (la foto) pero
                # no pisa nada de lo que ya dijo uno más nuevo (los dormitorios y la clasificación también cambian).
                es_mas_nuevo = mas_reciente is None or (
                    lectura.fecha_reporte is not None and lectura.fecha_reporte >= mas_reciente)
                if es_nueva or es_mas_nuevo:
                    vivienda.expediente = expediente
                    vivienda.departamento = (
                        departamento_canonico(fila["departamento"]) or fila["departamento"] or "SIN DATO")
                    vivienda.tipo_vivienda = TIPO_VIVIENDA.get(fila["tipo"])
                    vivienda.cant_dormitorios = fila["dormitorios"]
                    vivienda.clasificacion = clasificacion
                    vivienda.criterio = catalogo.criterio if catalogo else None
                    vivienda.fecha_solicitud = fila["fecha_solicitud"]
                    vivienda.titular_seudonimo = fila["titular_seudonimo"]
                    if organizacion is not None:
                        vivienda.cuit_org = organizacion.cuit
                    vivienda.estado = _estado(fila)
                    vivienda.avance_obra = int(fila["avance_obra"] or 0)
                    fin = fila["fecha_fin_obra"]
                    vivienda.fecha_fin = fin.strftime("%d-%m-%Y") if fin else None

                sesion.add(ViviendaFoto(
                    vivienda_num_exp=num_exp, importacion_id=importacion.id, fecha_reporte=lectura.fecha_reporte,
                    fecha_activacion=fila["fecha_activacion"], avance_obra=fila["avance_obra"],
                    fecha_fin_obra=fila["fecha_fin_obra"], desaprobada=fila["desaprobada"],
                    exp_reclamo=",".join(fila["exp_reclamo"]) or None, exp_acta=",".join(fila["exp_acta"]) or None))
                _registrar_expedientes(sesion, num_exp, expediente, fila, importacion.id)
        sesion.flush()
