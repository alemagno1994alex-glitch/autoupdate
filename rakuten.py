#!/usr/bin/env python3

# system imports
import os
import sys
from typing import List
from collections import namedtuple

# 3rd parties imports
import requests
from dotenv import load_dotenv


# Channel definition
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

# Load configuration
load_dotenv()


class Api:
    api_scheme = "https"
    api_domain = "gizmo.rakuten.tv"
    api_base_path = "/v3"
    api_base_url = "{}://{}{}".format(
        api_scheme,
        api_domain,
        api_base_path
    )

    origin = "https://rakuten.tv"
    referer = "https://rakuten.tv/"
    user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0"

    language = os.getenv('CLASSIFICATION', 'it')

    classification_id = {
        "al": 270,
        "at": 300,
        "ba": 245,
        "be": 308,
        "bg": 269,
        "ch": 319,
        "cz": 272,
        "de": 307,
        "dk": 283,
        "ee": 288,
        "es": 5,
        "fi": 284,
        "fr": 23,
        "gr": 279,
        "hr": 302,
        "ie": 41,
        "is": 287,
        "it": 36,
        "jp": 309,
        "lt": 290,
        "lu": 74,
        "me": 259,
        "mk": 275,
        "nl": 69,
        "no": 286,
        "pl": 277,
        "pt": 64,
        "ro": 268,
        "rs": 266,
        "se": 282,
        "sk": 273,
        "uk": 18,
    }

    @classmethod
    def get_all_live_channels(cls):
        """Recupera tutti i canali live gestendo la paginazione."""
        all_channels = []
        page = 1
        per_page = 100

        while True:
            path = "/live_channels"
            headers = {
                "Origin": cls.origin,
                "Referer": cls.referer,
                "User_Agent": cls.user_agent,
            }
            query = {
                "classification_id": cls.classification_id[cls.language],
                "device_identifier": "web",
                "locale": cls.language,
                "market_code": cls.language,
                "page": page,
                "per_page": per_page,
            }

            response = requests.get(
                cls.api_base_url + path,
                headers=headers,
                params=query,
            )
            data = response.json()
            channels = data.get("data", [])
            if not channels:
                break

            all_channels.extend(channels)

            # Se la risposta contiene il numero totale di canali, possiamo fermarci
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
            "User_Agent": cls.user_agent,
        }
        query = {
            "classification_id": cls.classification_id[cls.language],
            "device_identifier": "web",
            "locale": cls.language,
            "market_code": cls.language
        }

        response = requests.get(
            cls.api_base_url + path,
            headers=headers,
            params=query,
        )

        return response.json()

    @classmethod
    def get_live_streaming(cls, channel: Channel, session: requests.Session = None):
        path = "/avod/streamings"
        headers = {
            "Origin": cls.origin,
            "Referer": cls.referer,
            "User_Agent": cls.user_agent,
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
            "audio_language": channel.language_ids[0],
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

        if session:
            caller = session
        else:
            caller = requests

        response = caller.post(
            cls.api_base_url + path,
            headers=headers,
            params=query,
            json=data,
        )

        return response.json()


# methods
def map_channels_categories(api_response):
    categories = api_response.get("data", [])

    channels_categories_map = {}
    for category in categories:
        name = category.get("name", "no_category")
        channels = category.get("live_channels", [])

        for channel in channels:
            channels_categories_map[channel] = name

    return channels_categories_map


def map_channels_streams(channels: List[Channel]):
    session = requests.Session()

    ch_stream_map = {}

    for channel in channels:
        stream_url = Api.get_live_streaming(channel, session)\
            .get("data", {})\
            .get("stream_infos", [None])[0]\
            .get("url", "# no_url")

        if stream_url != "# no_url":
            head, sep, tail = stream_url.partition('.m3u8')
            stream_url = head + sep

        ch_stream_map[channel.id] = stream_url

    return ch_stream_map


def get_channels() -> List[Channel]:
    live_channels_raw = Api.get_all_live_channels()
    categories_raw = Api.get_live_channel_categories()

    cc_map = map_channels_categories(categories_raw)

    ch_list = []

    channels = live_channels_raw.get("data", [])
    for channel in channels:

        ch_id = channel.get("id", "no_id")

        ch_languages = channel.get("labels", {}).get("languages", [])
        langs = []

        for lang in ch_languages:
            langs.append(lang.get("id"))

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
    list_builder = []

    list_builder.append("#EXTM3U")

    ch_streams = map_channels_streams(channels)

    head_line_format = "#EXTINF:-1 tvg-chno={} tvg-id=\"{}\" tvg-name=\"{}\" group-title=\"{}\",{}"

    for ch in sorted(channels, key=lambda x: x.channel_number):
        head_line = head_line_format.format(
            ch.channel_number,
            ch.id,
            ch.title,
            ch.category.lower().replace(" ", "_"),
            ch.title,
        )

        list_builder.append(head_line)
        list_builder.append(ch_streams.get(ch.id, "# no_stream"))

    return "\n".join(list_builder)


def save_m3u(content: str, filename: str = "rakuten.m3u") -> None:
    """Salva il contenuto M3U in un file."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Playlist salvata in: {filename}")
    print(f"   Canali totali: {content.count('#EXTINF')}")


def main():
    # Il primo argomento (se presente) è il nome del file di output
    output_file = sys.argv[1] if len(sys.argv) > 1 else "rakuten.m3u"

    print("⏳ Recupero dei canali...")
    channels = get_channels()
    print(f"   Trovati {len(channels)} canali.")

    print("⏳ Generazione playlist e recupero stream...")
    m3u_content = generate_list(channels)

    save_m3u(m3u_content, output_file)


if __name__ == "__main__":
    sys.exit(main())