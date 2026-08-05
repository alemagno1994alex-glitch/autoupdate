import json
import os
import requests
import subprocess

GIST_TOKEN = os.getenv('GIST_TOKEN')
GIST_ID = os.getenv('GIST_ID', '').strip() or None

if not GIST_TOKEN:
    print("❌ ERRORE: GIST_TOKEN non è configurato!")
    exit(1)

# Leggi il file della playlist
with open('tg_regionali.m3u', 'r') as f:
    file_content = f.read()

headers = {
    "Authorization": f"token {GIST_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

if not GIST_ID:
    # Crea nuovo gist
    print("📦 Creazione di un nuovo gist privato...")
    data = {
        "description": "Playlist TGR regioni (aggiornata automaticamente)",
        "public": False,
        "files": {
            "tg_regionali.m3u": {
                "content": file_content
            }
        }
    }
    
    response = requests.post("https://api.github.com/gists", json=data, headers=headers)
    
    if response.status_code == 201:
        gist_id = response.json()['id']
        print(f"✅ Nuovo gist creato: {gist_id}")
        print(f"🔗 URL: https://gist.github.com/{gist_id}")
        print(f"⚠️  Aggiungi come secret 'GIST_ID': {gist_id}")
    else:
        print(f"❌ Errore: {response.status_code}")
        print(response.json())
        exit(1)
else:
    # Aggiorna gist esistente
    print(f"🔄 Aggiornamento gist ({GIST_ID})...")
    data = {
        "files": {
            "tg_regionali.m3u": {
                "content": file_content
            }
        }
    }
    
    response = requests.patch(f"https://api.github.com/gists/{GIST_ID}", json=data, headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Gist aggiornato: https://gist.github.com/{GIST_ID}")
    else:
        print(f"❌ Errore: {response.status_code}")
        print(response.json())
        exit(1)