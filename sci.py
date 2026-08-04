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
PLAYER = os.environ.get("PLAYER", "X1")   # da env o default X1
PORT = 8000
OUTPUT = "sky.m3u"
CI = os.environ.get("CI", "false").lower() == "true"   # True in GitHub Actions

# ==================== LOGO MAP ====================
LOGO_MAP = {
    "sky uno": "https://pixel.disco.nowtv.it/logo/skychb_477_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    # ... (inserisci qui tutte le tue mappe, non le riscrivo per brevità)
    # Assicurati che la mappa sia completa come nel tuo script originale.
}

# ==================== FUNZIONE PULIZIA NOME CANALE ====================
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
        # Avvia browser in headless se CI, altrimenti visibile
        browser = await p.chromium.launch(
            headless=CI,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',           # necessario su GitHub
                '--disable-dev-shm-usage' # utile in container
            ]
        )
        context = await browser.new_context(user_agent='xromtv.italia')
        page = await context.new_page()

        # Anti-debug
        await page.add_init_script("""
            window._kill = function() {};
            const orig = window.setInterval;
            window.setInterval = function(fn, d) {
                if (fn.toString().includes('debugger')) return;
                return orig.call(this, fn, d);
            };
            console.clear = function() {};
            Object.defineProperty(window.location, 'hostname', {get: () => 'localhost'});
            Object.defineProperty(navigator, 'userAgent', {get: () => 'xromtv.italia'});
        """)

        url = f"http://127.0.0.1:{PORT}/sci.html"
        print(f"🔗 Caricamento {url}...")
        await page.goto(url)
        await page.click(f"text={player}")
        await page.wait_for_timeout(1000)

        # Gestione dialogo password
        try:
            dialog = await page.wait_for_event("dialog", timeout=5000)
            await dialog.accept(password)
        except:
            pass

        print(f"⏳ Attendo il caricamento di {player}...")
        # Attesa più lunga per headless
        await page.wait_for_timeout(8000 if CI else 5000)

        # Ottieni totale canali
        total = await page.evaluate("state.ch.length") if await page.evaluate("typeof state !== 'undefined'") else 0
        if total == 0:
            print("❌ Nessun canale trovato.")
            await browser.close()
            return

        print(f"📺 Trovati {total} canali")

        # Scorri tutti i canali
        print("⏳ Caricamento URL e lic...")
        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(300)

        for i in range(total):
            await page.keyboard.press("ArrowDown")
            await page.wait_for_timeout(200)   # leggermente più lento per affidabilità

            if i % 20 == 0:
                count = await page.evaluate("""
                    () => state.ch.filter(c => c.url && c.url.trim() !== '').length
                """)
                print(f"  ✅ {count}/{total} canali caricati")

        # Estrai canali
        channels = await page.evaluate("""
            () => state.ch.filter(c => c.url && c.url.trim() !== '')
        """)

        if not channels:
            print("❌ Nessun canale con URL.")
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
    # Avvia il server in un thread separato
    server_thread = threading.Thread(target=start_server, args=(PORT, "."), daemon=True)
    server_thread.start()
    time.sleep(3)   # attendi che il server parta

    # Esegui l'estrazione (il player viene dalla variabile PLAYER, già settata)
    asyncio.run(extract_playlist())

    print("✅ Estrazione completata. Il server si fermerà automaticamente.")
    # Il processo termina; il thread server è daemon, quindi si chiude con il main.