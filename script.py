import feedparser
import requests
import os
import time
import re
import json

# Configurare API din GitHub Secrets
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"
CONFIG_FILE = "config_bot.json"

# Setări implicite
DEFAULT_CONFIG = {
    "rss_urls": [
        "https://www.digi24.ro/rss/stiri/economie", 
        "https://www.digi24.ro/rss/stiri/sci-tech",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://finviz.com/news_rss.ashx"
    ],
    "keywords": ["economie", "finante", "tehnologie", "tech", "bursa", "profit", "bani", "digital", "industrie", "market"],
    "limit_chars": 800
}

def incarca_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_CONFIG

def salveaza_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def verifica_comenzi_telegram(config):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("ok"):
            for result in res.get("result", []):
                msg = result.get("message", {})
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")
                
                if str(chat_id) == str(TG_CHAT_ID):
                    if text.startswith("/adauga_keyword"):
                        nou_cuvant = text.replace("/adauga_keyword ", "").strip().lower()
                        if nou_cuvant and nou_cuvant not in config["keywords"]:
                            config["keywords"].append(nou_cuvant)
                            salveaza_config(config)
                            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                                          data={"chat_id": TG_CHAT_ID, "text": f"✅ Am adăugat cuvântul cheie: {nou_cuvant}"})
                    
                    elif text == "/lista_config":
                        info = f"📊 CONFIGURAȚIE ACTUALĂ:\n\nSursă RSS: {len(config['rss_urls'])}\nKeywords: {', '.join(config['keywords'])}"
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                                      data={"chat_id": TG_CHAT_ID, "text": info})
    except: pass
    return config

def cere_deepseek(titlu, rezumat_sursa, limit):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    prompt = (f"Ești un jurnalist economic/tech. Rezumă această știre în română (max {limit} caractere).\n"
              f"Titlu cu bold la început, folosește bullet points și emoji.\n"
              f"NU pune linkuri sau surse. Știre: {titlu} - {rezumat_sursa}")
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.6}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=60)
        return res.json()['choices'][0]['message']['content']
    except: return None

def extrage_imagine(entry):
    if 'media_content' in entry: return entry.media_content[0]['url']
    if 'enclosures' in entry and len(entry.enclosures) > 0: return entry.enclosures[0]['href']
    img_match = re.search(r'<img [^>]*src="([^"]+)"', entry.get('summary', ''))
    return img_match.group(1) if img_match else None

def posteaza_telegram(text, imagine_url):
    base_url = f"https://api.telegram.org/bot{TG_TOKEN}"
    if imagine_url:
        requests.post(f"{base_url}/sendPhoto", data={"chat_id": TG_CHAT_ID, "photo": imagine_url, "caption": text, "parse_mode": "Markdown"})
    else:
        requests.post(f"{base_url}/sendMessage", data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"})

def main():
    config = incarca_config()
    config = verifica_comenzi_telegram(config)
    
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: istoric = set(f.read().splitlines())

    postat = False
    for url in config["rss_urls"]:
        if postat: break
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            if entry.link not in istoric:
                text_analiza = (entry.title + " " + entry.get('summary', '')).lower()
                if any(k in text_analiza for k in config["keywords"]):
                    articol = cere_deepseek(entry.title, entry.get('summary', ''), config["limit_chars"])
                    if articol:
                        img = extrage_imagine(entry)
                        posteaza_telegram(articol, img)
                        with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                        postat = True; break

if __name__ == "__main__":
    main()
