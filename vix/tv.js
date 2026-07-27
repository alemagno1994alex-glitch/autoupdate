// ============================================================
//  Nova — navigazione TV / telecomando (modello a righe)
// ------------------------------------------------------------
//  Niente "geometria a caso": la pagina è una PILA DI RIGHE (rail).
//    • Su / Giù  -> cambia riga, mantenendo la colonna (la x più vicina)
//    • Sx / Dx   -> si muove dentro la riga
//    • OK/Enter  -> attiva l'elemento
//    • Back      -> indietro (o chiude il trailer)
//  Deterministico: dall'ultima riga Su va sempre alla riga sopra; si
//  arriva alla barra in alto solo quando si è in cima ai contenuti.
//
//  La "modalità TV" si attiva alla prima freccia e si spegne al mouse,
//  così su PC col mouse l'esperienza resta quella classica.
// ============================================================

// Contenitori che fanno da "riga" (i loro figli focusabili stanno in fila)
const RAIL_SEL =
  ".topbar, .tabbar, .hero-actions, .chips, .rail-track, .grid, " +
  ".episodes, .search-page, .watch-bar, .watch-next";

// Elementi focusabili (le "celle" delle righe)
const ITEM_SEL =
  ".brand, .card, .nav-link, .tab, .chip, .episode, .btn, .search-btn, .season-select, " +
  ".hero-feature-card, #search-input, .search-page-input, .back-link, .modal-close";

const WRAP_ROW_CONTAINERS = new Set(["grid", "episodes"]);

// ---------- utilità ----------
const isVisible = (el) => {
  if (el.offsetParent === null && getComputedStyle(el).position !== "fixed")
    return false;
  const r = el.getBoundingClientRect();
  return r.width > 1 && r.height > 1;
};

const rectOf = (el) => el.getBoundingClientRect();
const docTopOf = (el) => {
  const r = rectOf(el);
  const position = getComputedStyle(el).position;
  if (position === "fixed") {
    if (el.closest(".topbar")) return -1;
    if (el.closest(".tabbar")) return Number.MAX_SAFE_INTEGER;
  }
  return r.top + window.scrollY;
};
const centerX = (el) => {
  const r = rectOf(el);
  return r.left + r.width / 2;
};
const centerY = (el) => {
  const r = rectOf(el);
  return docTopOf(el) + r.height / 2;
};

// Su TV (app nativa) lo scroll "smooth" è a scatti: usiamo quello istantaneo.
const SCROLL_BEHAVIOR =
  document.documentElement.classList.contains("native-tv") ? "auto" : "smooth";

function enterTvMode() {
  document.body.classList.add("tv-nav");
}
function exitTvMode() {
  document.body.classList.remove("tv-nav");
}

function focusEl(el) {
  if (!el) return;
  el.focus({ preventScroll: true });
  el.scrollIntoView({ block: "nearest", inline: "nearest", behavior: SCROLL_BEHAVIOR });
}

// ---------- costruzione delle righe ----------
// Ritorna [{ items: [el,...] }, ...] ordinate dall'alto in basso.
function buildRails() {
  const rails = [];
  const used = new Set();

  for (const container of document.querySelectorAll(RAIL_SEL)) {
    const items = [...container.querySelectorAll(ITEM_SEL)].filter(isVisible);
    if (!items.length) continue;
    items.forEach((i) => used.add(i));
    items.sort((a, b) => rectOf(a).left - rectOf(b).left);
    splitVisualRows(container, items).forEach((row) => rails.push(row));
  }

  // focusabili "orfani" (non dentro una riga nota) -> riga a sé
  for (const el of document.querySelectorAll(ITEM_SEL)) {
    if (used.has(el) || !isVisible(el)) continue;
    used.add(el);
    rails.push({ items: [el] });
  }

  // Ordina per posizione nel documento, non nel viewport: con la nav fissa,
  // ordinare via getBoundingClientRect().top mandava "Su" sempre all'header.
  rails.forEach((r) => (r.top = Math.min(...r.items.map(docTopOf))));
  rails.sort((a, b) => a.top - b.top);
  return rails;
}

function locate(rails, el) {
  for (let r = 0; r < rails.length; r++) {
    const i = rails[r].items.indexOf(el);
    if (i >= 0) return [r, i];
  }
  return [-1, -1];
}

function nearestByX(items, x) {
  let best = items[0];
  let bestD = Infinity;
  for (const it of items) {
    const d = Math.abs(centerX(it) - x);
    if (d < bestD) {
      bestD = d;
      best = it;
    }
  }
  return best;
}

function splitVisualRows(container, items) {
  const shouldSplit = [...WRAP_ROW_CONTAINERS].some((className) =>
    container.classList.contains(className));
  if (!shouldSplit || items.length < 2) return [{ items }];

  const rows = [];
  const sorted = [...items].sort((a, b) => {
    const ra = rectOf(a);
    const rb = rectOf(b);
    return docTopOf(a) - docTopOf(b) || ra.left - rb.left;
  });

  for (const item of sorted) {
    const rect = rectOf(item);
    const midY = centerY(item);
    let row = rows.find((candidate) =>
      Math.abs(candidate.midY - midY) < Math.max(18, rect.height * 0.35));
    if (!row) {
      row = { items: [], midY };
      rows.push(row);
    }
    row.items.push(item);
    row.midY = (row.midY * (row.items.length - 1) + midY) / row.items.length;
  }

  rows.forEach((row) => row.items.sort((a, b) => rectOf(a).left - rectOf(b).left));
  return rows;
}

// Primo elemento sensato su una pagina nuova: pulsante principale (hero/Riproduci),
// poi la prima card, poi la prima riga dentro #app — mai l'header.
function defaultFocus() {
  const appEl = document.getElementById("app");
  if (appEl) {
    const pri = appEl.querySelector(".btn-primary");
    if (pri && isVisible(pri)) return pri;
    const card = [...appEl.querySelectorAll(".card")].find(isVisible);
    if (card) return card;
  }
  const rails = buildRails();
  for (const rl of rails) {
    if (appEl && appEl.contains(rl.items[0])) return rl.items[0];
  }
  return rails[0] ? rails[0].items[0] : null;
}

// ---------- movimento ----------
function move(dir) {
  const rails = buildRails();
  if (!rails.length) return;

  const cur = document.activeElement;
  let r = -1;
  let i = -1;
  if (cur && cur !== document.body) [r, i] = locate(rails, cur);

  if (r < 0) {
    focusEl(defaultFocus());
    return;
  }

  if (dir === "left") {
    if (i > 0) focusEl(rails[r].items[i - 1]);
    return;
  }
  if (dir === "right") {
    if (i < rails[r].items.length - 1) focusEl(rails[r].items[i + 1]);
    return;
  }

  // su / giù: cambia riga mantenendo la colonna
  const target = dir === "up" ? r - 1 : r + 1;
  if (target < 0 || target >= rails.length) return; // bordo: resta dove sei
  focusEl(nearestByX(rails[target].items, centerX(cur)));
}

// ---------- focus di default sulle pagine nuove ----------
let focusPoll = 0;
function clearFocusPoll() {
  if (focusPoll) {
    clearTimeout(focusPoll);
    focusPoll = 0;
  }
}
function scheduleDefaultFocus() {
  clearFocusPoll();
  if (location.hash.startsWith("#/watch")) return; // sul player comanda il video
  const remote =
    document.documentElement.classList.contains("native-app") ||
    document.body.classList.contains("tv-nav");
  if (!remote) return;

  let tries = 0;
  const attempt = () => {
    focusPoll = 0;
    const t = defaultFocus();
    if (t && isVisible(t)) {
      focusEl(t);
      return;
    }
    if (++tries < 60) focusPoll = setTimeout(attempt, 80);
  };
  focusPoll = setTimeout(attempt, 50);
}

// ---------- gestione tasti ----------
const DIRS = {
  ArrowLeft: "left",
  ArrowRight: "right",
  ArrowUp: "up",
  ArrowDown: "down",
};

function closeModalIfAny() {
  const modal = document.querySelector(".modal");
  if (modal) {
    modal.remove();
    return true;
  }
  return false;
}

function goBack() {
  if (history.length > 1) history.back();
  else location.hash = "#/";
}

function onKey(e) {
  const tgt = e.target;
  const tag = (tgt.tagName || "").toLowerCase();
  const typing = tag === "input" || tag === "textarea" || tgt.isContentEditable;
  const k = e.key;

  // --- Back / Indietro ---
  if (
    k === "Escape" || k === "Backspace" ||
    k === "GoBack" || k === "BrowserBack" || k === "XF86Back"
  ) {
    if (typing && k === "Backspace") return; // nel campo cerca: cancella
    e.preventDefault();
    if (closeModalIfAny()) return;
    goBack();
    return;
  }

  const dir = DIRS[k];
  if (!dir && k !== "Enter") return;

  // sul player le frecce controllano il video (gestite da player.js)
  if (location.hash.startsWith("#/watch")) return;

  clearFocusPoll(); // l'utente prende il controllo: stop all'auto-focus

  // --- OK / Enter ---
  if (k === "Enter") {
    if (typing) return; // la ricerca ha il suo handler
    const a = document.activeElement;
    if (a && a !== document.body) {
      e.preventDefault();
      enterTvMode();
      a.click();
    }
    return;
  }

  // --- dentro al campo di ricerca: ←/→ muovono il cursore, ↓ esce ---
  if (typing) {
    if (k === "ArrowDown") {
      e.preventDefault();
      enterTvMode();
      move("down");
    }
    return;
  }

  // --- frecce normali ---
  e.preventDefault();
  enterTvMode();
  move(dir);
}

// ---------- init ----------
function init() {
  // La navigazione D-pad/telecomando va attivata SOLO dentro l'app NovaTV
  // (UA "NovaTVApp/tv" -> classe native-tv). Su PC/browser le frecce devono
  // scrollare la pagina normalmente, senza "fallback" alla modalita' TV.
  if (!document.documentElement.classList.contains("native-tv")) return;

  document.addEventListener("keydown", onKey);
  document.addEventListener("mousemove", exitTvMode, { passive: true });

  // il router annuncia ogni cambio vista:
  //   "fresh"    pagina nuova    -> focus di default sui contenuti
  //   "restored" back istantaneo -> il focus l'ha già rimesso il router
  window.addEventListener("nova:view", (e) => {
    if (e.detail && e.detail.type === "restored") {
      clearFocusPoll();
      return;
    }
    scheduleDefaultFocus();
  });
}

if (document.readyState === "loading")
  document.addEventListener("DOMContentLoaded", init);
else init();
