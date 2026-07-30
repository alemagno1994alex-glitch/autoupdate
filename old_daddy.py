#!/usr/bin/env python3
"""
M3U Generator – DLHD → Gist
--------------------------------------------------
Questo script scarica il palinsesto da dlhd.st, filtra gli eventi di oggi,
genera un file M3U e lo carica su un Gist di GitHub tramite API.

Le credenziali vanno fornite tramite variabili d'ambiente:
    GITHUB_TOKEN  : token personale con permesso gist
    GIST_ID       : ID del Gist di destinazione
    (opzionali) GIST_FILENAME, OFFSET_HOURS
"""

import re
import sys
import os
from datetime import datetime, timedelta

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Dipendenze mancanti. Installa con:")
    print("    pip install requests beautifulsoup4")
    sys.exit(1)

# ============================================================
#  CONFIGURAZIONE (solo da variabili d'ambiente)
# ============================================================

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GIST_ID = os.environ.get("GIST_ID")
GIST_FILENAME = os.environ.get("GIST_FILENAME", "daddyeventi.m3u")
OFFSET_HOURS = int(os.environ.get("OFFSET_HOURS", 2))
BASE_URL = "https://dlhd.st/"
PROXY_URL = "https://proxy.alemagno1994alex.workers.dev/?url="
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ============================================================
#  FUNZIONI (invariate)
# ============================================================

def fetch_direct(url):
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text

def fetch_via_proxy(url):
    proxy_full = PROXY_URL + requests.utils.quote(url, safe="")
    resp = requests.get(proxy_full, timeout=30)
    resp.raise_for_status()
    return resp.text

def fetch_page(url):
    try:
        return fetch_direct(url)
    except Exception as e:
        print(f"⚠️  Direct fetch fallito: {e}")
        print("   Tentativo con proxy CORS...")
        return fetch_via_proxy(url)

def parse_day_title(text):
    date_part = text.split(" - ")[0]
    match = re.match(r"(\w+)\s+(\d+)(?:st|nd|rd|th)\s+(\w+)\s+(\d{4})", date_part)
    if not match:
        return None
    day = int(match.group(2))
    month_name = match.group(3)
    year = int(match.group(4))
    month_map = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }
    month = month_map.get(month_name)
    if month is None:
        return None
    return datetime(year, month, day).date()

def adjust_time(date_obj, time_str, offset_hours):
    try:
        h, m = map(int, time_str.split(":"))
    except ValueError:
        return time_str
    dt = datetime.combine(date_obj, datetime.min.time()) + timedelta(hours=h, minutes=m)
    dt += timedelta(hours=offset_hours)
    return dt.strftime("%H:%M")

def format_date_short(date_obj):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{date_obj.day} {months[date_obj.month - 1]} {date_obj.year}"

def generate_m3u(html):
    soup = BeautifulSoup(html, "html.parser")
    day_elements = soup.select(".schedule__day")
    if not day_elements:
        print("❌ Nessun giorno trovato. La pagina potrebbe non essere il palinsesto.")
        return None

    today = datetime.now().date()
    all_events = []

    for day_el in day_elements:
        title_el = day_el.select_one(".schedule__dayTitle")
        if not title_el:
            continue
        day_text = title_el.get_text(strip=True)
        date_obj = parse_day_title(day_text)
        if not date_obj:
            continue
        is_today = (date_obj == today)

        categories = day_el.select(".schedule__category")
        for cat in categories:
            cat_title_el = cat.select_one(".card__meta")
            if not cat_title_el:
                continue
            category = cat_title_el.get_text(strip=True)

            event_headers = cat.select(".schedule__event")
            for ev in event_headers:
                time_el = ev.select_one(".schedule__time")
                title_el = ev.select_one(".schedule__eventTitle")
                channel_links = ev.select(".schedule__channels a")
                if not time_el or not title_el or not channel_links:
                    continue

                time_str = time_el.get_text(strip=True)
                title = title_el.get_text(strip=True)

                streams = []
                for a in channel_links:
                    href = a.get("href")
                    if not href:
                        continue
                    if href.startswith(("http://", "https://")):
                        url = href
                    elif href.startswith("/"):
                        url = "https://dlhd.st" + href
                    else:
                        url = "https://dlhd.st/" + href
                    channel_name = a.get("title") or a.get_text(strip=True) or "Stream"
                    streams.append({"url": url, "channel_name": channel_name})

                if not streams:
                    continue

                all_events.append({
                    "day": date_obj,
                    "day_text": day_text,
                    "is_today": is_today,
                    "category": category,
                    "time": time_str,
                    "title": title,
                    "streams": streams
                })

    selected = [e for e in all_events if e["is_today"]]
    if not selected:
        print("⚠️  Nessun evento per oggi. Verranno inclusi tutti gli eventi disponibili.")
        selected = all_events

    if not selected:
        print("❌ Nessun evento valido trovato.")
        return None

    lines = ["#EXTM3U"]
    total_events = 0
    total_streams = 0

    for ev in selected:
        category = ev["category"]
        event_title = ev["title"]
        for stream in ev["streams"]:
            adjusted_time = adjust_time(ev["day"], ev["time"], OFFSET_HOURS)
            day_short = format_date_short(ev["day"])
            display_title = f"{day_short} {adjusted_time} – {event_title} – {stream['channel_name']}"
            lines.append(f'#EXTINF:-1 group-title="{category}",{display_title}')
            lines.append(stream["url"])
            total_streams += 1
        total_events += 1

    if len(lines) <= 1:
        print("❌ Nessuno stream valido trovato.")
        return None

    print(f"✅ Eventi: {total_events} · Stream: {total_streams}")
    return "\n".join(lines)

def upload_to_gist(content, token, gist_id, filename):
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "files": {
            filename: {
                "content": content
            }
        }
    }

    resp = requests.patch(url, headers=headers, json=payload, timeout=30)
    if not resp.ok:
        try:
            err_data = resp.json()
            err_msg = err_data.get("message", resp.text)
        except Exception:
            err_msg = resp.text
        raise Exception(f"GitHub API {resp.status_code}: {resp.reason} - {err_msg}")

    data = resp.json()
    return data.get("html_url", f"https://gist.github.com/{gist_id}")

def main():
    print("📺 M3U Generator – DLHD → Gist")
    print("=" * 40)

    if not GITHUB_TOKEN:
        print("❌ Errore: GITHUB_TOKEN non impostato. Imposta la variabile d'ambiente.")
        sys.exit(1)
    if not GIST_ID:
        print("❌ Errore: GIST_ID non impostato. Imposta la variabile d'ambiente.")
        sys.exit(1)

    print(f"🌐 Download da {BASE_URL} ...")
    try:
        html = fetch_page(BASE_URL)
        print("✅ Pagina scaricata.")
    except Exception as e:
        print(f"❌ Errore nel download: {e}")
        sys.exit(1)

    print("📋 Generazione M3U...")
    m3u = generate_m3u(html)
    if not m3u:
        print("❌ Impossibile generare il M3U.")
        sys.exit(1)

    print(f"📤 Invio a Gist (ID: {GIST_ID}, file: {GIST_FILENAME})...")
    try:
        gist_url = upload_to_gist(m3u, GITHUB_TOKEN, GIST_ID, GIST_FILENAME)
        print(f"✅ File caricato con successo!")
        print(f"🔗 {gist_url}")
    except Exception as e:
        print(f"❌ Errore durante l'upload: {e}")
        sys.exit(1)

    print("\n✨ Operazione completata.")

if __name__ == "__main__":
    main()