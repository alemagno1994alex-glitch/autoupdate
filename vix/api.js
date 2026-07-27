// ============================================================
//  Nova — API (TMDB metadati + estrazione stream)
// ============================================================
import {
  PROXY, SOURCE, SOURCE_REFERER,
  TMDB_KEY, TMDB_BASE, TMDB_IMG, LANG, REGION, AVAIL_TTL,
} from "./config.js";

// ---------- Proxy helper ----------
export function proxied(url, referer) {
  if (!url) return url;
  if (url.startsWith("data:") || url.startsWith("blob:")) return url;
  if (url.startsWith(PROXY)) return url;
  let out = PROXY + encodeURIComponent(url);
  if (referer) out += "&referer=" + encodeURIComponent(referer);
  return out;
}

// ---------- TMDB ----------
async function tmdb(path, params = {}) {
  const u = new URL(TMDB_BASE + path);
  u.searchParams.set("api_key", TMDB_KEY);
  u.searchParams.set("language", LANG);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") u.searchParams.set(k, v);
  }
  const r = await fetch(u);
  if (!r.ok) throw new Error("TMDB " + r.status);
  return r.json();
}

export function img(path, size = "w500") {
  return path ? `${TMDB_IMG}/${size}${path}` : null;
}

// Righe home
export const getTrending = (win = "week") =>
  tmdb(`/trending/all/${win}`).then((d) => d.results);
export const getPopularMovies = (page = 1) =>
  tmdb("/movie/popular", { page, region: REGION }).then((d) => d.results);
export const getPopularTV = (page = 1) =>
  tmdb("/tv/popular", { page }).then((d) => d.results);
export const getNowPlaying = (page = 1) =>
  tmdb("/movie/now_playing", { page, region: REGION }).then((d) => d.results);
export const getTopRatedMovies = (page = 1) =>
  tmdb("/movie/top_rated", { page, region: REGION }).then((d) => d.results);
export const getOnTheAir = (page = 1) =>
  tmdb("/tv/on_the_air", { page }).then((d) => d.results);

// Cataloghi paginati (pagine Film / Serie)
export const discover = (type, params = {}) =>
  tmdb(`/discover/${type}`, { sort_by: "popularity.desc", ...params });
export const getGenres = (type) =>
  tmdb(`/genre/${type}/list`).then((d) => d.genres);

// Dettaglio completo
export const getDetails = (type, id) =>
  tmdb(`/${type}/${id}`, {
    append_to_response: "credits,videos,recommendations,similar,external_ids",
  });
export const getSeason = (id, season) => tmdb(`/tv/${id}/season/${season}`);

// Ricerca
export const searchMulti = (q, page = 1) =>
  tmdb("/search/multi", { query: q, page, include_adult: false }).then(
    (d) => d.results
  );

// ---------- Disponibilità catalogo ----------
// /api/list/movie e /api/list/tv restituiscono [{tmdb_id, imdb_id}, ...]
let availCache = null;
export async function getAvailability() {
  if (availCache) return availCache;
  try {
    const cached = JSON.parse(localStorage.getItem("nv_avail") || "null");
    if (cached && Date.now() - cached.ts < AVAIL_TTL) {
      availCache = {
        movie: new Set(cached.movie),
        tv: new Set(cached.tv),
      };
      return availCache;
    }
  } catch {}

  const fetchList = async (type) => {
    const url = `https://${SOURCE}/api/list/${type}?lang=it`;
    const r = await fetch(proxied(url, SOURCE_REFERER));
    const arr = await r.json();
    return arr.map((x) => x.tmdb_id).filter(Boolean);
  };

  try {
    const [movies, tv] = await Promise.all([fetchList("movie"), fetchList("tv")]);
    availCache = { movie: new Set(movies), tv: new Set(tv) };
    localStorage.setItem(
      "nv_avail",
      JSON.stringify({ ts: Date.now(), movie: movies, tv })
    );
  } catch (e) {
    console.warn("Disponibilità non caricata:", e);
    availCache = { movie: new Set(), tv: new Set() };
  }
  return availCache;
}

export function isAvailable(avail, type, id) {
  if (!avail) return true;
  const set = type === "tv" ? avail.tv : avail.movie;
  if (!set || set.size === 0) return true; // se la lista non c'è, non bloccare
  return set.has(Number(id));
}

// ---------- Estrazione stream ----------
// Flusso:
//   1. /api/movie/{id}  oppure /api/tv/{id}/{stagione}/{episodio}
//        -> { src: "/embed/{id}?token=...&expires=...&canPlayFHD=1" }
//   2. GET /embed/...  -> pagina con window.masterPlaylist
//   3. m3u8 = url?token=...&expires=...(&h=1)
export async function getStream(type, tmdbId, season, episode) {
  const isMovie = type === "movie";
  const apiUrl = isMovie
    ? `https://${SOURCE}/api/movie/${tmdbId}`
    : `https://${SOURCE}/api/tv/${tmdbId}/${season}/${episode}`;

  const apiRes = await fetch(proxied(apiUrl, SOURCE_REFERER));
  if (!apiRes.ok) throw new Error("Sorgente non raggiungibile (" + apiRes.status + ")");
  let data;
  try {
    data = await apiRes.json();
  } catch {
    throw new Error("Contenuto non disponibile");
  }
  if (!data || !data.src) throw new Error("Contenuto non disponibile");

  const embedUrl = `https://${SOURCE}${data.src}`;
  const html = await (await fetch(proxied(embedUrl, SOURCE_REFERER))).text();

  const urlM = html.match(/url:\s*'([^']+)'/);
  const tokM = html.match(/['"]token['"]\s*:\s*'([^']+)'/);
  const expM = html.match(/['"]expires['"]\s*:\s*'([^']+)'/);
  if (!urlM || !tokM || !expM)
    throw new Error("Stream non trovato");

  const fhd = /canPlayFHD\s*=\s*true/.test(html);
  const sep = urlM[1].includes("?") ? "&" : "?";
  let m3u8 = `${urlM[1]}${sep}token=${tokM[1]}&expires=${expM[1]}`;
  if (fhd) m3u8 += "&h=1";

  // La master playlist passata dal proxy: i segmenti/sub sono già riscritti.
  return { src: proxied(m3u8, SOURCE_REFERER), raw: m3u8 };
}
