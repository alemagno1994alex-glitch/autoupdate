// ============================================================
//  Nova — store locale (watchlist + continua a guardare)
// ============================================================

const LIST_KEY = "nv_watchlist";
const PROGRESS_KEY = "nv_progress";

function read(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
}
function write(key, val) {
  localStorage.setItem(key, JSON.stringify(val));
}

// ---------- Watchlist (La mia lista) ----------
export function getWatchlist() {
  return read(LIST_KEY, []);
}
export function inWatchlist(type, id) {
  return getWatchlist().some((x) => x.type === type && x.id == id);
}
export function toggleWatchlist(item) {
  const list = getWatchlist();
  const i = list.findIndex((x) => x.type === item.type && x.id == item.id);
  if (i >= 0) {
    list.splice(i, 1);
    write(LIST_KEY, list);
    return false;
  }
  list.unshift({
    type: item.type,
    id: item.id,
    title: item.title,
    poster: item.poster,
    backdrop: item.backdrop,
    year: item.year,
    vote: item.vote,
    addedAt: Date.now(),
  });
  write(LIST_KEY, list);
  return true;
}

// ---------- Continua a guardare ----------
// chiave: type:id  (per le serie salva stagione/episodio correnti)
export function getProgressAll() {
  const obj = read(PROGRESS_KEY, {});
  return Object.values(obj).sort((a, b) => b.updatedAt - a.updatedAt);
}
export function getProgress(type, id) {
  const obj = read(PROGRESS_KEY, {});
  return obj[`${type}:${id}`] || null;
}
export function saveProgress(entry) {
  const obj = read(PROGRESS_KEY, {});
  const key = `${entry.type}:${entry.id}`;
  obj[key] = { ...obj[key], ...entry, updatedAt: Date.now() };
  write(PROGRESS_KEY, obj);
}
export function removeProgress(type, id) {
  const obj = read(PROGRESS_KEY, {});
  delete obj[`${type}:${id}`];
  write(PROGRESS_KEY, obj);
}

// ---------- Backup / import ----------
export function exportData() {
  return {
    watchlist: read(LIST_KEY, []),
    progress: read(PROGRESS_KEY, {}),
  };
}
export function importData(data) {
  if (data.watchlist) write(LIST_KEY, data.watchlist);
  if (data.progress) write(PROGRESS_KEY, data.progress);
}
