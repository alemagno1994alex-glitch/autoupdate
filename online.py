#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import requests
from datetime import datetime, timedelta
from typing import List, Dict

# ========================= CONFIGURAZIONE DA ENV =========================
SOURCE_URL = os.getenv("SOURCE_URL", "https://sportsonline.sl/prog.txt")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GIST_FILE = os.getenv("GIST_FILE", "sportsonline.m3u")
GIST_DESCRIPTION = os.getenv("GIST_DESCRIPTION", "SPORTSONLINE M3U — ")
PUBLIC_GIST = os.getenv("PUBLIC_GIST", "false").lower() == "true"   # default privato

# Controlli obbligatori
if not GITHUB_TOKEN:
    sys.exit("❌ GITHUB_TOKEN non impostato")
if not GIST_ID:
    sys.exit("❌ GIST_ID non impostato")

# ========================= COSTANTI (come nel JS originale) =========================
WEEKDAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
DAY_IT = {
    "MONDAY": "LUNEDÌ", "TUESDAY": "MARTEDÌ", "WEDNESDAY": "MERCOLEDÌ",
    "THURSDAY": "GIOVEDÌ", "FRIDAY": "VENERDÌ", "SATURDAY": "SABATO", "SUNDAY": "DOMENICA"
}
IT_MONTHS = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
             "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

LOGO = {
    "default": "https://raw.githubusercontent.com/nero081/loghi/main/loghi/default.png",
    "hd1":  "https://raw.githubusercontent.com/nero081/loghi/main/loghi/inglese.png",
    "hd2":  "https://raw.githubusercontent.com/nero081/loghi/main/loghi/inglese.png",
    "hd3":  "https://raw.githubusercontent.com/nero081/loghi/main/loghi/germania.png",
    "hd6":  "https://raw.githubusercontent.com/nero081/loghi/main/loghi/spagna.png",
    "hd7":  "https://raw.githubusercontent.com/nero081/loghi/main/loghi/play.png",
    "hd8":  "https://raw.githubusercontent.com/nero081/loghi/main/loghi/play.png",
    "hd9":  "https://raw.githubusercontent.com/nero081/loghi/main/loghi/turco_inglese.png",
    "hd11": "https://raw.githubusercontent.com/nero081/loghi/main/loghi/araboinglesespagna.png",
    "br":   "https://raw.githubusercontent.com/nero081/loghi/main/loghi/brasile.png"
}

# ========================= UTILITY (identiche al JS) =========================
def pad(n: int) -> str:
    return str(n).zfill(2)

def adjust_time(t: str) -> str:
    m = re.match(r'^(\d{2}):(\d{2})$', t)
    if not m:
        return t
    h = (int(m.group(1)) + 1) % 24
    return f"{pad(h)}:{m.group(2)}"

def format_event(s: str) -> str:
    return s.replace(" x ", " vs ").replace(" v ", " vs ").replace(" @ ", " vs ")

def to_http(url: str) -> str:
    return url.replace("https://", "http://")

def get_ch_key(url: str) -> str:
    m = re.search(r'(hd\d+|br\d+)\.php', url, re.IGNORECASE)
    if not m:
        return "def"
    k = m.group(1).lower()
    if k.startswith("br"):
        return "br"
    if k in ("hd1", "hd2"):
        return "hd1"
    return k

def get_logo(url: str) -> str:
    k = get_ch_key(url)
    if k == "br":
        return LOGO["br"]
    return LOGO.get(k, LOGO["default"])

def get_label(url: str) -> str:
    m = re.search(r'(hd\d+|br\d+)\.php', url, re.IGNORECASE)
    return m.group(1).upper() if m else "STREAM"

def correggi_giorni(lines: List[str]) -> List[str]:
    out = []
    last_idx = -1
    for line in lines:
        s = line.strip()
        u = s.upper()
        if u in WEEKDAYS:
            idx = WEEKDAYS.index(u)
            if idx <= last_idx:
                idx = last_idx + 1
                if idx >= len(WEEKDAYS):
                    idx = idx % len(WEEKDAYS)
            out.append(WEEKDAYS[idx])
            last_idx = idx
        else:
            out.append(s)
    return out

def get_date_for_day(day_name: str, last_date: datetime) -> datetime:
    target = WEEKDAYS.index(day_name)
    diff = target - last_date.weekday()   # Python: 0=Mon
    if diff <= 0:
        diff += 7
    return last_date + timedelta(days=diff)

# ========================= PARSER =========================
def parse_prog(text: str) -> List[Dict]:
    lines = correggi_giorni(text.splitlines())
    days = []
    cur_day = None
    cur_events = []
    last_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    pending_date = None

    for line in lines:
        u = line.strip().upper()
        if u in WEEKDAYS:
            if cur_day is not None and cur_events:
                days.append({
                    'day': DAY_IT[cur_day],
                    'date': pending_date or last_date,
                    'events': cur_events
                })
            new_date = get_date_for_day(u, last_date)
            last_date = new_date
            cur_day = u
            cur_events = []
            pending_date = new_date
            continue

        m = re.match(r'^(\d{2}:\d{2})\s+(.*?)\s+\|\s+(.+)$', line.strip())
        if m:
            time = adjust_time(m.group(1))
            name = format_event(m.group(2))
            url = to_http(m.group(3).strip())
            cur_events.append({
                'time': time,
                'name': name,
                'url': url,
                'chKey': get_ch_key(url),
                'logo': get_logo(url),
                'label': get_label(url)
            })

    if cur_day is not None and cur_events:
        days.append({
            'day': DAY_IT[cur_day],
            'date': pending_date or last_date,
            'events': cur_events
        })

    # Assegna date mancanti
    d = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    for block in days:
        if block['date'] is None:
            for en, it in DAY_IT.items():
                if it == block['day']:
                    block['date'] = get_date_for_day(en, d)
                    d = block['date']
                    break
        else:
            d = block['date']

    return days

def build_m3u(parsed_days: List[Dict]) -> str:
    lines = ["#EXTM3U"]
    for block in parsed_days:
        for ev in block['events']:
            lines.append(f'#EXTINF:-1 group-title="{block["day"]}" tvg-logo="{ev["logo"]}",{ev["time"]} {ev["name"]}')
            lines.append(ev["url"])
            lines.append("")
    return "\n".join(lines)

# ========================= GIST UPDATE =========================
def update_gist(content: str, gist_id: str, token: str, filename: str, description: str, public: bool = False) -> dict:
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    payload = {
        "description": description,
        "public": public,
        "files": {
            filename: {"content": content}
        }
    }
    resp = requests.patch(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()

# ========================= MAIN =========================
def main():
    print("🔄 Download di prog.txt...")
    try:
        resp = requests.get(SOURCE_URL, timeout=30)
        resp.raise_for_status()
        text = resp.text
    except Exception as e:
        sys.exit(f"❌ Errore nel download: {e}")

    print("🔄 Parsing del file...")
    try:
        parsed = parse_prog(text)
    except Exception as e:
        sys.exit(f"❌ Errore nel parsing: {e}")

    if not parsed:
        sys.exit("❌ Nessun evento trovato.")

    total_events = sum(len(block['events']) for block in parsed)
    print(f"✅ Trovati {total_events} eventi in {len(parsed)} giorni.")

    print("🔄 Generazione M3U...")
    m3u_content = build_m3u(parsed)
    print(f"📦 Contenuto M3U: {len(m3u_content)} caratteri.")

    print("🔄 Aggiornamento Gist...")
    try:
        desc = GIST_DESCRIPTION + datetime.now().strftime("%Y-%m-%d %H:%M")
        result = update_gist(
            content=m3u_content,
            gist_id=GIST_ID,
            token=GITHUB_TOKEN,
            filename=GIST_FILE,
            description=desc,
            public=PUBLIC_GIST
        )
        raw_url = result['files'][GIST_FILE]['raw_url']
        html_url = result['html_url']
        print(f"✅ Gist aggiornato con successo!")
        print(f"   HTML: {html_url}")
        print(f"   RAW : {raw_url}")
    except Exception as e:
        sys.exit(f"❌ Errore durante l'aggiornamento: {e}")

if __name__ == "__main__":
    main()