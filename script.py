import feedparser, requests, os, re, json

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"
CONFIG_FILE = "config_bot.json"

DEFAULT_CONFIG = {
    "rss_urls": [
        "https://www.digi24.ro/rss/stiri/economie", 
        "http://feeds.marketwatch.com/marketwatch/topstories/",
        "https://www.reutersagency.com/feed/?best-topics=business",
        "https://finviz.com/news_rss.ashx"
    ],
    "keywords": ["economie", "finante", "bursa", "tech", "market", "fed", "bitcoin", "trump"],
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
    url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("ok"):
            for result in res.get("result", []):
                msg = result.get("message", {})
                text = msg.get("text", "")
                caller_id = msg.get("chat", {}).get("id")
                if text == "/lista_config":
                    info = f"📊 CONFIG:\nSurse: {len(config['rss_urls'])}\nKeywords: {', '.join(config['keywords'])}"
                    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": caller_id, "text": info})
                elif text.startswith("/adauga_keyword"):
                    k = text.replace("/adauga_keyword ", "").strip().lower()
                    if k and k not in config["keywords"]:
                        config["keywords"].append(k)
                        salveaza_config(config)
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": caller_id, "text": f"✅ Adaugat: {k}"})
    except: pass
    return config

def verifica_duplicat_ai(titlu_nou, istoric_titluri):
    if not istoric_titluri: return False
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    prompt = f"Titlu nou: '{titlu_nou}'. Istoric: {istoric_titluri}. Daca e acelasi subiect raspunde 'DA', altfel 'NU'."
    try:
        res = requests.post(url, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}, headers=headers, timeout=10).json()
        return "DA" in res['choices'][0]['message']['content'].upper()
    except: return False

def cere_deepseek(titlu, rezumat, limit):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    prompt = f"Rezuma in romana (max {limit} ch, Bold, Emoji). SENTIMENT la final (🟢/🔴/🟡): {titlu} - {rezumat}"
    try:
        res = requests.post(url, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.5}, headers=headers, timeout=60).json()
        return res['choices'][0]['message']['content']
    except: return None

def main():
    config = incarca_config()
    config = verifica_comenzi_telegram(config) # Am activat urechile!
    
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: istoric_completa = f.read().splitlines()
    istoric_linkuri = {line.split('|')[0] for line in istoric_completa if '|' in line}
    titluri_recente = [line.split('|')[1] for line in istoric_completa[-20:] if '|' in line]

    postat = False
    for url in config["rss_urls"]:
        if postat: break
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            if entry.link not in istoric_linkuri:
                if any(k in (entry.title + entry.get('summary', '')).lower() for k in config["keywords"]):
                    if not verifica_duplicat_ai(entry.title, titluri_recente):
                        articol = cere_deepseek(entry.title, entry.get('summary', ''), config["limit_chars"])
                        if articol:
                            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": TG_CHAT_ID, "text": articol, "parse_mode": "Markdown"})
                            with open(DB_FILE, "a") as f: f.write(f"{entry.link}|{entry.title}\n")
                            postat = True; break

if __name__ == "__main__":
    main()
