"""Configuración de la capa de datos: dónde vive la base real y la clave de anonimización."""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")


class ConfiguracionFaltante(RuntimeError):
    """Falta algo que hay que configurar en el entorno (por ejemplo, en .env)."""


def db_url() -> str:
    """Base real: un archivo SQLite propio, separado de los datos simulados."""
    predeterminada = f"sqlite:///{(RAIZ / 'db' / 'datos_reales.db').as_posix()}"
    return os.getenv("DATOS_DB_URL", predeterminada)


def anon_secret() -> str:
    """Clave con la que se generan los seudónimos. Sin ella no se puede importar."""
    secreto = os.getenv("ANON_SECRET", "")
    if len(secreto) < 16:
        raise ConfiguracionFaltante(
            "Falta ANON_SECRET en el archivo .env (mínimo 16 caracteres). "
            'Generá una con: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    return secreto
