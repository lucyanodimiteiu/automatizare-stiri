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
    "keywords": ["economie", "finante", "bursa", "tech", "market", "fed", "inflation", "trump"],
    "limit_chars": 800
}

def incarca_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try: return json.load(f)
            except: return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def verifica_duplicat_ai(titlu_nou, istoric_titluri):
    """Întreabă AI-ul dacă știrea a mai fost postată sub altă formă"""
    if not istoric_titluri: return False
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    prompt = f"Compară acest titlu: '{titlu_nou}' cu această listă de titluri recente: {istoric_titluri}. Dacă subiectul este același, răspunde doar cu 'DA'. Dacă este un subiect nou, răspunde cu 'NU'."
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10).json()
        return "DA" in res['choices'][0]['message']['content'].upper()
    except: return False

def cere_deepseek(titlu, rezumat, limit):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    prompt = (f"Ești expert financiar. Rezumă în română (max {limit} caractere, Bold, Emoji).\n"
              f"La final adaugă o secțiune 'SENTIMENT' cu un cerc colorat (🟢/🔴/🟡) și explică impactul pe scurt.\n"
              f"Știre: {titlu} - {rezumat}")
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.5}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=60).json()
        return res['choices'][0]['message']['content']
    except: return None

def main():
    config = incarca_config()
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: istoric_completa = f.read().splitlines()
    
    # Păstrăm ultimele 20 de titluri pentru comparație AI
    istoric_linkuri = set(istoric_completa)
    titluri_recente = [line.split('|')[1] for line in istoric_completa[-20:] if '|' in line]

    postat = False
    for url in config["rss_urls"]:
        if postat: break
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            if entry.link not in istoric_linkuri:
                # 1. Verificăm cuvinte cheie
                text_analiza = (entry.title + " " + entry.get('summary', '')).lower()
                if any(k in text_analiza for k in config["keywords"]):
                    # 2. Verificăm duplicat prin AI
                    if not verifica_duplicat_ai(entry.title, titluri_recente):
                        articol = cere_deepseek(entry.title, entry.get('summary', ''), config["limit_chars"])
                        if articol:
                            # Trimitem pe Telegram
                            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                                          data={"chat_id": TG_CHAT_ID, "text": articol, "parse_mode": "Markdown"})
                            # Salvăm link-ul și titlul pentru deduplicare viitoare
                            with open(DB_FILE, "a") as f: f.write(f"{entry.link}|{entry.title}\n")
                            postat = True; break

if __name__ == "__main__":
    main()
