# son valores compartidos por todo el proyecto
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

NOMBRE_COLECCION = "SerieAnimada"
ARCHIVO_CSV = RAIZ / "data" / "series_animadas.csv"