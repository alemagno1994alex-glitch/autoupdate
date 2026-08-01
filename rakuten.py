#!/usr/bin/env python3

import os
import json
import requests
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

class Api:
    api_scheme = "https"
    api_domain = "gizmo.rakuten.tv"
    api_base_path = "/v3"
    api_base_url = f"{api_scheme}://{api_domain}{api_base_path}"

    origin = "https://rakuten.tv"
    referer = "https://rakuten.tv/"
    user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

    language = os.getenv('CLASSIFICATION', 'it')

    classification_id = {
        "al": 270, "at": 300, "ba": 245, "be": 308, "bg": 269,
        "ch": 319, "cz": 272, "de": 307, "dk": 283, "ee": 288,
        "es": 5, "fi": 284, "fr": 23, "gr": 279, "hr": 302,
        "ie": 41, "is": 287, "it": 36, "jp": 309, "lt": 290,
        "lu": 74, "me": 259, "mk": 275, "nl": 69, "no": 286,
        "pl": 277, "pt": 64, "ro": 268, "rs": 266, "se": 282,
        "sk": 273, "uk": 18,
    }

print("=" * 100)
print("DEBUG - TIPI DI CANALE")
print("=" * 100)

headers = {
    "Origin": Api.origin,
    "Referer": Api.referer,
    "User-Agent": Api.user_agent,
}

query = {
    "classification_id": Api.classification_id[Api.language],
    "device_identifier": "web",
    "locale": Api.language,
    "market_code": Api.language,
    "page": 1,
    "per_page": 100,
}

try:
    response = requests.get(Api.api_base_url + "/live_channels", headers=headers, params=query, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    channels = data.get("data", [])
    print(f"\nTotali canali recuperati: {len(channels)}\n")
    
    # Categorizza per ID pattern
    vod_channels = []
    live_channels = []
    other_channels = []
    
    for ch in channels:
        ch_id = ch.get('id', '')
        title = ch.get('title', '')
        ch_type = ch.get('type', '')
        ch_number = ch.get('channel_number', -1)
        
        # Analizza l'ID per capire se è VOD
        if any(x in ch_id for x in ['rakuten-tv', 'top-', 'action-', 'comedy-', 'drama-', 'horror-', 'thriller-']):
            vod_channels.append({
                'id': ch_id,
                'title': title,
                'channel_number': ch_number,
                'has_languages': len(ch.get('labels', {}).get('languages', [])) > 0
            })
        elif ch_type == 'live_channels' and ch_number > 100:
            live_channels.append({
                'id': ch_id,
                'title': title,
                'channel_number': ch_number,
                'has_languages': len(ch.get('labels', {}).get('languages', [])) > 0
            })
        else:
            other_channels.append({
                'id': ch_id,
                'title': title,
                'channel_number': ch_number,
                'type': ch_type,
                'has_languages': len(ch.get('labels', {}).get('languages', [])) > 0
            })
    
    print("=" * 100)
    print(f"CATEGORIE VOD (senza stream live): {len(vod_channels)}")
    print("=" * 100)
    if vod_channels:
        for ch in vod_channels[:5]:
            print(f"  - {ch['id']}: {ch['title'][:40]}")
        if len(vod_channels) > 5:
            print(f"  ... e {len(vod_channels) - 5} altri")
    
    print("\n" + "=" * 100)
    print(f"CANALI LIVE REALI: {len(live_channels)}")
    print("=" * 100)
    if live_channels:
        for ch in live_channels[:10]:
            langs = "✓" if ch['has_languages'] else "✗"
            print(f"  [{ch['channel_number']:3d}] {langs} {ch['id'][:30]:30s} - {ch['title'][:40]}")
        if len(live_channels) > 10:
            print(f"  ... e {len(live_channels) - 10} altri")
    else:
        print("  NESSUN CANALE LIVE TROVATO!")
    
    print("\n" + "=" * 100)
    print(f"ALTRI CANALI: {len(other_channels)}")
    print("=" * 100)
    if other_channels:
        for ch in other_channels[:10]:
            langs = "✓" if ch['has_languages'] else "✗"
            print(f"  [{ch['channel_number']:3d}] {langs} {ch['id'][:30]:30s} - {ch['title'][:40]} (type: {ch['type']})")
        if len(other_channels) > 10:
            print(f"  ... e {len(other_channels) - 10} altri")
    
    print("\n" + "=" * 100)
    print("PROBLEMI IDENTIFICATI:")
    print("=" * 100)
    
    if len(vod_channels) > 0 and len(live_channels) == 0:
        print("\n❌ PROBLEMA CRITICO:")
        print("   Tutti i canali sono VOD, nessun canale LIVE trovato!")
        print("   Questo spiega perché nessuno ha uno stream.")
        print("\n✅ SOLUZIONE POSSIBILE:")
        print("   1. Filtrare solo i veri canali LIVE (channel_number > 900?)")
        print("   2. Oppure usare un endpoint diverso per i live channels")
        print("   3. Oppure Rakuten ha rimosso i veri live channels")
    elif len(live_channels) > 0:
        print(f"\n✓ Trovati {len(live_channels)} canali LIVE potenziali")
        print("   Dovrebbero avere stream disponibili")
    
    # Mostra un canale live completo per debug
    if live_channels:
        print("\n" + "=" * 100)
        print("ESEMPIO CANALE LIVE (raw JSON):")
        print("=" * 100)
        for ch in channels:
            if any(c['id'] == ch.get('id') for c in live_channels):
                print(json.dumps(ch, indent=2, ensure_ascii=False)[:1000])
                break

except Exception as e:
    print(f"❌ Errore: {e}")
    import traceback
    traceback.print_exc()