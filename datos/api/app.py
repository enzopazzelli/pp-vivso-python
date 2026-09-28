"""La app FastAPI: arma las rutas y migra la base propia al arrancar."""
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Deja la base propia con el esquema al día, igual que hace la línea de comandos (Plan 1)."""
    from datos.sesion import migrar
    migrar()
    yield


app = FastAPI(title="Capa de datos VIVSO", description="API de solo lectura sobre los reportes importados.",
             lifespan=_lifespan)

from datos.api.colecciones import router as router_colecciones
from datos.api.importar import router as router_importar
from datos.api.indicadores import router as router_indicadores
from datos.api.reportes import router as router_reportes

app.include_router(router_colecciones)
app.include_router(router_indicadores)
app.include_router(router_reportes)
app.include_router(router_importar)


@app.get("/")
def salud() -> dict:
    return {"estado": "ok"}
