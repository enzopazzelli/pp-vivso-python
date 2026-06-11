"""
Crea las tablas en la base de datos local SQLite y siembra el catálogo de rubros AFO.
Ejecutar una sola vez, o cuando cambie el schema.

    python -m db.setup
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from db.models import Base, RubroObra

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "db/vivso_local.db")

# Catálogo oficial de rubros del AFO — suma de peso_pct = 100
# Derivado del sistema legacy VISOC (imagen docs/afo.jpeg)
RUBROS_CATALOGO = [
    {"id": 1,  "nombre": "Terreno y limpieza",                "descripcion": "Limpieza del terreno y preparación del sitio de obra",                "peso_pct": 3,  "orden": 1},
    {"id": 2,  "nombre": "Excavación e impermeabilización",   "descripcion": "Excavación de cimientos y colocación de capa aisladora",               "peso_pct": 5,  "orden": 2},
    {"id": 3,  "nombre": "Mampostería hasta dintel",          "descripcion": "Construcción de mampostería de ladrillo hasta nivel de dintel",         "peso_pct": 10, "orden": 3},
    {"id": 4,  "nombre": "Mampostería cerámico/Block",        "descripcion": "Mampostería de ladrillo cerámico o block sobre dintel",                 "peso_pct": 10, "orden": 4},
    {"id": 5,  "nombre": "Encadenado",                        "descripcion": "Encadenado de hormigón armado",                                         "peso_pct": 5,  "orden": 5},
    {"id": 6,  "nombre": "Revoque interior",                  "descripcion": "Revoque grueso y fino en paredes interiores",                           "peso_pct": 10, "orden": 6},
    {"id": 7,  "nombre": "Revoque exterior",                  "descripcion": "Revoque grueso y fino en fachada exterior",                             "peso_pct": 8,  "orden": 7},
    {"id": 8,  "nombre": "Cielorraso con aislante térmico",   "descripcion": "Colocación de cielorraso y aislación térmica",                          "peso_pct": 5,  "orden": 8},
    {"id": 9,  "nombre": "Construcción de cielorrasos",       "descripcion": "Terminación y pintura de cielorrasos",                                  "peso_pct": 4,  "orden": 9},
    {"id": 10, "nombre": "Carpintería",                       "descripcion": "Colocación de puertas, ventanas y herrería",                            "peso_pct": 10, "orden": 10},
    {"id": 11, "nombre": "Instalación de agua",               "descripcion": "Red de distribución de agua potable interior",                          "peso_pct": 7,  "orden": 11},
    {"id": 12, "nombre": "Instalación eléctrica",             "descripcion": "Instalación eléctrica completa con tablero",                            "peso_pct": 8,  "orden": 12},
    {"id": 13, "nombre": "Instalación sanitaria",             "descripcion": "Desagüe cloacal y artefactos sanitarios",                               "peso_pct": 7,  "orden": 13},
    {"id": 14, "nombre": "Revestimiento exterior",            "descripcion": "Revestimiento de fachada y terminaciones exteriores",                   "peso_pct": 5,  "orden": 14},
    {"id": 15, "nombre": "Varios",                            "descripcion": "Trabajos varios de albañilería y terminaciones finales",                 "peso_pct": 3,  "orden": 15},
]


def crear_tablas():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Base.metadata.create_all(engine)

    # Sembrar catálogo de rubros (idempotente: solo inserta si la tabla está vacía)
    with Session(engine) as session:
        if session.query(RubroObra).count() == 0:
            session.bulk_insert_mappings(RubroObra, RUBROS_CATALOGO)
            session.commit()
            print(f"  Catálogo de rubros sembrado: {len(RUBROS_CATALOGO)} rubros")
        else:
            print(f"  Catálogo de rubros ya existente, se omite siembra")

    print(f"Base de datos lista: {DB_PATH}")
    return engine


if __name__ == "__main__":
    crear_tablas()
