// ============================================================
//  Nova — configurazione
// ============================================================

// Proxy CORS (gira sulla tua VPS). Tutto il traffico passa di qui.
export const PROXY = "https://xromita.com/xrom-voood/xrom-vod-proxy.php?url=";

// Sorgente stream
export const SOURCE = "vixsrc.to";
export const SOURCE_REFERER = "https://vixsrc.to/";

// TMDB (metadati: titoli, poster, trame, cast...). Chiave pubblica TMDB v3:
// puoi sostituirla con la tua su https://www.themoviedb.org/settings/api
export const TMDB_KEY = "8265bd1679663a7ea12ac168da84d2e8";
export const TMDB_BASE = "https://api.themoviedb.org/3";
export const TMDB_IMG = "https://image.tmdb.org/t/p";
export const LANG = "it-IT";
export const REGION = "IT";

// Generi mostrati nelle righe della home / filtri
export const GENRE_ROWS = [
  { id: 28, name: "Azione", type: "movie" },
  { id: 35, name: "Commedia", type: "movie" },
  { id: 27, name: "Horror", type: "movie" },
  { id: 878, name: "Fantascienza", type: "movie" },
  { id: 16, name: "Animazione", type: "movie" },
  { id: 53, name: "Thriller", type: "movie" },
  { id: 10749, name: "Romantico", type: "movie" },
  { id: 80, name: "Crime", type: "tv" },
];

// Cache disponibilità catalogo (ms)
export const AVAIL_TTL = 6 * 60 * 60 * 1000; // 6 ore
