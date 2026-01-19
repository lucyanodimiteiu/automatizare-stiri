import feedparser, requests, os, re, json

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"
CONFIG_FILE = "config_bot.json"

DEFAULT_CONFIG = {
    "rss_urls": [
        "https://finance.yahoo.com/rss/topstories",
        "https://finance.yahoo.com/rss/crypto",
        "http://feeds.marketwatch.com/marketwatch/topstories/",
        "https://www.reutersagency.com/feed/?best-topics=business",
        "https://www.digi24.ro/rss/stiri/economie"
    ],
    "keywords": ["economie", "finante", "bursa", "tech", "market", "fed", "bitcoin", "trump", "aur", "fotovoltaice", "imprimare3d"],
    "limit_chars": 900
}

def incarca_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                conf = json.load(f)
                if conf and "rss_urls" in conf: return conf
        except: pass
    return DEFAULT_CONFIG

def extraie_imagine(entry):
    if 'media_content' in entry: return entry.media_content[0]['url']
    if 'media_thumbnail' in entry: return entry.media_thumbnail[0]['url']
    match = re.search(r'<img src="([^"]+)"', entry.get('description', '') + entry.get('summary', ''))
    if match: return match.group(1)
    return None

def trimite_telegram(text, img_url=None):
    """Încearcă să trimită cu poză, dacă eșuează, trimite doar textul"""
    try:
        if img_url:
            res = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                                data={"chat_id": TG_CHAT_ID, "photo": img_url, "caption": text, "parse_mode": "Markdown"}, timeout=20)
            if res.status_code == 200: return True
        
        # Dacă nu avem imagine sau trimiterea imaginii a eșuat
        res = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                            data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=20)
        return res.status_code == 200
    except:
        return False

def main():
    config = incarca_config()
    # Verificăm comenzi (simplificat pentru stabilitate)
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: lines = f.read().splitlines()
    istoric_links = {l.split('|')[0] for l in lines if '|' in l}
    titluri_vechi = [l.split('|')[1] for l in lines[-30:] if '|' in l]

    for url in config["rss_urls"]:
        feed = feedparser.parse(url)
        for entry in feed.entries[:20]: 
            if entry.link not in istoric_links:
                text_analiza = (entry.title + " " + entry.get('summary', '')).lower()
                if any(k in text_analiza for k in config["keywords"]):
                    # Verificare dublură AI
                    url_ai = "https://api.deepseek.com/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
                    prompt_dup = f"Titlu nou: {entry.title}. Istoric: {titluri_vechi}. Daca e acelasi subiect, raspunde doar DA, altfel NU."
                    
                    try:
                        res_dup = requests.post(url_ai, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt_dup}], "temperature": 0.1}, headers=headers, timeout=10).json()
                        is_dup = "DA" in res_dup['choices'][0]['message']['content'].upper()
                    except: is_dup = False

                    if not is_dup:
                        # Generare Rezumat
                        prompt_rez = f"Rezuma in romana (max 900 ch, Bold, Emoji). SENTIMENT (🟢/🔴/🟡) la final: {entry.title} - {entry.get('summary', '')}"
                        try:
                            res_rez = requests.post(url_ai, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt_rez}], "temperature": 0.5}, headers=headers, timeout=60).json()
                            articol = res_rez['choices'][0]['message']['content']
                            
                            img = extraie_imagine(entry)
                            if trimite_telegram(articol, img):
                                with open(DB_FILE, "a") as f: f.write(f"{entry.link}|{entry.title}\n")
                        except: pass

if __name__ == "__main__":
    main()
