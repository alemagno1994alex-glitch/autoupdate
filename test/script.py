#!/usr/bin/env python3
# build_vod_map.py - TMDB + StreamingCommunity -> data.js
import asyncio, json, re, argparse, datetime
import requests
from playwright.async_api import async_playwright

TMDB_KEY = "2e0b38cfb2936cec8ab1ce48e4335ac3"
TMDB_API = "https://api.themoviedb.org/3"
TMDB_IMG = "https://image.tmdb.org/t/p"
TMDB_LANG = "it-IT"

SC_BASE = "https://streamingcommunityz.build"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "Chrome/137.0.0.0 Safari/537.36")

TIMEOUT = 15000
MAX_PARALLEL = 5

GENRES = {
    28: "Azione", 12: "Avventura", 16: "Animazione", 35: "Commedia",
    80: "Crime", 99: "Documentario", 18: "Dramma", 10751: "Famiglia",
    14: "Fantasy", 36: "Storia", 27: "Horror", 10402: "Musica",
    9648: "Mistero", 10749: "Romance", 878: "Fantascienza",
    10770: "Film TV", 53: "Thriller", 10752: "Guerra", 37: "Western",
    10759: "Azione & Avventura", 10762: "Kids", 10763: "News",
    10764: "Reality", 10765: "Sci-Fi & Fantasy", 10766: "Soap",
    10767: "Talk", 10768: "War & Politics",
}

def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

def tmdb_catalog(kind, pages):
    out = []
    for page in range(1, pages + 1):
        try:
            r = requests.get(
                f"{TMDB_API}/{kind}/popular",
                params={"api_key": TMDB_KEY, "language": TMDB_LANG, "page": page},
                timeout=10,
            )
            if r.status_code != 200:
                break
            for it in r.json().get("results", []):
                gids = it.get("genre_ids") or []
                out.append({
                    "tmdb_id": it["id"],
                    "type": kind,
                    "title": it.get("title") or it.get("name") or "",
                    "original_title": it.get("original_title") or it.get("original_name") or "",
                    "year": (it.get("release_date") or it.get("first_air_date") or "")[:4],
                    "poster": (f"{TMDB_IMG}/w500{it['poster_path']}") if it.get("poster_path") else "",
                    "backdrop": (f"{TMDB_IMG}/original{it['backdrop_path']}") if it.get("backdrop_path") else "",
                    "rating": round(it.get("vote_average") or 0, 1),
                    "overview": it.get("overview") or "",
                    "genres": [GENRES.get(g, "Altro") for g in gids],
                    "popularity": it.get("popularity") or 0,
                })
        except Exception:
            break
    return out

async def resolve_one(page, title, year=None):
    """Ritorna (watch_url, reason) — URL diretto di StreamingCommunity."""
    query = title + (f" {year}" if year else "")
    url = f"{SC_BASE}/it/search?q=" + requests.utils.quote(query)
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT)
        await page.wait_for_timeout(1200)
        html = await page.content()
    except Exception as e:
        return None, f"nav_err:{str(e)[:40]}"

    # Cerca link /it/titles/{id}-{slug} nella pagina dei risultati
    found = re.findall(r'/it/titles/(\d+)-([a-z0-9-]+)', html)
    seen, uniq = set(), []
    for mid, slug in found:
        if mid not in seen:
            seen.add(mid)
            uniq.append((mid, slug))

    if not uniq:
        return None, "not_found"

    target = norm(title)
    for mid, slug in uniq:
        n = norm(slug)
        if n == target or n.startswith(target) or target.startswith(n):
            return f"{SC_BASE}/it/watch/{mid}", "exact"

    # fallback: primo risultato
    return f"{SC_BASE}/it/watch/{uniq[0][0]}", "first"

async def worker(sem, ctx, item, out, lock, counter, total):
    async with sem:
        page = None
        try:
            page = await ctx.new_page()
            url, reason = await resolve_one(page, item["title"], item.get("year"))
            counter[0] += 1
            if url:
                item["sc_id"] = url.rsplit("/", 1)[-1]
                item["watch_url"] = url
                async with lock:
                    out.append(item)
                print(f"[{counter[0]}/{total}] OK  {item['title']} -> {item['sc_id']}  ({reason})")
            else:
                print(f"[{counter[0]}/{total}] X   {item['title']}  ({reason})")
        finally:
            if page:
                try: await page.close()
                except: pass

async def resolve_all(items):
    out, lock, counter = [], asyncio.Lock(), [0]
    sem = asyncio.Semaphore(MAX_PARALLEL)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = await browser.new_context(user_agent=UA)
        try:
            await asyncio.gather(*[
                worker(sem, ctx, it, out, lock, counter, len(items))
                for it in items
            ])
        finally:
            await browser.close()
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default="data.js")
    ap.add_argument("--type", default="movie", choices=["movie", "tv", "both"])
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--parallel", type=int, default=MAX_PARALLEL)
    args = ap.parse_args()

    items = []
    if args.type in ("movie", "both"): items += tmdb_catalog("movie", args.pages)
    if args.type in ("tv", "both"):    items += tmdb_catalog("tv", args.pages)
    if args.limit: items = items[:args.limit]

    print(f"Titoli TMDB: {len(items)}")
    resolved = asyncio.run(resolve_all(items))

    payload = {
        "generated": datetime.datetime.now().isoformat(),
        "total": len(resolved),
        "items": resolved,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("window.VOD_DATA = ")
        json.dump(payload, f, ensure_ascii=False)
        f.write(";\n")
    print(f"\nScritto {len(resolved)}/{len(items)} in {args.output}")

if __name__ == "__main__":
    main()