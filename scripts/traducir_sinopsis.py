# Esta clase reemplaza las sinopsis en inglés por sinopsis en español, usando la API de TMDB.
# Se ejecuta una sola vez, dando como resultado el csv (data/series_animadas.csv) y
# es el que se sube a git, así que quien clone el proyecto NO necesita clave de TMDB.

# se usa desde la carpeta principal con python -m scripts.traducir_sinopsis
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = RAIZ / "data" / "series_animadas.csv"

URL_TMDB = "https://api.themoviedb.org/3/tv/{}"
IDIOMAS = ["es-MX", "es-ES"]   # se prueban en este orden
MIN_CARACTERES = 40            # una sinopsis más corta se considera vacía
PAUSA = 0.05                   # segundos entre consultas, para no saturar a TMDB


def pedir_sinopsis(sesion, api_key, tmdb_id, idioma):
    """Devuelve la sinopsis en ese idioma, '' si no existe o None si no se pudo consultar."""
    for intento in range(3):
        try:
            respuesta = sesion.get(
                URL_TMDB.format(tmdb_id),
                params={"api_key": api_key, "language": idioma},
                timeout=15,
            )
        except requests.RequestException:
            time.sleep(1 + intento)
            continue

        if respuesta.status_code == 200:
            return (respuesta.json().get("overview") or "").strip()
        if respuesta.status_code == 401:
            raise SystemExit("TMDB rechazó la clave (401). Revisa TMDB_API_KEY en tu archivo .env.")
        if respuesta.status_code == 404:
            return ""
        time.sleep(1 + intento)  # límite de peticiones u otro error: esperar y reintentar
    return None


def main():
    api_key = os.getenv("TMDB_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Falta TMDB_API_KEY en el archivo .env")

    df = pd.read_csv(ARCHIVO)
    if "overview_en" not in df.columns:
        df["overview_en"] = df["overview"]
        df["sinopsis_idioma"] = ""
    df["sinopsis_idioma"] = df["sinopsis_idioma"].fillna("")

    pendientes = list(df.index[df["sinopsis_idioma"] == ""])
    print(f"Series por procesar: {len(pendientes)} de {len(df)}")

    sesion = requests.Session()
    try:
        for n, i in enumerate(pendientes, start=1):
            tmdb_id = int(df.at[i, "tmdb_id"])
            for idioma in IDIOMAS:
                texto = pedir_sinopsis(sesion, api_key, tmdb_id, idioma)
                if texto is None:   # fallo de red: se deja pendiente para otra ejecución
                    break
                if len(texto) >= MIN_CARACTERES:
                    df.at[i, "overview"] = texto
                    df.at[i, "sinopsis_idioma"] = "es"
                    break
            else:                   # ninguna sinopsis en español
                df.at[i, "sinopsis_idioma"] = "en"

            if n % 100 == 0:
                print(f"  {n}/{len(pendientes)}")
            time.sleep(PAUSA)
    finally:
        df.to_csv(ARCHIVO, index=False)  # se guarda incluso si se interrumpe con Ctrl+C

    conteo = df["sinopsis_idioma"].value_counts()
    print("\nListo.")
    print("En español:", int(conteo.get("es", 0)))
    print("Se quedaron en inglés:", int(conteo.get("en", 0)))
    print("Pendientes (fallos de conexión):", int(conteo.get("", 0)))


if __name__ == "__main__":
    main()