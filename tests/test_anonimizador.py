import pytest

from datos.anonimizador import Anonimizador, limpiar_dni, normalizar_persona
from datos.config import ConfiguracionFaltante, anon_secret


def test_normalizar_persona_ignora_tildes_mayusculas_y_puntuacion():
    assert normalizar_persona("  María  José PÉREZ-gómez. ") == "MARIA JOSE PEREZ GOMEZ"


def test_la_misma_persona_escrita_distinto_recibe_el_mismo_seudonimo(anon):
    assert anon("Zzyzx Qwertyuiop") == anon("  ZZYZX   qwertyuiop ")


def test_el_seudonimo_no_contiene_el_nombre_real(anon):
    seudonimo = anon("Zzyzx Qwertyuiop").lower()
    assert "zzyzx" not in seudonimo and "qwertyuiop" not in seudonimo


def test_personas_distintas_reciben_seudonimos_distintos(anon):
    assert anon("Zzyzx Qwertyuiop") != anon("Wwxyz Asdfghjkl")


def test_otra_clave_da_otro_seudonimo(secreto):
    a = Anonimizador(secreto)("Zzyzx Qwertyuiop")
    b = Anonimizador("otra-clave-distinta-de-32-caracteres!")("Zzyzx Qwertyuiop")
    assert a != b


def test_un_nombre_vacio_da_vacio(anon):
    assert anon("") == "" and anon("   ") == ""


def test_una_clave_corta_se_rechaza():
    with pytest.raises(ValueError):
        Anonimizador("corta")


def test_limpiar_dni_tapa_numeros_de_7_u_8_cifras():
    assert limpiar_dni("titular DNI 12.345.678 vive") == "titular DNI [DNI] vive"
    assert limpiar_dni("nro 1234567") == "nro [DNI]"
    assert limpiar_dni("plazo 90 dias") == "plazo 90 dias"


def test_falta_la_clave_de_anonimizacion(monkeypatch):
    monkeypatch.delenv("ANON_SECRET", raising=False)
    with pytest.raises(ConfiguracionFaltante) as error:
        anon_secret()
    assert "ANON_SECRET" in str(error.value)


def test_la_clave_se_lee_del_entorno(monkeypatch):
    monkeypatch.setenv("ANON_SECRET", "x" * 32)
    assert anon_secret() == "x" * 32
