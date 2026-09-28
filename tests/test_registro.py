from datetime import date

from datos.importadores.base import Chequeo, Importador, Validacion, fecha_corta
from datos.importadores.registro import elegir, sonda


class ImportadorFalso(Importador):
    codigo = "falso"

    def __init__(self, confianza):
        self.confianza = confianza

    def reconoce(self, ruta):
        return self.confianza

    def leer(self, ruta, anonimizar, opciones=None):
        raise NotImplementedError

    def validar(self, lectura):
        raise NotImplementedError

    def mapear(self, lectura, sesion, importacion):
        raise NotImplementedError


def test_fecha_corta_lee_dd_mm_aa():
    assert fecha_corta("31/10/25") == date(2025, 10, 31)


def test_la_validacion_es_ok_solo_si_todos_los_chequeos_lo_son():
    assert Validacion([Chequeo("a", True), Chequeo("b", True)]).ok
    assert not Validacion([Chequeo("a", True), Chequeo("b", False, "no cierra")]).ok


def test_elegir_usa_el_importador_mas_seguro(tmp_path):
    archivo = tmp_path / "x.pdf"
    archivo.write_bytes(b"x")
    elegido = elegir(archivo, candidatos=[ImportadorFalso(0.7), ImportadorFalso(0.95)])
    assert elegido.confianza == 0.95


def test_elegir_devuelve_none_si_ninguno_llega_al_minimo(tmp_path):
    archivo = tmp_path / "x.pdf"
    archivo.write_bytes(b"x")
    assert elegir(archivo, candidatos=[ImportadorFalso(0.3), ImportadorFalso(0.59)]) is None


def test_la_sonda_describe_la_forma_sin_mostrar_texto(tmp_path):
    archivo = tmp_path / "raro.txt"
    archivo.write_text("JUAN PEREZ 12345678\notra linea\n", encoding="utf-8")
    descripcion = sonda(archivo)
    assert descripcion["formato"] == ".txt" and descripcion["lineas"] == 2
    assert descripcion["forma"][0] == "xxxx xxxxx 99999999"
    assert "JUAN" not in str(descripcion) and "PEREZ" not in str(descripcion)


def test_la_sonda_no_falla_con_un_pdf_ilegible(tmp_path):
    archivo = tmp_path / "roto.pdf"
    archivo.write_bytes(b"esto no es un pdf")
    descripcion = sonda(archivo)
    assert descripcion["formato"] == ".pdf" and "error" in descripcion


def test_la_sonda_avisa_si_no_sabe_leer_el_formato(tmp_path):
    archivo = tmp_path / "datos.xlsx"
    archivo.write_bytes(b"x")
    assert "mensaje" in sonda(archivo)
