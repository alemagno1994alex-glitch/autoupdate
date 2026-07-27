// ============================================================
//  Nova — componenti UI (card, righe, griglie, toast, helper)
// ============================================================
import { img } from "./api.js";
import { getProgress } from "./store.js";

export const $ = (s, r = document) => r.querySelector(s);
export const $$ = (s, r = document) => [...r.querySelectorAll(s)];

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null) continue;
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k.startsWith("on") && typeof v === "function")
      node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c == null) continue;
    node.append(c.nodeType ? c : document.createTextNode(c));
  }
  return node;
}

// ---------- normalizzazione TMDB ----------
export function normalize(item) {
  const type =
    item.media_type === "tv" || item.media_type === "movie"
      ? item.media_type
      : item.title || item.release_date
      ? "movie"
      : "tv";
  return {
    type,
    id: item.id,
    title: item.title || item.name || "Senza titolo",
    poster: item.poster_path,
    backdrop: item.backdrop_path,
    overview: item.overview,
    vote: item.vote_average ? item.vote_average.toFixed(1) : null,
    year: (item.release_date || item.first_air_date || "").slice(0, 4) || null,
  };
}

export function fmtRuntime(min) {
  if (!min) return null;
  const h = Math.floor(min / 60), m = min % 60;
  return h ? `${h}h ${m}m` : `${m}m`;
}

// ---------- card ----------
// opts: { href, onRemove } — onRemove(node) mostra il pulsante rimuovi
export function card(item, opts = {}) {
  const it = item.type ? item : normalize(item);
  const poster = img(it.poster, "w342");
  const href = opts.href || `#/${it.type}/${it.id}`;

  const prog = getProgress(it.type, it.id);
  let bar = null;
  if (prog && prog.duration && prog.time) {
    const pct = Math.min(100, (prog.time / prog.duration) * 100);
    bar = el("div", { class: "card-progress" }, el("i", { style: `width:${pct}%` }));
  }

  const posterEl = el("div", { class: "poster" },
    poster
      ? el("img", { src: poster, alt: it.title, loading: "lazy" })
      : el("div", { class: "poster-empty" }, "🎬"),
    el("span", { class: "poster-vignette", "aria-hidden": "true" }),
    el("span", { class: "poster-action", "aria-hidden": "true" }, "Apri"),
    el("span", { class: "badge badge-kind" }, it.type === "tv" ? "Serie" : "Film"),
    it.vote ? el("span", { class: "badge badge-vote" }, "★ " + it.vote) : null,
    bar);

  const a = el("a",
    {
      class: `card card-${it.type}`,
      href,
      "data-type": it.type,
      "data-id": it.id,
      style: poster ? `--poster-glow:url(${poster})` : "",
      "aria-label": `${it.title}${it.year ? `, ${it.year}` : ""}`,
    },
    posterEl,
    el("div", { class: "meta" },
      el("span", { class: "meta-title" }, it.title),
      el("span", { class: "meta-sub" }, `${it.year || "Nova"} · ${it.type === "tv" ? "Serie" : "Film"}`)));

  if (opts.onRemove) {
    a.classList.add("card--owned");
    const rm = el("button", { class: "card-rm", "aria-label": "Rimuovi", tabindex: "-1" }, "✕");
    rm.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); opts.onRemove(a); });
    posterEl.append(rm);
  }
  return a;
}

// ---------- riga / carosello ----------
export function rail(title, items, { moreHref } = {}) {
  if (!items || !items.length) return null;
  return el("section", { class: "rail" },
    el("div", { class: "rail-head" },
      el("div", { class: "rail-title" },
        el("span", { class: "rail-eyebrow" }, "Collezione"),
        el("h2", {}, title)),
      moreHref ? el("a", { class: "rail-more", href: moreHref }, "Tutti ›") : null),
    el("div", { class: "rail-track" },
      items.map((i) => (i.nodeType ? i : card(i)))));
}

export function skeletonRail(title) {
  return el("section", { class: "rail" },
    el("div", { class: "rail-head" }, el("h2", {}, title)),
    el("div", { class: "rail-track" },
      Array.from({ length: 8 }, () =>
        el("div", { class: "card skeleton" }, el("div", { class: "poster" })))));
}

// ---------- griglia ----------
export function grid(items) {
  return el("div", { class: "grid" }, items.map((i) => (i.nodeType ? i : card(i))));
}

// ---------- cast / persona ----------
export function personCard(c) {
  const p = img(c.profile_path, "w185");
  return el("div", { class: "person" },
    p ? el("img", { src: p, alt: c.name, loading: "lazy" })
      : el("div", { class: "person-empty" }, "👤"),
    el("span", { class: "person-name" }, c.name),
    el("span", { class: "person-role" }, c.character || ""));
}

// ---------- toast ----------
let toastTimer;
export function toast(msg) {
  let t = $("#toast");
  if (!t) { t = el("div", { id: "toast", class: "toast" }); document.body.append(t); }
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 2400);
}
