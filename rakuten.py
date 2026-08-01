#!/usr/bin/env python3

import os
import sys
import time
from typing import List
from collections import namedtuple

import requests
from dotenv import load_dotenv

load_dotenv()

CHANNEL_FIELDS = [
    "id",
    "numerical_id",
    "title",
    "type",
    "channel_number",
    "category",
    "language_ids",
]

Channel = namedtuple("Channel", CHANNEL_FIELDS)

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

    @classmethod
    def get_all_live_channels(cls):
        all_channels = []
        page = 1
        per_page = 100
        while True:
            path = "/live_channels"
            headers = {
                "Origin": cls.origin,
                "Referer": cls.referer,
                "User-Agent": cls.user_agent,
            }
            query = {
                "classification_id": cls.classification_id[cls.language],
                "device_identifier": "web",
                "locale": cls.language,
                "market_code": cls.language,
                "page": page,
                "per_page": per_page,
            }
            response = requests.get(cls.api_base_url + path, headers=headers, params=query, timeout=30)
            response.raise_for_status()
            data = response.json()
            channels = data.get("data", [])
            if not channels:
                break
            all_channels.extend(channels)
            total = data.get("total", 0)
            if total and len(all_channels) >= total:
                break
            page += 1
        return {"data": all_channels}

    @classmethod
    def get_live_channel_categories(cls):
        path = "/live_channel_categories"
        headers = {
            "Origin": cls.origin,
            "Referer": cls.referer,
            "User-Agent": cls.user_agent,
        }
        query = {
            "classification_id": cls.classification_id[cls.language],
            "device_identifier": "web",
            "locale": cls.language,
            "market_code": cls.language
        }
        response = requests.get(cls.api_base_url + path, headers=headers, params=query, timeout=30)
        response.raise_for_status()
        return response.json()

    @classmethod
    def get_live_streaming(cls, channel: Channel, session: requests.Session = None):
        """
        Recupera lo stream di un canale.
        
        Se ritorna 422, prova con audio_language diverso.
        """
        path = "/avod/streamings"
        headers = {
            "Origin": cls.origin,
            "Referer": cls.referer,
            "User-Agent": cls.user_agent,
        }
        query = {
            "classification_id": cls.classification_id[cls.language],
            "device_identifier": "web",
            "device_stream_audio_quality": "2.0",
            "device_stream_hdr_type": "NONE",
            "device_stream_video_quality": "FHD",
            "disable_dash_legacy_packages": False,
            "locale": cls.language,
            "market_code": cls.language
        }
        
        # Prova prima con la lingua del canale
        audio_languages_to_try = []
        
        if channel.language_ids:
            audio_languages_to_try.extend(channel.language_ids)
        
        # Aggiungi fallback
        audio_languages_to_try.extend(["MIS", "ENG", "ITA"])
        
        # Rimuovi duplicati mantenendo l'ordine
        audio_languages_to_try = list(dict.fromkeys(audio_languages_to_try))
        
        last_error = None
        
        for audio_lang in audio_languages_to_try:
            data = {
                "audio_language": audio_lang,
                "audio_quality": "2.0",
                "classification_id": cls.classification_id[cls.language],
                "content_id": channel.id,
                "content_type": "live_channels",
                "device_serial": "not implemented",
                "player": "web:HLS-NONE:NONE",
                "strict_video_quality": False,
                "subtitle_language": "MIS",
                "video_type": "stream"
            }
            
            try:
                caller = session if session else requests
                response = caller.post(
                    cls.api_base_url + path,
                    headers=headers,
                    params=query,
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 422:
                    # Prova la prossima lingua
                    last_error = response
                    continue
                else:
                    response.raise_for_status()
                    
            except Exception as e:
                last_error = e
                continue
        
        # Se arriviamo qui, nessuna richiesta è andata a buon fine
        if last_error:
            if isinstance(last_error, requests.Response):
                raise requests.HTTPError(f"422 on all audio languages", response=last_error)
            else:
                raise last_error
        
        raise Exception("No audio language worked")

def map_channels_categories(api_response):
    categories = api_response.get("data", [])
    channels_categories_map = {}
    for category in categories:
        name = category.get("name", "no_category")
        for channel in category.get("live_channels", []):
            channels_categories_map[channel] = name
    return channels_categories_map

def map_channels_streams(channels: List[Channel]):
    session = requests.Session()
    ch_stream_map = {}
    total = len(channels)
    
    success_count = 0
    error_count = 0
    
    for idx, channel in enumerate(channels, 1):
        try:
            stream_response = Api.get_live_streaming(channel, session)
            stream_info = stream_response.get("data", {}).get("stream_infos", [None])[0]
            
            if stream_info and stream_info.get("url"):
                url = stream_info.get("url", "")
                head, sep, _ = url.partition('.m3u8')
                stream_url = head + sep
                ch_stream_map[channel.id] = stream_url
                success_count += 1
            else:
                ch_stream_map[channel.id] = "# no_stream"
                error_count += 1
        except Exception as e:
            ch_stream_map[channel.id] = "# no_stream"
            error_count += 1
        
        # Mostra progressione ogni 10 canali
        if idx % 10 == 0 or idx == total:
            print(f"   [{idx}/{total}] OK: {success_count}, Errori: {error_count}")
        
        # Piccolo delay per evitare rate limiting
        time.sleep(0.1)
    
    session.close()
    print(f"   ✅ Completato: {success_count}/{total} stream recuperati")
    return ch_stream_map

def get_channels() -> List[Channel]:
    live_channels_raw = Api.get_all_live_channels()
    categories_raw = Api.get_live_channel_categories()
    cc_map = map_channels_categories(categories_raw)
    ch_list = []
    for channel in live_channels_raw.get("data", []):
        ch_id = channel.get("id", "no_id")
        langs = [lang.get("id") for lang in channel.get("labels", {}).get("languages", []) if lang.get("id")]
        ch = Channel(
            id=ch_id,
            numerical_id=int(channel.get("numerical_id", -1)),
            title=channel.get("title", "no_title"),
            type=channel.get("type", "no_type"),
            channel_number=int(channel.get("channel_number", -1)),
            category=cc_map.get(ch_id, "no_category"),
            language_ids=langs,
        )
        ch_list.append(ch)
    return ch_list

def generate_list(channels: List[Channel]) -> str:
    lines = ["#EXTM3U"]
    ch_streams = map_channels_streams(channels)
    head_line_format = '#EXTINF:-1 tvg-chno="{}" tvg-id="{}" tvg-name="{}" group-title="{}",{}'
    for ch in sorted(channels, key=lambda x: x.channel_number):
        group = ch.category.lower().replace(" ", "_")
        lines.append(head_line_format.format(ch.channel_number, ch.id, ch.title, group, ch.title))
        lines.append(ch_streams.get(ch.id, "# no_stream"))
    return "\n".join(lines)

def main():
    output_file = sys.argv[1] if len(sys.argv) > 1 else "rakuten.m3u"
    print("⏳ Recupero dei canali...")
    channels = get_channels()
    print(f"   ✓ Trovati {len(channels)} canali")
    print("⏳ Generazione playlist e recupero stream...")
    m3u_content = generate_list(channels)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    
    total = m3u_content.count('#EXTINF')
    valid = total - m3u_content.count('# no_stream')
    
    print(f"✅ Playlist salvata in: {output_file}")
    print(f"   Canali totali: {total}")
    print(f"   Stream validi: {valid}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
