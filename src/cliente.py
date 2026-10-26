# Es la conexión a Weaviate Cloud, reutilizable por todo el proyecto.
import os

import weaviate
from dotenv import load_dotenv
from weaviate.classes.init import Auth

load_dotenv()  # busca el archivo .env 


def obtener_cliente():
    """Devuelve un cliente conectado. Acuérdate de cerrarlo con client.close()."""
    url = os.getenv("WEAVIATE_URL")
    api_key = os.getenv("WEAVIATE_API_KEY")

    if not url or not api_key:
        raise RuntimeError("Faltan WEAVIATE_URL o WEAVIATE_API_KEY en el archivo .env")

    # se acepta la URL con o sin https:// y con o sin "/" al final
    url = url.strip().replace("https://", "").rstrip("/")

    return weaviate.connect_to_weaviate_cloud(
        cluster_url="https://" + url,
        auth_credentials=Auth.api_key(api_key.strip()),
    )