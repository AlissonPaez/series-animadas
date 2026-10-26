# Esta clase comprueba que el proyecto se conecta bien al cluster de Weaviate Cloud
from src.cliente import obtener_cliente

client = obtener_cliente()
try:
    print("Conectado:", client.is_ready())
    print("Versión de Weaviate:", client.get_meta()["version"])
    print("Colecciones existentes:", list(client.collections.list_all().keys()))
finally:
    client.close()