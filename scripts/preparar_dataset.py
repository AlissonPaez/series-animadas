# Esta clase filtra el csv grande que se tenía con series y peliculas de TMDB y deja las series animadas más votadas.

# para usarla es desde la carpeta principal con python -m scripts.preparar_dataset

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent


ARCHIVO_ENTRADA = RAIZ / "data" / "raw" / "TMDB_tv_dataset_v3.csv"  # csv grande
ARCHIVO_SALIDA = RAIZ / "data" / "series_animadas.csv"
CANTIDAD = 1000                  # cuántas series dejar
MIN_VOTOS = 20                   # descarta series con muy pocos votos
MIN_CARACTERES_SINOPSIS = 60     # descarta sinopsis demasiado cortas


COLUMNAS = [
    "id", "name", "overview", "genres", "first_air_date", "original_language",
    "number_of_seasons", "number_of_episodes", "vote_average", "vote_count",
    "popularity", "adult", "poster_path",
]

df = pd.read_csv(ARCHIVO_ENTRADA, usecols=COLUMNAS)
print("Series en el CSV original:", len(df))

# 1. Solo animadas
df = df[df["genres"].fillna("").str.contains("Animation", case=False)]
print("Series animadas:", len(df))

# 2. Sin contenido adulto
df = df[df["adult"].astype(str).str.lower() != "true"]

# 3. Con sinopsis útil y con votos suficientes
df["overview"] = df["overview"].fillna("").str.strip()
df = df[df["overview"].str.len() >= MIN_CARACTERES_SINOPSIS]
df = df[df["vote_count"] >= MIN_VOTOS]
print("Después de filtrar sinopsis y votos:", len(df))

# 4. Quedarse con las más votadas (series conocidas)
df = df.sort_values("vote_count", ascending=False).head(CANTIDAD)

# 5. Limpieza final
df["year"] = pd.to_datetime(df["first_air_date"], errors="coerce").dt.year.fillna(0).astype(int)
df = df.drop_duplicates(subset=["name", "year"])
df = df.rename(columns={
    "id": "tmdb_id",
    "name": "title",
    "number_of_seasons": "seasons",
    "number_of_episodes": "episodes",
    "vote_average": "rating",
    "vote_count": "votes",
})
df = df[["tmdb_id", "title", "overview", "genres", "year", "original_language",
         "seasons", "episodes", "rating", "votes", "poster_path"]]

df.to_csv(ARCHIVO_SALIDA, index=False)
print(f"\nGuardado: {ARCHIVO_SALIDA.name} con {len(df)} series")
print(df[["title", "year", "genres"]].head(10).to_string(index=False))