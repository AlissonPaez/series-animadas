"""API del buscador de series animadas (FastAPI).

Ejecutar desde la carpeta principal:   uvicorn api:app --reload
Documentación interactiva automática:  http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles

from src.busqueda import (
    buscar_hibrida,
    series_populares,
    series_similares,
)
from src.cliente import obtener_cliente
from src.config import RAIZ

MAX_RESULTADOS = 50    # pasado este punto, los resultados casi no tienen relevancia
ALPHA_BUSQUEDA = 0.7   # 1 = solo significado, 0 = solo palabras clave


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Abre una conexión a Weaviate al iniciar y la cierra al apagar."""
    app.state.client = obtener_cliente()
    yield
    app.state.client.close()


app = FastAPI(title="Buscador de series animadas", lifespan=lifespan)


def get_client(request: Request):
    return request.app.state.client


def _paginar(resultados, limite, offset, tope=None):
    """Pedimos limite+1 resultados: si llega el extra, sabemos que hay más."""
    hay_mas = len(resultados) > limite
    if tope is not None and offset + limite >= tope:
        hay_mas = False
    return {"resultados": resultados[:limite], "hay_mas": hay_mas}


@app.get("/api/populares")
def populares(
    limite: int = Query(10, ge=1, le=30),
    offset: int = Query(0, ge=0),
    anio_desde: int | None = None,
    anio_hasta: int | None = None,
    rating_min: float | None = None,
    client=Depends(get_client),
):
    """Series con más votos: la lista que se muestra al abrir la página."""
    resultados = series_populares(
        client, limite=limite + 1, offset=offset,
        anio_desde=anio_desde, anio_hasta=anio_hasta, rating_min=rating_min,
    )
    return _paginar(resultados, limite, offset)


@app.get("/api/buscar")
def buscar(
    q: str = Query(..., min_length=1),
    limite: int = Query(10, ge=1, le=30),
    offset: int = Query(0, ge=0),
    anio_desde: int | None = None,
    anio_hasta: int | None = None,
    rating_min: float | None = None,
    client=Depends(get_client),
):
    """Búsqueda principal. Por debajo es híbrida: sirve para títulos y para descripciones."""
    resultados = buscar_hibrida(
        client, q,
        limite=limite + 1, offset=offset, alpha=ALPHA_BUSQUEDA,
        anio_desde=anio_desde, anio_hasta=anio_hasta, rating_min=rating_min,
    )
    return _paginar(resultados, limite, offset, tope=MAX_RESULTADOS)


@app.get("/api/similares")
def similares(
    titulo: str,
    anio: int,
    limite: int = Query(6, ge=1, le=20),
    client=Depends(get_client),
):
    """Series parecidas a una que ya existe en la colección."""
    return {"resultados": series_similares(client, titulo, anio, limite=limite)}


# La página web (HTML/CSS/JS) vive en la carpeta web/. Va al final para que
# las rutas /api/... tengan prioridad.
CARPETA_WEB = RAIZ / "web"
if CARPETA_WEB.exists():
    app.mount("/", StaticFiles(directory=CARPETA_WEB, html=True), name="web")