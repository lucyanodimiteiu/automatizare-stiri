import feedparser
import requests
import os
import time
import re
import json

# Configurare API
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"
CONFIG_FILE = "config_bot.json"

DEFAULT_CONFIG = {
    "rss_urls": [
        "https://www.digi24.ro/rss/stiri/economie", 
        "https://www.digi24.ro/rss/stiri/sci-tech",
        "http://feeds.bbci.co.uk/news/world/rss.xml"
    ],
    "keywords": ["economie", "finante", "tech", "bursa", "profit"],
    "limit_chars": 800
}

def incarca_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try: return json.load(f)
            except: return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def salveaza_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def verifica_comenzi_telegram(config):
    # Folosim getUpdates cu un timeout mic pentru a prinde mesajele "offline"
    url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
    try:
        res = requests.get(url, timeout=20).json()
        if res.get("ok"):
            for result in res.get("result", []):
                msg = result.get("message", {})
                text = msg.get("text", "")
                user_id = msg.get("chat", {}).get("id")

                if text == "/lista_config":
                    mesaj = f"📊 CONFIGURAȚIE:\n\nSurse: {len(config['rss_urls'])}\nKeywords: {', '.join(config['keywords'])}"
                    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": user_id, "text": mesaj})

                elif text.startswith("/adauga_sursa"):
                    noua_sursa = text.replace("/adauga_sursa ", "").strip()
                    if noua_sursa not in config["rss_urls"]:
                        config["rss_urls"].append(noua_sursa)
                        salveaza_config(config)
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": user_id, "text": f"✅ Sursă adăugată!"})

                elif text.startswith("/adauga_keyword"):
                    cuvant = text.replace("/adauga_keyword ", "").strip().lower()
                    if cuvant not in config["keywords"]:
                        config["keywords"].append(cuvant)
                        salveaza_config(config)
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": user_id, "text": f"✅ Keyword adăugat!"})
    except: pass
    return config

def cere_deepseek(titlu, rezumat, limit):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    prompt = f"Ești jurnalist economic. Rezumă în română (max {limit} caractere, Bold, Emoji, Fără surse): {titlu} - {rezumat}"
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.5}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=60)
        return res.json()['choices'][0]['message']['content']
    except: return None

def extrage_imagine(entry):
    if 'media_content' in entry: return entry.media_content[0]['url']
    if 'enclosures' in entry and len(entry.enclosures) > 0: return entry.enclosures[0]['href']
    img_match = re.search(r'<img [^>]*src="([^"]+)"', entry.get('summary', ''))
    return img_match.group(1) if img_match else None

def posteaza_telegram(text, img):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/"
    if img: requests.post(url + "sendPhoto", data={"chat_id": TG_CHAT_ID, "photo": img, "caption": text, "parse_mode": "Markdown"})
    else: requests.post(url + "sendMessage", data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"})

def main():
    config = incarca_config()
    config = verifica_comenzi_telegram(config)
    
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: istoric = set(f.read().splitlines())

    postat = False
    for url in config["rss_urls"]:
        if postat: break
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            if entry.link not in istoric:
                if any(k in (entry.title + entry.get('summary', '')).lower() for k in config["keywords"]):
                    articol = cere_deepseek(entry.title, entry.get('summary', ''), config["limit_chars"])
                    if articol:
                        posteaza_telegram(articol, extrage_imagine(entry))
                        with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                        postat = True; break

if __name__ == "__main__":
    main()
