# Buscador semántico de series animadas

> **Electiva I — Bases de Datos Modernas**  
> **Tema:** Bases de datos vectoriales   

Es una plicación web que permite encontrar series animadas escribiendo su título o
**describiendo su trama**, por ejemplo:
*«un científico loco que viaja a otras dimensiones con su nieto»*.

Está construida sobre **Weaviate**, una base de datos vectorial. En lugar de
buscar solo palabras exactas, compara el *significado* de la consulta con el de
las sinopsis de 1000 series.


## Cómo funciona

1. **Datos.** Se comienza con un dataset de series de TMDB (Kaggle). Del cual se filtran las
   series animadas más votadas (en este caso se dejaron 1000) y sus sinopsis se descargan en español
   desde la API de TMDB.
2. **Carga.** Cada una de las series se guarda en una colección de Weaviate. El servicio de
   embeddings de Weaviate Cloud convierte el título, la sinopsis y los géneros
   en un vector.
3. **Búsqueda.** El buscador usa una búsqueda **híbrida**, es decir vectorial + palabras
   clave, por lo que sirve tanto para escribir un título como para describir
   una trama. Contiene filtros por año y por calificación mínima.
4. **Series parecidas.** Cada resultado tiene un botón que usa los vectores para
   recomendar series similares.

**Tecnologías:** Python, Weaviate Cloud, FastAPI, HTML, CSS y JavaScript.

## Requisitos

- Python 3.10 o superior
- Una cuenta gratuita en [Weaviate Cloud](https://console.weaviate.cloud/)

## Instalación y uso

### 1. Clonar e instalar

```bash
git clone <URL-del-repositorio>
cd series-animadas
python -m venv venv
```

Activar el entorno virtual:

- Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
- macOS / Linux: `source venv/bin/activate`

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

### 2. Configurar el acceso a Weaviate

Con la URL y la API key de lectura, copia la plantilla
`.env.example` como `.env` y completa los dos primeros valores:

```
WEAVIATE_URL=la-url-recibida
WEAVIATE_API_KEY=la-api-key-recibida
```
(La URL puede llevar o no el `https://`.)
No hay que cargar nada. 


### 3. Iniciar la aplicación

```bash
uvicorn api:app --reload
```

Abre <http://127.0.0.1:8000> en el navegador. La documentación interactiva de la
API está en <http://127.0.0.1:8000/docs>.


## Estructura del proyecto

```
series-animadas/
├── api.py                    # API (FastAPI) y servidor de la página web
├── requirements.txt
├── .env.example              # plantilla de credenciales
├── data/
│   └── series_animadas.csv   # 1000 series con sinopsis en español
├── scripts/
│   ├── preparar_dataset.py   # filtra el CSV grande de Kaggle
│   ├── traducir_sinopsis.py  # descarga las sinopsis en español desde TMDB
│   ├── probar_conexion.py    # comprueba la conexión con Weaviate
│   └── cargar_datos.py       # crea la colección y sube las series
├── src/
│   ├── cliente.py            # conexión a Weaviate
│   ├── config.py             # nombre de la colección y rutas
│   └── busqueda.py           # búsquedas (vectorial e hibrida)
└── web/
    ├── index.html
    ├── style.css
    └── app.js
```

## API

| Ruta | Descripción |
|------|-------------|
| `GET /api/populares` | Series con más votos. Acepta filtros. |
| `GET /api/buscar?q=...` | Búsqueda híbrida. Acepta `anio_desde`, `anio_hasta`, `rating_min`, `limite` y `offset`. |
| `GET /api/similares?titulo=...&anio=...` | Series parecidas a una ya existente. |


## Origen de los datos

- Datos y pósters: [TMDB](https://www.themoviedb.org/). Esta app usa la API
  de TMDB.
- Dataset base: *Full TMDB TV Shows Dataset* (autor: asaniczka, en Kaggle).
- Búsqueda vectorial y embeddings: [Weaviate](https://weaviate.io/).