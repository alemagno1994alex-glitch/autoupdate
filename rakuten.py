#!/usr/bin/env python3

import os
import sys
import time
import logging
from typing import List
from collections import namedtuple

import requests
from dotenv import load_dotenv

load_dotenv()

# Configurare logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0"

    language = os.getenv('CLASSIFICATION', 'it')
    
    # Timeout più lungo per GitHub Actions
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2

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
    def _make_request(cls, method, path, headers=None, params=None, json=None):
        """Effettua una richiesta HTTP con retry logic"""
        url = cls.api_base_url + path
        
        if headers is None:
            headers = {
                "Origin": cls.origin,
                "Referer": cls.referer,
                "User-Agent": cls.user_agent,
            }
        
        for attempt in range(cls.MAX_RETRIES):
            try:
                if method == "GET":
                    response = requests.get(
                        url, 
                        headers=headers, 
                        params=params,
                        timeout=cls.REQUEST_TIMEOUT
                    )
                elif method == "POST":
                    response = requests.post(
                        url,
                        headers=headers,
                        params=params,
                        json=json,
                        timeout=cls.REQUEST_TIMEOUT
                    )
                else:
                    raise ValueError(f"Metodo HTTP non supportato: {method}")
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout tentativo {attempt + 1}/{cls.MAX_RETRIES} per {path}")
                if attempt < cls.MAX_RETRIES - 1:
                    time.sleep(cls.RETRY_DELAY)
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Errore connessione tentativo {attempt + 1}/{cls.MAX_RETRIES}: {e}")
                if attempt < cls.MAX_RETRIES - 1:
                    time.sleep(cls.RETRY_DELAY)
            except requests.exceptions.HTTPError as e:
                logger.error(f"Errore HTTP {response.status_code}: {e}")
                if response.status_code == 429:  # Rate limited
                    wait_time = int(response.headers.get('Retry-After', cls.RETRY_DELAY))
                    logger.warning(f"Rate limited. Attesa {wait_time} secondi...")
                    if attempt < cls.MAX_RETRIES - 1:
                        time.sleep(wait_time)
                else:
                    raise
        
        raise Exception(f"Impossibile connettersi a {path} dopo {cls.MAX_RETRIES} tentativi")

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
            try:
                response = cls._make_request("GET", path, headers=headers, params=query)
                data = response.json()
                channels = data.get("data", [])
                if not channels:
                    break
                all_channels.extend(channels)
                total = data.get("total", 0)
                if total and len(all_channels) >= total:
                    break
                page += 1
                # Piccolo delay per evitare rate limiting
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Errore nel recupero dei canali: {e}")
                break
        
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
        try:
            response = cls._make_request("GET", path, headers=headers, params=query)
            return response.json()
        except Exception as e:
            logger.error(f"Errore nel recupero delle categorie: {e}")
            return {"data": []}

    @classmethod
    def get_live_streaming(cls, channel: Channel, session: requests.Session = None):
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
        data = {
            "audio_language": channel.language_ids[0] if channel.language_ids else "MIS",
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
            if session:
                response = session.post(
                    cls.api_base_url + path,
                    headers=headers,
                    params=query,
                    json=data,
                    timeout=cls.REQUEST_TIMEOUT
                )
            else:
                response = cls._make_request("POST", path, headers=headers, params=query, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Errore nel recupero dello stream per {channel.title}: {e}")
            return {"data": {}}

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
    session.headers.update({
        "Origin": Api.origin,
        "Referer": Api.referer,
        "User-Agent": Api.user_agent,
    })
    
    ch_stream_map = {}
    total = len(channels)
    
    for idx, channel in enumerate(channels, 1):
        logger.info(f"Recupero stream {idx}/{total}: {channel.title}")
        try:
            response = Api.get_live_streaming(channel, session)
            stream_url = response.get("data", {}).get("stream_infos", [None])[0]
            
            if stream_url and stream_url.get("url"):
                url = stream_url.get("url", "")
                # Estrai solo l'URL base (fino a .m3u8)
                head, sep, _ = url.partition('.m3u8')
                stream_url = head + sep
                ch_stream_map[channel.id] = stream_url
                logger.debug(f"✓ Stream trovato per {channel.title}")
            else:
                ch_stream_map[channel.id] = "# no_stream"
                logger.warning(f"✗ Nessun stream per {channel.title}")
                
        except Exception as e:
            ch_stream_map[channel.id] = "# no_stream"
            logger.error(f"✗ Errore per {channel.title}: {str(e)}")
        
        # Delay tra le richieste per evitare rate limiting
        time.sleep(0.3)
    
    session.close()
    return ch_stream_map

def get_channels() -> List[Channel]:
    logger.info("Recupero canali live...")
    live_channels_raw = Api.get_all_live_channels()
    
    logger.info("Recupero categorie...")
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
    logger.info("Recupero URL degli stream...")
    ch_streams = map_channels_streams(channels)
    
    head_line_format = '#EXTINF:-1 tvg-chno="{}" tvg-id="{}" tvg-name="{}" group-title="{}",{}'
    
    for ch in sorted(channels, key=lambda x: x.channel_number):
        group = ch.category.lower().replace(" ", "_")
        lines.append(head_line_format.format(ch.channel_number, ch.id, ch.title, group, ch.title))
        lines.append(ch_streams.get(ch.id, "# no_stream"))
    
    return "\n".join(lines)

def main():
    output_file = sys.argv[1] if len(sys.argv) > 1 else "rakuten.m3u"
    
    try:
        logger.info("⏳ Recupero dei canali...")
        channels = get_channels()
        logger.info(f"✓ Trovati {len(channels)} canali")
        
        logger.info("⏳ Generazione playlist e recupero stream...")
        m3u_content = generate_list(channels)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(m3u_content)
        
        stream_count = m3u_content.count('#EXTINF')
        logger.info(f"✅ Playlist salvata in: {output_file}")
        logger.info(f"   Canali totali: {stream_count}")
        
        # Conta gli stream effettivi
        no_stream_count = m3u_content.count("# no_stream")
        valid_streams = stream_count - no_stream_count
        logger.info(f"   Stream validi: {valid_streams}/{stream_count}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Errore critico: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
