// ============================================================
//  Nova — router con cache delle schermate (stile app streaming)
// ------------------------------------------------------------
//  Andando avanti la schermata corrente non viene distrutta ma
//  messa da parte VIVA (nodi DOM + posizione di scroll + focus).
//  Tornando indietro viene rimessa istantaneamente, senza
//  ricaricare nulla: scroll e focus esattamente dov'erano.
//
//  Il player (#/watch) e la ricerca (#/search) NON vengono messi
//  in cache: il primo va fermato all'uscita, la seconda cambia a
//  ogni lettera.
// ============================================================

const routes = [];

let rootEl = null;            // contenitore delle viste (#app)
const cache = new Map();      // navKey -> { nodes, scrollY, focusNode }
let stack = [];               // cronologia logica delle chiavi
let current = null;           // chiave attualmente mostrata

export function configureViewCache(root) {
  rootEl = root;
}

export function route(pattern, handler) {
  // pattern es: "/", "/movie/:id", "/tv/:id", "/search", "/movies", "/list"
  const keys = [];
  const rx = new RegExp(
    "^" +
      pattern
        .replace(/:[^/]+/g, (m) => {
          keys.push(m.slice(1));
          return "([^/]+)";
        })
        .replace(/\//g, "\\/") +
      "$"
  );
  routes.push({ rx, keys, handler });
}

export function navigate(path) {
  if (location.hash.slice(1) === path) handle();
  else location.hash = path;
}

export function currentQuery() {
  const q = location.hash.split("?")[1] || "";
  return Object.fromEntries(new URLSearchParams(q));
}

// ---------- helper chiavi ----------
const navKey = () => location.hash.slice(1) || "/";
const pathOf = (k) => "/" + (k || "").replace(/^\//, "").split("?")[0];
const isWatch = (k) => pathOf(k).startsWith("/watch");
const isSearch = (k) => pathOf(k) === "/search";
const isCacheable = (k) => !isWatch(k) && !isSearch(k);

function emit(type, key) {
  window.dispatchEvent(new CustomEvent("nova:view", { detail: { type, key } }));
}

// ---------- cache delle viste ----------
function saveView(key) {
  const active = document.activeElement;
  const focusNode = active && rootEl.contains(active) ? active : null;
  cache.set(key, {
    nodes: [...rootEl.childNodes],          // riferimenti vivi (restano in memoria)
    scrollY: window.scrollY || window.pageYOffset || 0,
    focusNode,
  });
  rootEl.replaceChildren();                 // stacca la vista (senza distruggerla)
}

function restoreView(key) {
  const v = cache.get(key);
  cache.delete(key);
  rootEl.replaceChildren(...v.nodes);
  requestAnimationFrame(() => {
    window.scrollTo(0, v.scrollY || 0);
    if (v.focusNode) {
      try {
        v.focusNode.focus({ preventScroll: true });
        v.focusNode.scrollIntoView({ block: "nearest", inline: "center" });
      } catch (e) {}
    }
  });
}

function dropView(key) {
  rootEl.replaceChildren();
  cache.delete(key);
}

// ---------- dispatch ----------
async function dispatch(key) {
  const path = pathOf(key);
  for (const { rx, keys, handler } of routes) {
    const m = path.match(rx);
    if (m) {
      const params = {};
      keys.forEach((k, i) => (params[k] = decodeURIComponent(m[i + 1])));
      window.scrollTo(0, 0);
      await handler(params, currentQuery());
      return true;
    }
  }
  return false;
}

// ---------- gestione navigazione ----------
async function handle() {
  if (!rootEl) rootEl = document.getElementById("app");
  const key = navKey();

  // uscendo dal player: fermalo (audio/video non devono restare in background)
  if (current !== null && isWatch(current)) {
    window.dispatchEvent(new CustomEvent("nova:disposeplayer"));
  }

  const idx = stack.lastIndexOf(key);
  const isBack = idx !== -1 && idx < stack.length - 1;

  // metti da parte (o scarta) la vista corrente
  if (current !== null && rootEl) {
    if (isCacheable(current)) saveView(current);
    else dropView(current);
  }

  // --- INDIETRO ---
  if (isBack) {
    stack.splice(idx + 1).forEach((k) => cache.delete(k)); // scarta le viste sopra
    current = key;
    if (cache.has(key)) {
      restoreView(key);            // ripristino istantaneo
      emit("restored", key);
      return;
    }
    dropView(key);                  // non in cache (player/ricerca): ri-renderizza
    if (!(await dispatch(key))) return navigate("/");
    emit("fresh", key);
    return;
  }

  // --- AVANTI / NUOVA PAGINA ---
  // ricerche consecutive: sostituisci la voce invece di accumularle
  if (stack.length && isSearch(stack[stack.length - 1]) && isSearch(key)) {
    stack[stack.length - 1] = key;
  } else if (idx === -1) {
    stack.push(key);
  }
  current = key;
  dropView(key);
  if (!(await dispatch(key))) return navigate("/");
  emit("fresh", key);
}

export function startRouter() {
  window.addEventListener("hashchange", handle);
  handle();
}
