import json

import pytest

from datos.importadores.base import Importador
from datos.importar import importar_archivo, main
from datos.modelo import Importacion, MedidaOrganizacion, RegistroCrudo
from db.models import Organizacion, Vivienda
from tests.fixtures_visoc import LINEAS_PS, LINEAS_V, NOMBRES_INVENTADOS


@pytest.fixture
def pdf_falso(tmp_path):
    ruta = tmp_path / "reporte.pdf"
    ruta.write_bytes(b"%PDF-falso")
    return ruta


@pytest.fixture
def leer_de_memoria(monkeypatch):
    """Hace que los lectores de PDF devuelvan líneas de ejemplo, así se prueba todo el camino sin PDF."""
    def _preparar(lineas_ps=None, lineas_v=None):
        monkeypatch.setattr("datos.importadores.visoc_por_solicitante.leer_lineas_texto",
                            lambda ruta, max_paginas=None: lineas_ps or [])
        monkeypatch.setattr("datos.importadores.visoc_viviendas.leer_lineas_tokens",
                            lambda ruta, max_paginas=None: lineas_v or [])
    return _preparar


def test_por_solicitante_de_punta_a_punta(sesion, anon, pdf_falso, leer_de_memoria):
    leer_de_memoria(lineas_ps=LINEAS_PS)
    resultado = importar_archivo(pdf_falso, sesion, anon)
    assert resultado.estado == "ok" and resultado.tipo_reporte == "visoc_por_solicitante"
    assert resultado.filas_leidas == 3 and all(c["ok"] for c in resultado.chequeos)
    assert sesion.query(MedidaOrganizacion).count() == 12
    importacion = sesion.get(Importacion, resultado.importacion_id)
    assert importacion.estado == "ok" and importacion.filas_leidas == 3 and importacion.version_importador == "1"
    assert sesion.query(RegistroCrudo).filter_by(importacion_id=importacion.id).count() == 3


def test_viviendas_de_punta_a_punta_sin_nombres_reales(sesion, anon, pdf_falso, leer_de_memoria):
    leer_de_memoria(lineas_v=LINEAS_V)
    resultado = importar_archivo(pdf_falso, sesion, anon)
    assert resultado.estado == "ok" and resultado.tipo_reporte == "visoc_viviendas_segun_solicitante"
    assert sesion.query(Vivienda).count() == 5
    crudo = json.dumps([r.datos for r in sesion.query(RegistroCrudo).all()], ensure_ascii=False).upper()
    viviendas = " ".join(v.titular_seudonimo for v in sesion.query(Vivienda).all()).upper()
    assert not any(nombre in crudo or nombre in viviendas for nombre in NOMBRES_INVENTADOS)


def test_el_mismo_archivo_dos_veces_queda_duplicado(sesion, anon, pdf_falso, leer_de_memoria):
    leer_de_memoria(lineas_ps=LINEAS_PS)
    primera = importar_archivo(pdf_falso, sesion, anon)
    segunda = importar_archivo(pdf_falso, sesion, anon)
    assert primera.estado == "ok" and segunda.estado == "duplicada"
    assert segunda.importacion_id == primera.importacion_id
    assert sesion.query(Importacion).count() == 1 and sesion.query(MedidaOrganizacion).count() == 12


def test_forzar_vuelve_a_importar(sesion, anon, pdf_falso, leer_de_memoria):
    leer_de_memoria(lineas_ps=LINEAS_PS)
    importar_archivo(pdf_falso, sesion, anon)
    forzada = importar_archivo(pdf_falso, sesion, anon, forzar=True)
    assert forzada.estado == "ok" and sesion.query(Importacion).count() == 2


def test_un_reporte_que_no_cierra_se_rechaza_sin_tocar_el_modelo(sesion, anon, pdf_falso, leer_de_memoria):
    sin_una_fila = [l for l in LINEAS_PS if "COOP.DE TRABAJO" not in l]
    leer_de_memoria(lineas_ps=sin_una_fila)
    resultado = importar_archivo(pdf_falso, sesion, anon)
    assert resultado.estado == "rechazada"
    assert any(not c["ok"] for c in resultado.chequeos)
    assert sesion.query(Organizacion).count() == 0 and sesion.query(MedidaOrganizacion).count() == 0
    assert sesion.query(RegistroCrudo).count() == 2                     # el crudo se conserva
    assert sesion.get(Importacion, resultado.importacion_id).estado == "rechazada"


def test_una_rechazada_no_bloquea_reimportar_el_archivo_corregido(sesion, anon, pdf_falso, leer_de_memoria):
    leer_de_memoria(lineas_ps=[l for l in LINEAS_PS if "COOP.DE TRABAJO" not in l])
    assert importar_archivo(pdf_falso, sesion, anon).estado == "rechazada"
    leer_de_memoria(lineas_ps=LINEAS_PS)
    assert importar_archivo(pdf_falso, sesion, anon).estado == "ok"


def test_una_advertencia_deja_el_estado_con_advertencias(sesion, anon, pdf_falso, leer_de_memoria):
    con_total_raro = ["TOTAL GRAL 99 17 4 3" if l.startswith("TOTAL GRAL") else l for l in LINEAS_PS]
    leer_de_memoria(lineas_ps=con_total_raro)
    resultado = importar_archivo(pdf_falso, sesion, anon)
    assert resultado.estado == "con_advertencias" and resultado.advertencias


def test_un_archivo_desconocido_queda_sin_importador_y_sin_texto(sesion, anon, tmp_path):
    archivo = tmp_path / "raro.txt"
    archivo.write_text("JUAN PEREZ 12345678\n", encoding="utf-8")
    resultado = importar_archivo(archivo, sesion, anon)
    assert resultado.estado == "sin_importador" and resultado.tipo_reporte is None
    importacion = sesion.get(Importacion, resultado.importacion_id)
    assert importacion.parametros["sonda"]["formato"] == ".txt"
    assert "JUAN" not in json.dumps(importacion.parametros) and "PEREZ" not in json.dumps(importacion.parametros)


def test_un_pdf_ilegible_no_rompe_la_importacion(sesion, anon, tmp_path):
    archivo = tmp_path / "roto.pdf"
    archivo.write_bytes(b"esto no es un pdf")
    assert importar_archivo(archivo, sesion, anon).estado == "sin_importador"


class ImportadorQueFalla(Importador):
    codigo = "visoc_por_solicitante"

    def reconoce(self, ruta):
        return 1.0

    def leer(self, ruta, anonimizar, opciones=None):
        from datos.importadores.visoc_por_solicitante import VisocPorSolicitante
        return VisocPorSolicitante().lectura_desde_lineas(LINEAS_PS)

    def validar(self, lectura):
        from datos.importadores.visoc_por_solicitante import VisocPorSolicitante
        return VisocPorSolicitante().validar(lectura)

    def mapear(self, lectura, sesion, importacion):
        from datos.organizaciones import obtener_o_crear_organizacion
        obtener_o_crear_organizacion(sesion, "ORGANIZACION QUE SE DESHACE", origen="prueba")
        raise RuntimeError("falla al mapear")


def test_si_falla_el_mapeo_se_deshace_todo_y_queda_registrado(sesion, anon, pdf_falso):
    resultado = importar_archivo(pdf_falso, sesion, anon, importador=ImportadorQueFalla())
    assert resultado.estado == "rechazada"
    assert sesion.query(Organizacion).count() == 0
    assert "nombres_organizacion" not in sesion.info
    importacion = sesion.get(Importacion, resultado.importacion_id)
    assert importacion.estado == "rechazada" and "falla al mapear" in importacion.validacion["error"]
    assert sesion.query(RegistroCrudo).filter_by(importacion_id=importacion.id).count() == 3


def test_la_linea_de_comandos_avisa_si_falta_la_clave(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("ANON_SECRET", raising=False)
    archivo = tmp_path / "x.txt"
    archivo.write_text("hola", encoding="utf-8")
    assert main([str(archivo)]) == 3
    assert "ANON_SECRET" in capsys.readouterr().out


def test_la_linea_de_comandos_informa_un_formato_desconocido(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    monkeypatch.setenv("DATOS_DB_URL", f"sqlite:///{(tmp_path / 'datos.db').as_posix()}")
    archivo = tmp_path / "raro.txt"
    archivo.write_text("hola", encoding="utf-8")
    assert main([str(archivo)]) == 2
    assert "sin_importador" in capsys.readouterr().out


def test_real_importacion_completa(real, sesion, anon):
    esperado = {"solicitadas": "ok", "activadas": "con_advertencias", "finalizadas": "ok"}
    for nombre, estado in esperado.items():
        assert importar_archivo(real(nombre), sesion, anon).estado == estado, nombre
    assert sesion.query(MedidaOrganizacion).count() == (715 + 704 + 685) * 4
    lugones = importar_archivo(real("lugones"), sesion, anon)
    # con aviso: 64 de 107 filas comparten número de expediente con otra
    assert lugones.estado == "con_advertencias" and sesion.query(Vivienda).count() == 107


# --- Correcciones tras la revisión final ------------------------------------------------------------

def test_el_nombre_de_un_archivo_no_reconocido_no_se_guarda(sesion, anon, tmp_path):
    archivo = tmp_path / "reclamo_JUANA_INVENTADA_PEREZ.txt"
    archivo.write_text("hola\n", encoding="utf-8")
    resultado = importar_archivo(archivo, sesion, anon)
    guardado = sesion.get(Importacion, resultado.importacion_id).archivo_nombre
    assert "JUANA" not in guardado.upper() and "PEREZ" not in guardado.upper() and guardado.endswith(".txt")


class ImportadorQueNoPuedeLeer(Importador):
    codigo = "visoc_por_solicitante"

    def reconoce(self, ruta):
        return 1.0

    def leer(self, ruta, anonimizar, opciones=None):
        raise ValueError("valor inesperado 'JUANA INVENTADA PEREZ' en la columna dormitorios")

    def validar(self, lectura):
        raise NotImplementedError

    def mapear(self, lectura, sesion, importacion):
        raise NotImplementedError


def test_si_falla_la_lectura_queda_registrado_sin_texto_del_archivo(sesion, anon, pdf_falso):
    resultado = importar_archivo(pdf_falso, sesion, anon, importador=ImportadorQueNoPuedeLeer())
    assert resultado.estado == "rechazada" and resultado.filas_leidas == 0
    importacion = sesion.get(Importacion, resultado.importacion_id)
    volcado = (json.dumps(importacion.validacion) + " ".join(resultado.advertencias)).upper()
    assert "VALUEERROR" in volcado and "JUANA" not in volcado and "PEREZ" not in volcado


def test_la_linea_de_comandos_crea_el_esquema_con_migraciones(monkeypatch, tmp_path):
    from sqlalchemy import create_engine, inspect
    url = f"sqlite:///{(tmp_path / 'datos.db').as_posix()}"
    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    monkeypatch.setenv("DATOS_DB_URL", url)
    archivo = tmp_path / "raro.txt"
    archivo.write_text("hola", encoding="utf-8")
    main([str(archivo)])
    assert "alembic_version" in inspect(create_engine(url)).get_table_names()
