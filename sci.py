import asyncio
import json
import sys
import threading
import time
import re
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.async_api import async_playwright

# ==================== CONFIG ====================
PASSWORD = "---!!!wafu.aq.sa.lahat.-0419!!!---"
PLAYER = os.environ.get("PLAYER", "X1")   # X1 o X2
PORT = 8000
OUTPUT = "sky.m3u"
CI = os.environ.get("CI", "false").lower() == "true"

# ==================== LOGO MAP (esempio ridotto) ====================
LOGO_MAP = {
    "sky uno": "https://pixel.disco.nowtv.it/logo/skychb_477_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky atlantic": "https://pixel.disco.nowtv.it/logo/skychb_226_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky serie": "https://pixel.disco.nowtv.it/logo/skychb_684_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    # ... inserisci qui tutte le tue mappe (come nel tuo script originale)
    # Se non hai tutte le mappe, lo script genera comunque i canali senza logo.
}

def clean_channel_name(name):
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r'\s*[\(\[][^\)\]]*[\)\]]\s*$', '', name)
    name = re.sub(r'\s+(fhd|hd|4k|uhd|uhq|full\s*hd|ultra\s*hd)$', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

# ==================== SERVER HTTP ====================
def start_server(port=PORT, directory="."):
    os.chdir(directory)
    handler = SimpleHTTPRequestHandler
    httpd = HTTPServer(("127.0.0.1", port), handler)
    print(f"✅ Server HTTP avviato su http://127.0.0.1:{port}")
    httpd.serve_forever()

# ==================== FUNZIONE PRINCIPALE ====================
async def extract_playlist(player=PLAYER, password=PASSWORD):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=CI,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        page = await context.new_page()

        # Override anti-detection
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['it-IT', 'it']});
            window._kill = function() {};
            const orig = window.setInterval;
            window.setInterval = function(fn, d) {
                if (fn.toString().includes('debugger')) return;
                return orig.call(this, fn, d);
            };
            console.clear = function() {};
            Object.defineProperty(window.location, 'hostname', {get: () => 'localhost'});
        """)

        url = f"http://127.0.0.1:{PORT}/sci.html"
        print(f"🔗 Caricamento {url}...")
        await page.goto(url, wait_until="domcontentloaded")
        print("✅ Pagina caricata")

        # Clicca sul pulsante corretto usando l'attributo onclick
        if player == "X1":
            await page.click("button[onclick*='eskeyfhd47298']")
        else:
            await page.click("button[onclick*='eskeyfhd47298-2']")
        print(f"✅ Cliccato su {player}")

        # Gestione dialogo password (se appare)
        try:
            dialog = await page.wait_for_event("dialog", timeout=3000)
            await dialog.accept(password)
            print("✅ Dialogo password accettato")
        except:
            print("⏳ Nessun dialogo password")

        # Attendi che la variabile state venga definita e popolata
        print("⏳ Attendo state...")
        try:
            await page.wait_for_function(
                "typeof state !== 'undefined' && state.ch && state.ch.length > 0",
                timeout=30000
            )
            print("✅ state trovato")
        except:
            print("❌ Timeout: state non definito o vuoto")
            await browser.close()
            return

        total = await page.evaluate("state.ch.length")
        print(f"📺 Trovati {total} canali")

        # Scorri tutti i canali per caricare URL e lic
        print("⏳ Scorro i canali per caricare URL...")
        for i in range(total):
            await page.keyboard.press("ArrowDown")
            await page.wait_for_timeout(150)
            if i % 20 == 0:
                count = await page.evaluate("""
                    () => state.ch.filter(c => c.url && c.url.trim() !== '').length
                """)
                print(f"  ✅ {count}/{total} canali caricati")

        # Estrai canali con URL
        channels = await page.evaluate("""
            () => state.ch.filter(c => c.url && c.url.trim() !== '')
        """)
        if not channels:
            print("❌ Nessun canale con URL")
            await browser.close()
            return

        print(f"✅ Trovati {len(channels)} canali con URL")

        # Genera M3U
        m3u = "#EXTM3U\n"
        for ch in channels:
            if ch.get("cat") == "GHOST_TRAP":
                continue
            if not ch.get("lic"):
                continue

            nome_originale = ch.get("name", "")
            nome_pulito = clean_channel_name(nome_originale)
            logo_url = LOGO_MAP.get(nome_pulito, "")

            url_raw = ch.get("url", "")
            if ".mpd" in url_raw:
                url_pulito = url_raw.split(".mpd")[0] + ".mpd"
            else:
                url_pulito = url_raw

            m3u += f'#EXTINF:-1 tvg-id="{ch.get("id", "")}"'
            if logo_url:
                m3u += f' tvg-logo="{logo_url}"'
            m3u += f' group-title="{ch.get("group", ch.get("cat", "Altro"))}",{nome_originale}\n'
            m3u += f'#KODIPROP:inputstream.adaptive.license_type=clearkey\n'
            m3u += f'#KODIPROP:inputstream.adaptive.license_key={ch.get("lic")}\n'
            m3u += url_pulito + "\n\n"

        with open(OUTPUT, "w", encoding="utf-8") as f:
            f.write(m3u)

        print(f"✅ Playlist salvata: {OUTPUT} ({len([c for c in channels if c.get('lic')])} canali con lic)")
        await browser.close()

# ==================== AVVIO ====================
if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, args=(PORT, "."), daemon=True)
    server_thread.start()
    time.sleep(3)
    asyncio.run(extract_playlist())
    print("✅ Estrazione completata.")
    # Il server è daemon, quindi termina con il processo