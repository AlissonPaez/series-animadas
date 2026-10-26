# Esta clase crea la colección en Weaviate y sube las series del csv filtrado
# Se puede ejecutar varias veces, si la colección ya existe, la borra y la vuelve a crear

import pandas as pd
from weaviate.classes.config import Configure, DataType, Property
from weaviate.util import generate_uuid5

from src.cliente import obtener_cliente
from src.config import ARCHIVO_CSV, NOMBRE_COLECCION

COLUMNAS = [
    "title", "overview", "genres", "year", "original_language",
    "seasons", "episodes", "rating", "votes", "poster_path",
]


def leer_csv():
    df = pd.read_csv(ARCHIVO_CSV)[COLUMNAS]  # ignora columnas extra que no sirven aquí
    df["overview"] = df["overview"].fillna("")
    df["genres"] = df["genres"].fillna("")
    df["poster_path"] = df["poster_path"].fillna("")
    df["original_language"] = df["original_language"].fillna("")
    for columna in ["year", "seasons", "episodes", "votes"]:
        df[columna] = df[columna].fillna(0).astype(int)
    df["rating"] = df["rating"].fillna(0).astype(float)
    return df


def crear_coleccion(client):
    if client.collections.exists(NOMBRE_COLECCION):
        print(f"La colección {NOMBRE_COLECCION} ya existía: se borra y se vuelve a crear.")
        client.collections.delete(NOMBRE_COLECCION)

    return client.collections.create(
        name=NOMBRE_COLECCION,
        properties=[
            Property(name="title", data_type=DataType.TEXT),
            Property(name="overview", data_type=DataType.TEXT),
            Property(name="genres", data_type=DataType.TEXT),
            Property(name="year", data_type=DataType.INT),
            Property(name="original_language", data_type=DataType.TEXT),
            Property(name="seasons", data_type=DataType.INT),
            Property(name="episodes", data_type=DataType.INT),
            Property(name="rating", data_type=DataType.NUMBER),
            Property(name="votes", data_type=DataType.INT),
            Property(name="poster_path", data_type=DataType.TEXT),
        ],
        # Weaviate genera los vectores ya que tiene su propio servicio de embeddings.
        # Solo se vectoriza el texto que describe la serie.
        vector_config=Configure.Vectors.text2vec_weaviate(
            name="default",
            source_properties=["title", "overview", "genres"],
        ),
    )


def main():
    df = leer_csv()
    print(f"Series a subir: {len(df)}")

    client = obtener_cliente()
    try:
        series = crear_coleccion(client)

        with series.batch.fixed_size(batch_size=100) as batch:
            for fila in df.to_dict("records"):
                batch.add_object(
                    properties=fila,
                    uuid=generate_uuid5(f"{fila['title']}-{fila['year']}"),
                )
                if batch.number_errors > 10:
                    print("Se detuvo la carga: demasiados errores.")
                    break

        fallidos = series.batch.failed_objects
        if fallidos:
            print(f"Objetos con error: {len(fallidos)}")
            print("Primer error:", fallidos[0].message)

        total = series.aggregate.over_all(total_count=True).total_count
        print(f"Series guardadas en Weaviate: {total}")
    finally:
        client.close()


if __name__ == "__main__":
    main()