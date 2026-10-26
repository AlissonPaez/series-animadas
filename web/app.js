"use strict";

const LIMITE = 10;

const GENEROS = {
  "Animation": "Animación",
  "Action & Adventure": "Acción y aventura",
  "Comedy": "Comedia",
  "Drama": "Drama",
  "Sci-Fi & Fantasy": "Ciencia ficción y fantasía",
  "Kids": "Infantil",
  "Family": "Familia",
  "Mystery": "Misterio",
  "Crime": "Crimen",
  "War & Politics": "Guerra y política",
  "Documentary": "Documental",
  "Reality": "Reality",
  "Soap": "Telenovela",
  "Talk": "Entrevistas",
  "News": "Noticias",
  "Western": "Western",
};

const estado = { consulta: "", offset: 0, peticion: 0 };

const $ = (id) => document.getElementById(id);

function crear(etiqueta, clase, texto) {
  const nodo = document.createElement(etiqueta);
  if (clase) nodo.className = clase;
  if (texto !== undefined) nodo.textContent = texto;
  return nodo;
}

function traducirGenero(genero) {
  return GENEROS[genero] || genero;
}

function filtrosActuales() {
  const filtros = {};
  const desde = $("anio-desde").value.trim();
  const hasta = $("anio-hasta").value.trim();
  const rating = Number($("rating-min").value);
  if (desde) filtros.anio_desde = desde;
  if (hasta) filtros.anio_hasta = hasta;
  if (rating > 0) filtros.rating_min = rating;
  return filtros;
}

async function pedir(ruta, parametros) {
  const respuesta = await fetch(`${ruta}?${new URLSearchParams(parametros)}`);
  if (!respuesta.ok) throw new Error(`Error ${respuesta.status}`);
  return respuesta.json();
}

function mostrarMensaje(texto, tipo) {
  const nodo = $("estado");
  nodo.textContent = texto;
  nodo.className = tipo ? `estado estado--${tipo}` : "estado";
}

function textoMeta(serie) {
  const partes = [];
  if (serie.rating > 0) partes.push(`⭐ ${serie.rating.toFixed(1)}`);
  if (serie.seasons > 0) {
    partes.push(`${serie.seasons} ${serie.seasons === 1 ? "temporada" : "temporadas"}`);
  }
  if (serie.episodes > 0) partes.push(`${serie.episodes} episodios`);
  return partes.join(" · ");
}

function crearTarjeta(serie, conSimilares) {
  const tarjeta = crear("article", "tarjeta");

  const poster = crear("div", "tarjeta__poster");
  if (serie.poster) {
    const imagen = document.createElement("img");
    imagen.src = serie.poster;
    imagen.alt = `Póster de ${serie.title}`;
    imagen.loading = "lazy";
    imagen.addEventListener("error", () => {
      imagen.remove();
      poster.textContent = "🎬";
    });
    poster.appendChild(imagen);
  } else {
    poster.textContent = "🎬";
  }
  tarjeta.appendChild(poster);

  const info = crear("div", "tarjeta__info");
  const anio = serie.year ? serie.year : "s/f";
  info.appendChild(crear("h3", "tarjeta__titulo", `${serie.title} (${anio})`));

  const meta = textoMeta(serie);
  if (meta) info.appendChild(crear("p", "tarjeta__meta", meta));

  const generos = serie.genres
    .split(",")
    .map((g) => g.trim())
    .filter((g) => g && g !== "Animation");
  if (generos.length) {
    const lista = crear("div", "chips");
    generos.forEach((g) => lista.appendChild(crear("span", "chip", traducirGenero(g))));
    info.appendChild(lista);
  }

  const sinopsis = crear("p", "tarjeta__sinopsis", serie.overview);
  sinopsis.title = "Clic para ver la sinopsis completa";
  sinopsis.addEventListener("click", () => sinopsis.classList.toggle("tarjeta__sinopsis--abierta"));
  info.appendChild(sinopsis);

  if (conSimilares) {
    const boton = crear("button", "boton boton--suave", "Ver series parecidas");
    boton.type = "button";
    boton.addEventListener("click", () => abrirSimilares(serie));
    info.appendChild(boton);
  }

  tarjeta.appendChild(info);
  return tarjeta;
}

function actualizarTitulo() {
  if (estado.consulta) {
    $("titulo-seccion").textContent = `Resultados para “${estado.consulta}”`;
    $("limpiar").hidden = false;
  } else {
    $("titulo-seccion").textContent = "Series más populares";
    $("limpiar").hidden = true;
  }
}

async function cargar(reiniciar) {
  const filtros = filtrosActuales();
  if (filtros.anio_desde && filtros.anio_hasta && Number(filtros.anio_desde) > Number(filtros.anio_hasta)) {
    mostrarMensaje("El año inicial no puede ser mayor que el año final.", "error");
    return;
  }

  const miPeticion = ++estado.peticion;
  if (reiniciar) {
    estado.offset = 0;
    $("resultados").replaceChildren();
    $("ver-mas").hidden = true;
  }
  actualizarTitulo();
  mostrarMensaje("Buscando series…");
  $("ver-mas").disabled = true;

  const parametros = { limite: LIMITE, offset: estado.offset, ...filtros };
  let ruta = "/api/populares";
  if (estado.consulta) {
    ruta = "/api/buscar";
    parametros.q = estado.consulta;
  }

  try {
    const datos = await pedir(ruta, parametros);
    if (miPeticion !== estado.peticion) return;

    datos.resultados.forEach((serie) => $("resultados").appendChild(crearTarjeta(serie, true)));
    if ($("resultados").children.length === 0) {
      mostrarMensaje("No encontramos series con esa búsqueda y esos filtros. Prueba con otras palabras o amplía los filtros.");
    } else {
      mostrarMensaje("");
    }
    $("ver-mas").hidden = !datos.hay_mas;
  } catch (error) {
    if (miPeticion !== estado.peticion) return;
    if (!reiniciar) estado.offset -= LIMITE;
    mostrarMensaje("No pudimos conectar con el servidor. Revisa que la API esté encendida e inténtalo de nuevo.", "error");
  } finally {
    if (miPeticion === estado.peticion) $("ver-mas").disabled = false;
  }
}

async function abrirSimilares(serie) {
  $("modal-titulo").textContent = `Series parecidas a ${serie.title}`;
  $("modal-resultados").replaceChildren();
  $("modal-estado").textContent = "Buscando series parecidas…";
  $("modal").showModal();

  try {
    const datos = await pedir("/api/similares", { titulo: serie.title, anio: serie.year, limite: 6 });
    datos.resultados.forEach((s) => $("modal-resultados").appendChild(crearTarjeta(s, false)));
    $("modal-estado").textContent = datos.resultados.length ? "" : "No encontramos series parecidas.";
  } catch (error) {
    $("modal-estado").textContent = "No pudimos cargar las series parecidas.";
  }
}

// ---------- Eventos ----------
$("form-busqueda").addEventListener("submit", (evento) => {
  evento.preventDefault();
  estado.consulta = $("consulta").value.trim();
  cargar(true);
});

["anio-desde", "anio-hasta", "rating-min"].forEach((id) => {
  $(id).addEventListener("change", () => cargar(true));
});

$("limpiar").addEventListener("click", () => {
  $("consulta").value = "";
  estado.consulta = "";
  cargar(true);
});

$("ver-mas").addEventListener("click", () => {
  estado.offset += LIMITE;
  cargar(false);
});

$("modal-cerrar").addEventListener("click", () => $("modal").close());
$("modal").addEventListener("click", (evento) => {
  if (evento.target === $("modal")) $("modal").close();  
});

cargar(true);