"""Importador del reporte «Por Solicitante» de VISOC (PDF).

Trae, por organización y período, cuatro números: solicitudes, beneficiarios, activadas y fin de
obra. Al pie trae los totales de 4 categorías (cooperativa, asociación/ONG, comisionado,
intendencia). Las tres consultas (solicitadas, activadas, finalizadas) tienen la MISMA cabecera:
se distinguen solo por sus datos, así que la consulta se infiere.
"""
import re
from datetime import date
from pathlib import Path

from datos.importadores.base import Chequeo, Importador, Lectura, Validacion, fecha_corta
from datos.importadores.pdf import leer_lineas_texto
from datos.modelo import MedidaCategoria, MedidaOrganizacion
from datos.organizaciones import obtener_o_crear_organizacion

METRICAS = ("solicitudes", "beneficiarios", "activadas", "fin_obras")
CATEGORIAS = ("COOPERATIVA", "ASOCIACION/ONG", "COMISIONADO", "INTENDENCIA")
_PIE = CATEGORIAS + ("EXTERNA", "TOTAL GRAL")
# Las etiquetas del pie tal como las imprime VISOC, traducidas al código del catálogo tipo_solicitante
# (datos/catalogos.py::TIPO_SOLICITANTE). EXTERNA se guarda igual que las demás, aunque hoy siempre da 0.
_CODIGO_TIPO_SOLICITANTE = {
    "COOPERATIVA": "COOPERATIVA", "ASOCIACION/ONG": "ASOCIACION_ONG",
    "COMISIONADO": "COMISIONADO", "INTENDENCIA": "INTENDENCIA", "EXTERNA": "EXTERNA",
}
_ENCABEZADOS = ("Por Solicitante", "Fecha:", "Periodo:", "Solicitante Solicitudes")
_FILA = re.compile(r"^(.*\S)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)$")
_CABECERA = "Solicitante Solicitudes Beneficiarios Activadas Fin Obras"


def parsear_por_solicitante(lineas: list[str]) -> tuple[dict, list[dict], dict]:
    """Devuelve (parámetros del reporte, filas por organización, pie por categoría)."""
    parametros: dict = {}
    filas: list[dict] = []
    pie: dict = {}
    for crudo in lineas:
        linea = crudo.strip()
        fecha = re.match(r"^Fecha:\s*(\d{2}/\d{2}/\d{2})$", linea)
        if fecha:
            parametros["fecha_reporte"] = fecha_corta(fecha.group(1)).isoformat()
        periodo = re.match(r"^Periodo:\s*(\d{2}/\d{2}/\d{2})\s+al\s+(\d{2}/\d{2}/\d{2})$", linea)
        if periodo:
            parametros["periodo_desde"] = fecha_corta(periodo.group(1)).isoformat()
            parametros["periodo_hasta"] = fecha_corta(periodo.group(2)).isoformat()
        if not linea or any(linea.startswith(e) for e in _ENCABEZADOS):
            continue
        coincide = _FILA.match(linea)
        if not coincide:
            continue
        nombre = coincide.group(1).strip()
        numeros = tuple(int(n.replace(".", "")) for n in coincide.groups()[1:])
        if nombre in _PIE:
            pie[nombre] = numeros
        else:
            filas.append({"nombre": nombre, **dict(zip(METRICAS, numeros))})
    return parametros, filas, pie


def inferir_consulta(filas: list[dict]) -> str:
    """Las tres consultas no dicen cuál son. Se infiere: en «finalizadas» todo lo solicitado está
    activado y terminado; en «activadas», todo lo solicitado está activado."""
    if all(f["solicitudes"] == f["activadas"] == f["fin_obras"] for f in filas):
        return "finalizadas"
    if all(f["solicitudes"] == f["activadas"] for f in filas):
        return "activadas"
    return "solicitadas"


def reconoce_lineas(lineas: list[str]) -> float:
    inicio = [l.strip() for l in lineas[:8]]
    if any("Por Solicitante" in l for l in inicio) and any(l.startswith(_CABECERA) for l in inicio):
        return 0.95
    return 0.0


class VisocPorSolicitante(Importador):
    codigo = "visoc_por_solicitante"

    def reconoce(self, ruta: Path) -> float:
        if Path(ruta).suffix.lower() != ".pdf":
            return 0.0
        try:
            return reconoce_lineas(leer_lineas_texto(ruta, max_paginas=1))
        except Exception:
            return 0.0

    def leer(self, ruta: Path, anonimizar, opciones: dict | None = None) -> Lectura:
        consulta = (opciones or {}).get("consulta")
        return self.lectura_desde_lineas(leer_lineas_texto(ruta), consulta)

    def lectura_desde_lineas(self, lineas: list[str], consulta: str | None = None) -> Lectura:
        parametros, filas, pie = parsear_por_solicitante(lineas)
        parametros["consulta"] = consulta or (inferir_consulta(filas) if filas else "solicitadas")
        parametros["consulta_inferida"] = consulta is None
        fecha = date.fromisoformat(parametros["fecha_reporte"]) if "fecha_reporte" in parametros else None
        advertencias: list[str] = []
        total_gral = pie.get("TOTAL GRAL")
        if total_gral is not None:
            sumas = tuple(sum(f[m] for f in filas) for m in METRICAS)
            if total_gral != sumas:
                advertencias.append(
                    f"El TOTAL GRAL impreso {total_gral} no coincide con la suma de las filas {sumas}. "
                    "En los reportes de activadas, VISOC suma además el reporte de solicitadas.")
        return Lectura(self.codigo, parametros, fecha, filas, pie, advertencias)

    def validar(self, lectura: Lectura) -> Validacion:
        validacion = Validacion([Chequeo("filas_leidas", bool(lectura.filas), f"{len(lectura.filas)} filas")])
        categorias = [lectura.totales_declarados.get(c) for c in CATEGORIAS]
        if any(c is None for c in categorias):
            validacion.chequeos.append(Chequeo("pie_presente", False, "Falta alguna de las 4 categorías del pie"))
            return validacion
        validacion.chequeos.append(Chequeo("pie_presente", True, "Están las 4 categorías del pie"))
        for i, metrica in enumerate(METRICAS):
            leido = sum(f[metrica] for f in lectura.filas)
            impreso = sum(c[i] for c in categorias)
            validacion.chequeos.append(
                Chequeo(f"suma_{metrica}", leido == impreso, f"filas {leido} · pie {impreso}"))
        return validacion

    def mapear(self, lectura: Lectura, sesion, importacion) -> None:
        p = lectura.parametros
        desde = date.fromisoformat(p["periodo_desde"]) if p.get("periodo_desde") else None
        hasta = date.fromisoformat(p["periodo_hasta"]) if p.get("periodo_hasta") else None
        for fila in lectura.filas:
            organizacion = obtener_o_crear_organizacion(sesion, fila["nombre"], origen=self.codigo)
            for metrica in METRICAS:
                sesion.add(MedidaOrganizacion(
                    importacion_id=importacion.id, cuit=organizacion.cuit, consulta=p["consulta"],
                    metrica=metrica, valor=fila[metrica], periodo_desde=desde, periodo_hasta=hasta))
        for etiqueta, codigo in _CODIGO_TIPO_SOLICITANTE.items():
            valores = lectura.totales_declarados.get(etiqueta)
            if valores is None:
                continue
            for metrica, valor in zip(METRICAS, valores):
                sesion.add(MedidaCategoria(
                    importacion_id=importacion.id, tipo_solicitante=codigo, consulta=p["consulta"],
                    metrica=metrica, valor=valor, periodo_desde=desde, periodo_hasta=hasta))
        sesion.flush()
