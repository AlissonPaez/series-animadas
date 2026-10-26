# Son las funciones de búsqueda sobre la colección de series en Weaviate.
# todas reciben un `client` ya conectado (src/cliente.py) y devuelven
# una lista de diccionarios fáciles de mostrar en la interfaz.

from weaviate.classes.query import Filter, MetadataQuery, Sort
from weaviate.util import generate_uuid5

from src.config import NOMBRE_COLECCION

URL_POSTER = "https://image.tmdb.org/t/p/w342"


def _coleccion(client):
    return client.collections.get(NOMBRE_COLECCION)


def _filtros(anio_desde=None, anio_hasta=None, rating_min=None):
    """Combina los filtros numéricos que el usuario haya activado."""
    filtros = []
    if anio_desde:
        filtros.append(Filter.by_property("year").greater_or_equal(anio_desde))
    if anio_hasta:
        filtros.append(Filter.by_property("year").less_or_equal(anio_hasta))
    if rating_min:
        filtros.append(Filter.by_property("rating").greater_or_equal(rating_min))

    if not filtros:
        return None
    combinado = filtros[0]
    for f in filtros[1:]:
        combinado = combinado & f
    return combinado


def _formatear(objetos, campo_metrica):
    """Convierte los objetos de Weaviate en diccionarios simples."""
    resultados = []
    for obj in objetos:
        p = obj.properties
        metrica = getattr(obj.metadata, campo_metrica, None)
        resultados.append({
            "title": p["title"],
            "year": p["year"],
            "genres": p["genres"],
            "overview": p["overview"],
            "rating": p["rating"],
            "votes": p["votes"],
            "seasons": p["seasons"],
            "episodes": p["episodes"],
            "poster": URL_POSTER + p["poster_path"] if p["poster_path"] else None,
            "metrica": metrica,
        })
    return resultados


def buscar_semantica(client, consulta, limite=5, offset=0, **filtros):
    """Busca por significado. La métrica es la distancia (más baja = más parecido)."""
    respuesta = _coleccion(client).query.near_text(
        query=consulta,
        limit=limite,
        offset=offset,
        filters=_filtros(**filtros),
        return_metadata=MetadataQuery(distance=True),
    )
    return _formatear(respuesta.objects, "distance")


def buscar_hibrida(client, consulta, limite=5, alpha=0.5, offset=0, **filtros):
    """Mezcla significado y palabras clave.

    alpha=1 es solo vectorial, alpha=0 es solo palabras clave (BM25).
    La métrica es un puntaje (más alto = más parecido).
    """
    respuesta = _coleccion(client).query.hybrid(
        query=consulta,
        alpha=alpha,
        limit=limite,
        offset=offset,
        filters=_filtros(**filtros),
        return_metadata=MetadataQuery(score=True),
    )
    return _formatear(respuesta.objects, "score")


def buscar_palabras_clave(client, consulta, limite=5, offset=0, **filtros):
    """Búsqueda tradicional por palabras exactas (BM25), para comparar."""
    respuesta = _coleccion(client).query.bm25(
        query=consulta,
        limit=limite,
        offset=offset,
        filters=_filtros(**filtros),
        return_metadata=MetadataQuery(score=True),
    )
    return _formatear(respuesta.objects, "score")


def series_similares(client, titulo, anio, limite=5):
    """Recomienda series parecidas a una que ya existe en la colección."""
    uuid = generate_uuid5(f"{titulo}-{anio}")
    respuesta = _coleccion(client).query.near_object(
        near_object=uuid,
        limit=limite + 1,  # la primera coincidencia es la propia serie
        return_metadata=MetadataQuery(distance=True),
    )
    resultados = _formatear(respuesta.objects, "distance")
    return [r for r in resultados if not (r["title"] == titulo and r["year"] == anio)][:limite]


def series_populares(client, limite=10, offset=0, **filtros):
    """Las series con más votos (no es una búsqueda: solo ordena por una propiedad)."""
    respuesta = _coleccion(client).query.fetch_objects(
        limit=limite,
        offset=offset,
        filters=_filtros(**filtros),
        sort=Sort.by_property(name="votes", ascending=False),
    )
    return _formatear(respuesta.objects, "distance")