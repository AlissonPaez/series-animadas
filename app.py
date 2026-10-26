"""Interfaz del buscador de series animadas (Streamlit).

Ejecutar desde la carpeta principal:  streamlit run app.py
"""
import streamlit as st

from src.busqueda import (
    buscar_hibrida,
    buscar_palabras_clave,
    buscar_semantica,
    series_similares,
)
from src.cliente import obtener_cliente

st.set_page_config(page_title="Buscador de series animadas", page_icon="🎬", layout="wide")


@st.cache_resource
def get_client():
    """Una sola conexión a Weaviate compartida mientras la app esté abierta."""
    return obtener_cliente()


def elegir_similares(titulo, anio):
    st.session_state["similares_de"] = (titulo, anio)


def cerrar_similares():
    st.session_state["similares_de"] = None


def mostrar_serie(serie, clave, etiqueta_metrica, permitir_similares=True):
    col_img, col_info = st.columns([1, 5])
    with col_img:
        if serie["poster"]:
            st.image(serie["poster"], width=110)
    with col_info:
        anio = serie["year"] if serie["year"] else "s/f"
        st.subheader(f"{serie['title']} ({anio})")
        st.caption(
            f"{serie['genres']} · ⭐ {serie['rating']:.1f} · "
            f"{serie['seasons']} temporada(s) · {serie['episodes']} episodios"
        )
        sinopsis = serie["overview"]
        st.write(sinopsis if len(sinopsis) <= 350 else sinopsis[:350] + "…")
        if serie["metrica"] is not None:
            st.caption(f"{etiqueta_metrica}: {serie['metrica']:.3f}")
        if permitir_similares:
            st.button(
                "Ver series similares",
                key=clave,
                on_click=elegir_similares,
                args=(serie["title"], serie["year"]),
            )


# ---------- Barra lateral: opciones y filtros ----------
with st.sidebar:
    st.header("Opciones")
    modo = st.radio(
        "Tipo de búsqueda",
        ["Semántica", "Híbrida", "Palabras clave", "Comparar las tres"],
    )
    limite = st.slider("Cantidad de resultados", 3, 12, 6)

    alpha = 0.5
    if modo == "Híbrida":
        alpha = st.slider(
            "Peso del significado (alpha)", 0.0, 1.0, 0.5, 0.1,
            help="1 = solo significado (vectorial), 0 = solo palabras clave.",
        )

    st.subheader("Filtros")
    anio_desde, anio_hasta = None, None
    if st.checkbox("Filtrar por año de estreno"):
        anio_desde, anio_hasta = st.slider("Años", 1950, 2026, (2000, 2026))
    rating_min = st.slider("Puntuación mínima", 0.0, 10.0, 0.0, 0.5)

filtros = {
    "anio_desde": anio_desde,
    "anio_hasta": anio_hasta,
    "rating_min": rating_min or None,
}

# ---------- Pantalla principal ----------
st.title("🎬 Buscador semántico de series animadas")
st.caption(
    "Describe la trama con tus propias palabras. La búsqueda compara significados "
    "usando una base de datos vectorial (Weaviate), no solo palabras exactas."
)

try:
    client = get_client()

    # Sección de series similares (si se pidió)
    similares = st.session_state.get("similares_de")
    if similares:
        titulo, anio = similares
        st.info(f"Series parecidas a **{titulo}**")
        for i, serie in enumerate(series_similares(client, titulo, anio, limite)):
            mostrar_serie(serie, f"sim-{i}", "Distancia", permitir_similares=False)
        st.button("Cerrar series similares", on_click=cerrar_similares)
        st.divider()

    consulta = st.text_input(
        "¿Qué serie quieres encontrar?",
        placeholder="Ej.: un joven que sueña con ser el mejor ninja",
    )

    if consulta:
        if modo == "Comparar las tres":
            columnas = st.columns(3)
            tipos = [
                ("Semántica", buscar_semantica, "distancia"),
                ("Híbrida", buscar_hibrida, "puntaje"),
                ("Palabras clave", buscar_palabras_clave, "puntaje"),
            ]
            for col, (nombre, funcion, etiqueta) in zip(columnas, tipos):
                with col:
                    st.subheader(nombre)
                    resultados = funcion(client, consulta, limite=limite, **filtros)
                    if not resultados:
                        st.write("Sin resultados.")
                    for r in resultados:
                        st.markdown(f"**{r['title']}** ({r['year']})")
                        st.caption(f"{etiqueta}: {r['metrica']:.3f}")
        else:
            if modo == "Semántica":
                resultados = buscar_semantica(client, consulta, limite=limite, **filtros)
                etiqueta = "Distancia (más baja = más parecido)"
            elif modo == "Híbrida":
                resultados = buscar_hibrida(client, consulta, limite=limite, alpha=alpha, **filtros)
                etiqueta = "Puntaje (más alto = más parecido)"
            else:
                resultados = buscar_palabras_clave(client, consulta, limite=limite, **filtros)
                etiqueta = "Puntaje (más alto = más parecido)"

            if not resultados:
                st.warning("No se encontraron series con esa búsqueda y esos filtros.")
            for i, serie in enumerate(resultados):
                mostrar_serie(serie, f"res-{i}", etiqueta)
                st.divider()

except Exception as error:
    st.error(f"Ocurrió un problema al hablar con Weaviate: {error}")