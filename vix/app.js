// ============================================================
//  Nova — applicazione (controller di pagina)
// ============================================================
import * as api from "./api.js";
import { img } from "./api.js";
import {
  $, $$, el, card, rail, skeletonRail, grid, personCard, toast,
  normalize, fmtRuntime,
} from "./ui.js";
import * as store from "./store.js";
import { mountPlayer, disposePlayer } from "./player.js";
import {
  route, navigate, startRouter, currentQuery, configureViewCache,
} from "./router.js";

const app = $("#app");
let AVAIL = null;

// ---------- helper ----------
function setActiveNav(name) {
  $$(".nav-link, .tab").forEach((a) =>
    a.classList.toggle("active", a.dataset.nav === name));
}

// Evidenzia l'icona/voce giusta in base all'URL corrente.
// Va richiamato a OGNI cambio vista (anche sul restore dalla cache, dove
// l'handler della route non viene rieseguito), altrimenti tornando indietro
// (es. da Serie a Film) l'icona attiva resterebbe quella della pagina prima.
const NAV_BY_PATH = {
  "/": "home",
  "/movies": "movies",
  "/series": "series",
  "/search": "search",
  "/list": "list",
};
function syncActiveNav() {
  const path = "/" + (location.hash.slice(1) || "/").replace(/^\//, "").split("?")[0];
  setActiveNav(NAV_BY_PATH[path] || "");
}

function markAvailability(root) {
  if (!AVAIL) return;
  root.querySelectorAll(".card[data-id]:not(.card--owned)").forEach((c) => {
    if (!api.isAvailable(AVAIL, c.dataset.type, c.dataset.id))
      c.classList.add("unavail");
  });
}

function removeCard(node) {
  const track = node.parentElement;
  const sec = node.closest(".rail");
  node.remove();
  if (track && !track.querySelector(".card")) (sec || track).remove();
}

function wlCard(w) {
  return card(
    { type: w.type, id: w.id, title: w.title, poster: w.poster, backdrop: w.backdrop,
      vote: w.vote ? Number(w.vote).toFixed(1) : null, year: w.year },
    { onRemove: (n) => { store.toggleWatchlist({ type: w.type, id: w.id }); removeCard(n); toast("Rimosso dalla lista"); } });
}

function progressCard(p) {
  return card(
    { type: p.type, id: p.id, title: p.title, poster: p.poster, backdrop: p.backdrop,
      vote: p.vote ? Number(p.vote).toFixed(1) : null },
    {
      href: p.type === "tv"
        ? `#/watch/tv/${p.id}?s=${p.season}&e=${p.episode}`
        : `#/watch/movie/${p.id}`,
      onRemove: (n) => { store.removeProgress(p.type, p.id); removeCard(n); toast("Rimosso da Continua a guardare"); },
    });
}

// ============================================================
//  HOME
// ============================================================
route("/", async () => {
  setActiveNav("home");
  const rows = el("div", { class: "rows" },
    skeletonRail("Tendenze"), skeletonRail("Film popolari"), skeletonRail("Serie popolari"));
  app.replaceChildren(rows);

  const [trending, popM, popT, now, topM, air] = await Promise.all([
    api.getTrending().catch(() => []),
    api.getPopularMovies().catch(() => []),
    api.getPopularTV().catch(() => []),
    api.getNowPlaying().catch(() => []),
    api.getTopRatedMovies().catch(() => []),
    api.getOnTheAir().catch(() => []),
  ]);
  const progress = store.getProgressAll();
  const watchlist = store.getWatchlist();

  //const heroItem = normalize(trending.find((t) => t.backdrop_path) || trending[0] || {});
  //if (heroItem.id) app.insertBefore(buildHero(heroItem), rows);

  rows.replaceChildren();
  if (progress.length) rows.append(rail("Continua a guardare", progress.map(progressCard)));
  if (watchlist.length) rows.append(rail("La mia lista", watchlist.map(wlCard), { moreHref: "#/list" }));
  rows.append(
    rail("Tendenze della settimana", trending.map(normalize)),
    rail("Film popolari", popM.map(normalize), { moreHref: "#/movies" }),
    rail("Serie popolari", popT.map(normalize), { moreHref: "#/series" }),
    rail("Ora al cinema", now.map(normalize)),
    rail("Serie del momento", air.map(normalize)),
    rail("Film più votati", topM.map(normalize)));

  const { GENRE_ROWS } = await import("./config.js");
  const byGenre = await Promise.all(
    GENRE_ROWS.map((g) => api.discover(g.type, { with_genres: g.id }).then((d) => d.results).catch(() => [])));
  GENRE_ROWS.forEach((g, i) => {
    if (byGenre[i].length)
      rows.append(rail(`${g.name} • ${g.type === "tv" ? "Serie" : "Film"}`,
        byGenre[i].map((it) => normalize({ ...it, media_type: g.type }))));
  });

  markAvailability(app);
});

function buildHero(it) {
  const bg = img(it.backdrop, "w1280") || img(it.poster, "w780");
  const poster = img(it.poster, "w500") || bg;
  return el("section", { class: "hero hero-cinema" },
    el("div", { class: "hero-bg", style: bg ? `background-image:url(${bg})` : "" }),
    el("div", { class: "hero-shell" },
      el("div", { class: "hero-body" },
        el("div", { class: "hero-kicker" }, "Nova Premiere"),
        el("h1", { class: "hero-title" }, it.title),
        el("div", { class: "hero-meta" },
          it.vote ? el("span", { class: "pill" }, "★ " + it.vote) : null,
          it.year ? el("span", {}, it.year) : null,
          el("span", { class: `tag tag-${it.type}` }, it.type === "tv" ? "Serie TV" : "Film")),
        el("p", { class: "hero-overview" },
          (it.overview || "").slice(0, 230) + (it.overview && it.overview.length > 230 ? "…" : "")),
        el("div", { class: "hero-actions" },
          el("a", { class: "btn btn-primary", href: `#/${it.type}/${it.id}` }, "▶  Entra nel titolo"),
          el("a", { class: "btn btn-ghost", href: `#/${it.type}/${it.id}` }, "Dettagli"))),
      el("a", {
        class: "hero-feature-card",
        href: `#/${it.type}/${it.id}`,
        style: poster ? `--poster-glow:url(${poster})` : "",
        "aria-label": `Apri ${it.title}`,
      },
        poster ? el("img", { src: poster, alt: it.title }) : el("div", { class: "poster-empty" }, "🎬"),
        el("div", { class: "hero-feature-copy" },
          el("span", {}, it.type === "tv" ? "Serie in evidenza" : "Film in evidenza"),
          el("strong", {}, it.title))),
      el("div", { class: "hero-dashboard", "aria-hidden": "true" },
        el("span", {}, "4K"),
        el("span", {}, "HDR"),
        el("span", {}, "DPAD READY"))));
}

// ============================================================
//  BROWSE (Film / Serie)
// ============================================================
function browsePage(type) {
  return async (_p, query) => {
    setActiveNav(type === "movie" ? "movies" : "series");
    const genres = await api.getGenres(type).catch(() => []);
    const active = query.g ? Number(query.g) : null;
    const base = type === "movie" ? "#/movies" : "#/series";

    const chips = el("div", { class: "chips" },
      el("a", { class: "chip" + (!active ? " active" : ""), href: base }, "Tutti"),
      genres.map((g) => el("a",
        { class: "chip" + (active === g.id ? " active" : ""), href: `${base}?g=${g.id}` }, g.name)));

    const gridHost = el("div", { class: "grid" });
    const sentinel = el("div", { class: "sentinel" });
    app.replaceChildren(el("div", { class: "page" },
      el("h1", { class: "page-title" }, type === "movie" ? "Film" : "Serie TV"),
      chips, gridHost, sentinel));

    let page = 1, loading = false, done = false;
    const load = async () => {
      if (loading || done) return;
      loading = true;
      const params = { page };
      if (active) params.with_genres = active;
      const res = await api.discover(type, params).catch(() => ({ results: [], total_pages: 0 }));
      const frag = document.createDocumentFragment();
      res.results.forEach((i) => frag.append(card(normalize({ ...i, media_type: type }))));
      gridHost.append(frag);
      markAvailability(gridHost);
      page++;
      if (page > res.total_pages || page > 20) done = true;
      loading = false;
    };
    await load();
    new IntersectionObserver((e) => { if (e[0].isIntersecting) load(); }, { rootMargin: "700px" }).observe(sentinel);
  };
}
route("/movies", browsePage("movie"));
route("/series", browsePage("tv"));

// ============================================================
//  LA MIA LISTA
// ============================================================
route("/list", async () => {
  setActiveNav("list");
  const prog = store.getProgressAll();
  const wl = store.getWatchlist();
  const page = el("div", { class: "page" }, el("h1", { class: "page-title" }, "La mia lista"));
  if (prog.length) { page.append(el("h2", { class: "sub-title" }, "Continua a guardare"), grid(prog.map(progressCard))); }
  if (wl.length) { page.append(el("h2", { class: "sub-title" }, "Salvati"), grid(wl.map(wlCard))); }
  if (!prog.length && !wl.length)
    page.append(el("p", { class: "empty" }, "Niente qui ancora. Aggiungi film e serie alla tua lista!"));
  app.replaceChildren(page);
  markAvailability(app);
});

// ============================================================
//  RICERCA
// ============================================================
route("/search", async (_p, query) => {
  setActiveNav("search");
  const q0 = query.q || "";
  const input = el("input", { class: "search-page-input", type: "search", placeholder: "Cerca film o serie…", "aria-label": "Cerca", value: q0 });
  const results = el("div", {});
  app.replaceChildren(el("div", { class: "page" },
    el("h1", { class: "page-title" }, "Cerca"),
    el("div", { class: "search search-page" }, el("span", { class: "search-ic" }, "🔍"), input),
    results));

  let t;
  const doSearch = async (q) => {
    q = (q || "").trim();
    if (!q) { results.replaceChildren(el("p", { class: "empty" }, "Digita per cercare un titolo.")); return; }
    results.replaceChildren(skeletonRail(""));
    const res = (await api.searchMulti(q).catch(() => []))
      .filter((r) => r.media_type !== "person" && (r.poster_path || r.backdrop_path));
    if (!res.length) { results.replaceChildren(el("p", { class: "empty" }, "Nessun risultato.")); return; }
    results.replaceChildren(grid(res.map(normalize)));
    markAvailability(results);
  };
  window.__novaSearch = doSearch;
  input.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => doSearch(input.value), 300); });
  doSearch(q0);
});

// ============================================================
//  DETTAGLIO
// ============================================================
route("/movie/:id", (p) => detailPage("movie", p.id));
route("/tv/:id", (p) => detailPage("tv", p.id));

async function detailPage(type, id) {
  setActiveNav("");
  app.replaceChildren(el("div", { class: "loading" }, el("div", { class: "spinner" })));

  const d = await api.getDetails(type, id).catch(() => null);
  if (!d) { app.replaceChildren(el("p", { class: "empty" }, "Errore nel caricamento.")); return; }

  const it = normalize({ ...d, media_type: type });
  const bg = img(d.backdrop_path, "w1280") || img(d.poster_path, "w780");
  const available = api.isAvailable(AVAIL, type, id);
  const genres = (d.genres || []).map((g) => g.name).join(" · ");
  const runtime = fmtRuntime(d.runtime || (d.episode_run_time && d.episode_run_time[0]));
  const trailer = (d.videos?.results || []).find((v) => v.site === "YouTube" && /Trailer|Teaser/.test(v.type));
  const progress = store.getProgress(type, id);
  const tvSeason = progress?.season || (d.seasons || []).find((s) => s.season_number > 0)?.season_number || 1;
  const tvEpisode = progress?.episode || 1;

  const listBtn = el("button", { class: "btn btn-ghost" }, store.inWatchlist(type, id) ? "✓  Nella lista" : "+  La mia lista");
  listBtn.onclick = () => {
    const added = store.toggleWatchlist({ type, id, title: it.title, poster: d.poster_path, backdrop: d.backdrop_path, year: it.year, vote: it.vote });
    listBtn.textContent = added ? "✓  Nella lista" : "+  La mia lista";
    toast(added ? "Aggiunto alla tua lista" : "Rimosso dalla lista");
  };

  const actions = el("div", { class: "detail-actions" });
  actions.append(type === "movie"
    ? el("a", { class: "btn btn-primary", href: `#/watch/movie/${id}` }, "▶  Riproduci")
    : el("a", { class: "btn btn-primary", href: `#/watch/tv/${id}?s=${tvSeason}&e=${tvEpisode}` },
        progress ? `▶  Riprendi S${tvSeason}·E${tvEpisode}` : "▶  Riproduci S1·E1"));
  actions.append(listBtn);
 // if (trailer) actions.append(el("button", { class: "btn btn-ghost", onclick: () => openTrailer(trailer.key) }, "🎬  Trailer"));

  const facts = el("div", { class: "detail-facts" },
    it.vote ? el("div", { class: "fact" }, el("span", {}, "Voto"), el("strong", {}, "★ " + it.vote)) : null,
    it.year ? el("div", { class: "fact" }, el("span", {}, "Anno"), el("strong", {}, it.year)) : null,
    runtime ? el("div", { class: "fact" }, el("span", {}, type === "tv" ? "Durata ep." : "Durata"), el("strong", {}, runtime)) : null,
    type === "tv" && d.number_of_seasons ? el("div", { class: "fact" }, el("span", {}, "Stagioni"), el("strong", {}, d.number_of_seasons)) : null);

  const detail = el("div", { class: `detail detail-${type}` },
    bg ? el("div", { class: "detail-bg", style: `background-image:url(${bg})` }) : null,
    el("div", { class: "detail-wrap" },
      el("button", { class: "back-link", onclick: () => (history.length > 1 ? history.back() : navigate("/")) }, "← Indietro"),
      el("section", { class: "detail-hero" },
        el("div", { class: "detail-copy" },
          el("div", { class: "detail-kicker" }, type === "tv" ? "Serie TV" : "Film"),
          el("h1", {}, it.title),
          d.tagline ? el("p", { class: "tagline" }, d.tagline) : null,
          genres ? el("p", { class: "genres" }, genres) : null,
          el("p", { class: "overview" }, d.overview || "Nessuna trama disponibile."),
          !available ? el("p", { class: "warn" }, "⚠ Potrebbe non essere disponibile") : null,
          actions),
        el("aside", { class: "detail-panel" },
          img(d.poster_path, "w500")
            ? el("img", { class: "detail-poster", src: img(d.poster_path, "w500"), alt: it.title })
            : el("div", { class: "detail-poster poster-empty" }, "🎬"),
          facts))));
  app.replaceChildren(detail);

  const cast = (d.credits?.cast || []).slice(0, 12);
  if (cast.length) app.append(rail("Cast", cast.map(personCard)));

  if (type === "tv" && d.seasons) app.append(buildEpisodes(d, id));

  const recs = (d.recommendations?.results || d.similar?.results || []).filter((r) => r.poster_path);
  if (recs.length) app.append(rail("Consigliati", recs.map((r) => normalize({ ...r, media_type: r.media_type || type }))));

  markAvailability(app);
}

function buildEpisodes(d, id) {
  const seasons = (d.seasons || []).filter((s) => s.season_number > 0);
  const wrap = el("section", { class: "rail", id: "episodes" },
    el("div", { class: "rail-head" }, el("h2", {}, "Episodi")));
  const select = el("select", { class: "season-select" },
    seasons.map((s) => el("option", { value: s.season_number }, s.name || `Stagione ${s.season_number}`)));
  const list = el("div", { class: "episodes" });
  wrap.append(select, list);

  const loadSeason = async (sn) => {
    list.replaceChildren(el("div", { class: "spinner" }));
    const season = await api.getSeason(id, sn).catch(() => ({ episodes: [] }));
    const frag = document.createDocumentFragment();
    (season.episodes || []).forEach((ep) => {
      const still = img(ep.still_path, "w300");
      frag.append(el("a", { class: "episode", href: `#/watch/tv/${id}?s=${sn}&e=${ep.episode_number}` },
        el("div", { class: "ep-thumb" },
          still ? el("img", { src: still, loading: "lazy", alt: "" }) : el("div", { class: "poster-empty" }, "▶"),
          el("span", { class: "ep-num" }, ep.episode_number)),
        el("div", { class: "ep-body" },
          el("div", { class: "ep-title" }, ep.name || `Episodio ${ep.episode_number}`),
          el("div", { class: "ep-ov" }, (ep.overview || "").slice(0, 140)))));
    });
    list.replaceChildren(frag);
  };
  select.onchange = () => loadSeason(Number(select.value));
  loadSeason(seasons[0]?.season_number || 1);
  return wrap;
}

// ============================================================
//  WATCH (player) — fullscreen, no chrome
// ============================================================
route("/watch/:type/:id", async (p, query) => {
  setActiveNav("");
  disposePlayer();
  document.body.classList.add("player-fullscreen");
  const { type, id } = p;
  const season = query.s ? Number(query.s) : null;
  const episode = query.e ? Number(query.e) : null;

  const video = el("video", { class: "video-js vjs-big-play-centered vjs-fluid", controls: "", preload: "auto", playsinline: "", crossorigin: "anonymous" });
  const status = el("div", { class: "stage-status" }, el("div", { class: "spinner" }), el("span", {}, "Recupero stream…"));
  const stage = el("div", { class: "stage" }, video, status);
  app.replaceChildren(stage);
  // Back button fisso in alto a sinistra, fuori dallo stage
  const backBtn = document.createElement("button");
  backBtn.className = "player-back";
  backBtn.setAttribute("aria-label", "Indietro");
  backBtn.innerHTML = "❮";
  backBtn.onclick = () => {
    const h = location.hash.slice(1);
    const m = h.match(/^\/watch\/(movie|tv)\/(\d+)/);
    if (!m) return;
    // Tornare indietro "per davvero": history.back() tiene allineate la
    // cronologia del browser e lo stack del router. Usare navigate() qui
    // lasciava una voce "/watch" fantasma nella cronologia: premendo poi il
    // tasto Indietro del dispositivo/telecomando si rientrava nel player.
    if (history.length > 1) history.back();
    else navigate("/" + m[1] + "/" + m[2]);
  };
  document.body.append(backBtn);

  const d = await api.getDetails(type, id).catch(() => null);
  const baseTitle = d ? d.title || d.name : "Riproduzione";

  let stream;
  try { stream = await api.getStream(type, id, season, episode); }
  catch (e) {
    status.replaceChildren(el("div", {},
      el("p", {}, "⚠ " + e.message),
      el("p", { class: "muted" }, "Il titolo potrebbe non essere disponibile.")));
    return;
  }
  status.remove();

  const prev = store.getProgress(type, id);
  const startAt = prev && (type === "movie" || (prev.season == season && prev.episode == episode)) ? prev.time : 0;

  mountPlayer(video, stream.src, {
    startAt,
    onTime: (time, duration) => {
      if (!duration) return;
      if (duration - time < 60) { store.removeProgress(type, id); return; }
      store.saveProgress({ type, id, title: baseTitle, season, episode,
        poster: d?.poster_path, backdrop: d?.backdrop_path,
        vote: d?.vote_average ? d.vote_average.toFixed(1) : null, time, duration });
    },
  });
});

// ---------- trailer ----------
function openTrailer(key) {
  const modal = el("div", { class: "modal", onclick: (e) => { if (e.target === modal) modal.remove(); } },
    el("div", { class: "modal-box" },
      el("button", { class: "modal-close", onclick: () => modal.remove() }, "✕"),
      el("iframe", { src: `https://www.youtube.com/embed/${key}?autoplay=1`, allow: "autoplay; fullscreen", allowfullscreen: "" })));
  document.body.append(modal);
}

// ---------- header / ricerca globale ----------
function setupHeader() {
  const input = $("#search-input");
  const form = $("#search-form");
  if (form) form.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (q) navigate(`/search?q=${encodeURIComponent(q)}`);
  });
  if (input) {
    let t;
    input.addEventListener("input", () => {
      clearTimeout(t);
      const q = input.value.trim();
      t = setTimeout(() => {
        if (q.length < 2) return;
        if (location.hash.startsWith("#/search") && window.__novaSearch) window.__novaSearch(q);
        else navigate(`/search?q=${encodeURIComponent(q)}`);
      }, 320);
    });
  }
}

// ============================================================
//  Avvio
// ============================================================
(function init() {
  configureViewCache(app);
  // mantiene l'icona attiva sincronizzata sia sulle pagine nuove ("fresh")
  // sia sui ritorni istantanei dalla cache ("restored")
  window.addEventListener("nova:view", syncActiveNav);
  window.addEventListener("nova:disposeplayer", () => {
    disposePlayer();
    document.body.classList.remove("player-fullscreen");
    const oldBtn = document.querySelector(".player-back");
    if (oldBtn) oldBtn.remove();
  });

  window.addEventListener("nova:exitfullscreen", () => {
    const hash = location.hash.slice(1);
    const m = hash.match(/^\/watch\/(movie|tv)\/(\d+)/);
    if (!m) return; // gia' usciti dal player: niente da fare
    // stesso motivo del tasto a schermo: torna indietro davvero, niente
    // voce "/watch" fantasma che riaprirebbe il player.
    if (history.length > 1) history.back();
    else navigate(`/${m[1]}/${m[2]}`);
  });
  setupHeader();
  startRouter();
  api.getAvailability().then((a) => { AVAIL = a; markAvailability(document); });
})();
