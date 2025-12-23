#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import requests
from pathlib import Path

URLS = [
    "https://blackzone.gt.tc/cielo_del_rom.php?page=cinema",
    "https://blackzone.gt.tc/cielo_del_rom.php?page=intrattenimento",
    "https://blackzone.gt.tc/cielo_del_rom.php?page=sport",
    "https://blackzone.gt.tc/cielo_del_rom.php?page=kids"
]
OUTPUT = "solo_sky.m3u"

def download_blackzone(url):
    print(f"Scarico (Playwright): {url}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=60000)
            m3u_text = page.inner_text("body")
            browser.close()
            return m3u_text
    except Exception as e:
        print(f"⚠️  ERRORE: {e}")
        return None

def download_simple(url):
    print(f"Scarico (Requests): {url}")
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"⚠️  ERRORE: {e}")
        return None

def merge_playlists():
    merged = ["#EXTM3U"]
    success_count = 0
    
    for url in URLS:
        print(f"\n--- PROCESSO: {url} ---")
        
        if "blackzone" in url:
            content = download_blackzone(url)
        else:
            content = download_simple(url)
        
        if content is None:
            print(f"❌ Saltato")
            continue
        
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        lines = [line for line in lines if line.upper() != "#EXTM3U"]
        
        if lines:
            merged.extend(lines)
            success_count += 1
            print(f"✓ OK: {len(lines)} righe")
    
    if success_count > 0:
        Path(OUTPUT).write_text("\n".join(merged), encoding="utf-8")
        print(f"\n✓ COMPLETATO: {OUTPUT}")
        return True
    else:
        Path(OUTPUT).write_text("#EXTM3U\n", encoding="utf-8")
        return False

if __name__ == "__main__":
    merge_playlists()