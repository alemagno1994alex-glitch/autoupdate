#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import requests
from pathlib import Path

# URL da unire
URLS = [
    "https://blackzone.gt.tc/cielo_del_rom.php?page=cinema",  # protetto → Playwright
    "https://xromtv.com/italia/player/intrattenimento-_-xrom-_-italia",
    "http://xromtv.com/italia/player/sports-_-xrom-_-italia",
    "https://xromtv.com/italia/player/bambini-_-xrom-_-italia"
]

OUTPUT = "solo_sky.m3u"

# -------------------------------
# Scarica con Playwright (solo per blackzone)
# -------------------------------
def download_blackzone(url):
    print(f"Scarico (Playwright): {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        # Il contenuto M3U è nel body
        m3u_text = page.inner_text("body")

        browser.close()
        return m3u_text

# -------------------------------
# Scarica con Requests (xromtv)
# -------------------------------
def download_simple(url):
    print(f"Scarico (Requests): {url}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text

# -------------------------------
# MERGE
# -------------------------------
def merge_playlists():
    merged = ["#EXTM3U"]  # Solo uno all'inizio

    for url in URLS:
        print(f"\n--- PROCESSO: {url} ---")

        if "blackzone" in url:
            content = download_blackzone(url)
        else:
            content = download_simple(url)

        # Pulisci righe vuote
        lines = [line.strip() for line in content.splitlines() if line.strip()]

        # Rimuovi eventuali #EXTM3U interni
        lines = [line for line in lines if line.upper() != "#EXTM3U"]

        merged.extend(lines)

    Path(OUTPUT).write_text("\n".join(merged), encoding="utf-8")
    print(f"\n✓ MERGE COMPLETATO → {OUTPUT}")


# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    merge_playlists()
