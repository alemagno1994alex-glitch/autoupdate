#!/usr/bin/env python3
import os
import sys
import json
import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_URL = "https://test34344.herokuapp.com/filter.php?numTest=A1A211"
DEFAULT_OUTPUT = "tg_regionali.m3u"

def clean_title(title):
    """Rimuove i tag [COLOR...] dal titolo."""
    return re.sub(r'\[COLOR[^\]]*\]|\[/COLOR\]', '', title).strip()

def fetch_json(url):
    try:
        resp = requests.get(url, timeout=15, verify=False)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Errore nel recuperare {url}: {e}", file=sys.stderr)
        return None

def generate_playlist(main_url, output_file):
    main_data = fetch_json(main_url)
    if not main_data or "items" not in main_data:
        print("Impossibile ottenere l'elenco delle regioni.", file=sys.stderr)
        return False

    items = main_data["items"]
    m3u_lines = ["#EXTM3U"]
    count = 0

    for item in items:
        title = clean_title(item.get("title", "Senza titolo"))
        external_url = item.get("externallink")
        if not external_url:
            continue

        region_data = fetch_json(external_url)
        if not region_data or "items" not in region_data or not region_data["items"]:
            print(f"Nessun flusso trovato per {title}", file=sys.stderr)
            continue

        stream_item = region_data["items"][0]
        stream_url = stream_item.get("link")
        if not stream_url:
            print(f"Campo 'link' mancante per {title}", file=sys.stderr)
            continue

        m3u_lines.append(f'#EXTINF:-1,{title}')
        m3u_lines.append(stream_url)
        count += 1

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))

    print(f"Playlist generata: {output_file} ({count} canali)")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Genera playlist M3U per TGR regioni")
    parser.add_argument("--url", default=os.environ.get("MAIN_URL", DEFAULT_URL),
                        help="URL principale del filtro")
    parser.add_argument("--output", default=os.environ.get("OUTPUT_FILE", DEFAULT_OUTPUT),
                        help="Nome del file M3U in output")
    args = parser.parse_args()

    success = generate_playlist(args.url, args.output)
    sys.exit(0 if success else 1)