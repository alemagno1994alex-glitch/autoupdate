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
PLAYER = os.environ.get("PLAYER", "X1")   # "X1" o "X2"
PORT = 8000
OUTPUT = "sky.m3u"
CI = os.environ.get("CI", "false").lower() == "true"

# ==================== LOGO MAP ====================
LOGO_MAP = {
    "sky uno": "https://pixel.disco.nowtv.it/logo/skychb_477_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky uno +": "https://pixel.disco.nowtv.it/logo/skychb_477_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky atlantic": "https://pixel.disco.nowtv.it/logo/skychb_226_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky serie": "https://pixel.disco.nowtv.it/logo/skychb_684_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "comedy central": "https://pixel.disco.nowtv.it/logo/skychb_404_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "mtv": "https://pixel.disco.nowtv.it/logo/skychb_763_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky tg24": "https://pixel.disco.nowtv.it/logo/skychb_519_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport 24": "https://pixel.disco.nowtv.it/logo/skychb_35_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport uno": "https://pixel.disco.nowtv.it/logo/skychb_23_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport calcio": "https://pixel.disco.nowtv.it/logo/skychb_209_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport tennis": "https://pixel.disco.nowtv.it/logo/skychb_559_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport arena": "https://pixel.disco.nowtv.it/logo/skychb_24_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport max": "https://pixel.disco.nowtv.it/logo/skychb_248_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport golf": "https://pixel.disco.nowtv.it/logo/skychb_768_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport f1": "https://pixel.disco.nowtv.it/logo/skychb_478_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport motogp": "https://pixel.disco.nowtv.it/logo/skychb_483_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport basket": "https://pixel.disco.nowtv.it/logo/skychb_764_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport legend": "https://pixel.disco.nowtv.it/logo/skychb_578_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport mix": "https://pixel.disco.nowtv.it/logo/skychb_579_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport 251": "https://pixel.disco.nowtv.it/logo/skychb_917_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport 252": "https://pixel.disco.nowtv.it/logo/skychb_951_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport 253": "https://pixel.disco.nowtv.it/logo/skychb_233_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport 254": "https://pixel.disco.nowtv.it/logo/skychb_234_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport 255": "https://pixel.disco.nowtv.it/logo/skychb_910_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport 256": "https://pixel.disco.nowtv.it/logo/skychb_912_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport 257": "https://pixel.disco.nowtv.it/logo/skychb_775_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport 258": "https://pixel.disco.nowtv.it/logo/skychb_772_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky sport 259": "https://pixel.disco.nowtv.it/logo/skychb_613_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky cinema uno": "https://pixel.disco.nowtv.it/logo/skychb_202_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky cinema collection": "https://pixel.disco.nowtv.it/logo/skychb_204_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky cinema family": "https://pixel.disco.nowtv.it/logo/skychb_255_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky cinema action": "https://pixel.disco.nowtv.it/logo/skychb_206_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky cinema suspense": "https://pixel.disco.nowtv.it/logo/skychb_47_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky cinema romance": "https://pixel.disco.nowtv.it/logo/skychb_231_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky cinema drama": "https://pixel.disco.nowtv.it/logo/skychb_769_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky cinema comedy": "https://pixel.disco.nowtv.it/logo/skychb_30_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky cinema due": "https://pixel.disco.nowtv.it/logo/skychb_564_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky cinema stories": "https://pixel.disco.nowtv.it/logo/skychb_564_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky arte": "https://pixel.disco.nowtv.it/logo/skychb_74_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky documentaries": "https://pixel.disco.nowtv.it/logo/skychb_697_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky nature": "https://pixel.disco.nowtv.it/logo/skychb_695_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky adventure": "https://pixel.disco.nowtv.it/logo/skychb_961_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "history": "https://pixel.disco.nowtv.it/logo/skychb_513_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky crime": "https://pixel.disco.nowtv.it/logo/skychb_249_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "deakids": "https://pixel.disco.nowtv.it/logo/skychb_460_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "nickjr": "https://pixel.disco.nowtv.it/logo/skychb_424_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "nickelodeon": "https://pixel.disco.nowtv.it/logo/skychb_320_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "cartoonnetwork": "https://pixel.disco.nowtv.it/logo/skychb_258_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "boomerang": "https://pixel.disco.nowtv.it/logo/skychb_367_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky collection": "https://pixel.disco.nowtv.it/logo/skychb_431_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
    "sky investigation": "https://pixel.disco.nowtv.it/logo/skychb_686_darknow/LOGO_CHANNEL_LIGHT/4000?language=it-IT&proposition=NOWOTT",
}

# ==================== PULIZIA NOME ====================
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

# ==================== EXTRACT ====================
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
        context = await browser.new_context(user_agent='xromtv.italia')
        page = await context.new_page()

        # OVERRIDE NAVIGATOR.WEBDRIVER (ANTI-BOT)
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
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
        print("✅ Pagina caricata")

        # Clicca sul bottone giusto
        if player == "X1":
            print("🔘 Clicco su X1...")
            await page.click("button[onclick*='eskeyfhd47298']")
        else:
            print("🔘 Clicco su X2...")
            await page.click("button[onclick*='eskeyfhd47298-2']")
        print("✅ Cliccato")

        # Gestione dialogo password (se presente)
        try:
            dialog = await page.wait_for_event("dialog", timeout=3000)
            await dialog.accept(password)
            print("✅ Password inserita")
        except:
            print("ℹ️ Nessun dialogo password")

        # Aspetta che state.ch sia definito e popolato (fino a 60 secondi)
        print("⏳ Attendo caricamento canali...")
        try:
            await page.wait_for_function(
                """() => {
                    return typeof state !== 'undefined' && 
                           state.ch && 
                           state.ch.length > 0 &&
                           state.ch.some(c => c.url && c.url.trim() !== '');
                }""",
                timeout=60000
            )
            print("✅ state.ch caricato!")
        except:
            print("❌ Timeout: state.ch non caricato")
            # Prova a vedere cosa c'è nella console
            logs = await page.evaluate("console.log('test')")
            await browser.close()
            return

        total = await page.evaluate("state.ch.length")
        print(f"📺 Trovati {total} canali")

        # Scorri per caricare URL e lic
        print("⏳ Caricamento URL e lic...")
        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(300)

        for i in range(total):
            await page.keyboard.press("ArrowDown")
            await page.wait_for_timeout(150)

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