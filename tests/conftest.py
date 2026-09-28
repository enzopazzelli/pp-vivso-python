"""Configuración común de las pruebas."""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

# Archivos reales del área: contienen datos sensibles y no se versionan.
REALES = {
    "lugones": RAIZ.parent / "lugones.pdf",
    "solicitadas": RAIZ / "informe_ong_og_2026" / "datos_fuente" / "visoc_solicitadas_por_solicitante.pdf",
    "activadas": RAIZ / "informe_ong_og_2026" / "datos_fuente" / "visoc_activadas_por_solicitante.pdf",
    "finalizadas": RAIZ / "informe_ong_og_2026" / "datos_fuente" / "visoc_finalizadas_por_solicitante.pdf",
}


@pytest.fixture
def real():
    """Devuelve la ruta de un archivo real, o salta la prueba si no está en esta máquina."""
    def _ruta(nombre):
        ruta = REALES[nombre]
        if not ruta.exists():
            pytest.skip(f"No está el archivo real «{nombre}» (datos del área, no versionados)")
        return ruta
    return _ruta


@pytest.fixture
def secreto():
    return "clave-de-prueba-de-al-menos-32-caracteres"


@pytest.fixture
def anon(secreto):
    from datos.anonimizador import Anonimizador
    return Anonimizador(secreto)


@pytest.fixture
def sesion():
    """Sesión sobre una base en memoria, con las tablas y los catálogos ya creados."""
    from sqlalchemy.orm import Session
    from datos.sesion import crear_engine, crear_tablas, sembrar_catalogos

    engine = crear_engine("sqlite:///:memory:")
    crear_tablas(engine)
    with Session(engine) as s:
        sembrar_catalogos(s)
        yield s
