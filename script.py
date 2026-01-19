import feedparser, requests, os, json, time

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"
CONFIG_FILE = "config_bot.json"

def incarca_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"rss_urls": [], "keywords": [], "limit_chars": 900}

def trimite_tg(destinatar_id, text, img=None):
    """Trimite mesaj către un ID specific (canal sau user privat)"""
    try:
        if img:
            r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                             data={"chat_id": destinatar_id, "photo": img, "caption": text, "parse_mode": "Markdown"}, timeout=15)
            if r.status_code == 200: return True
        
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                     data={"chat_id": destinatar_id, "text": text, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def proceseaza_comenzi(config):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
        res = requests.get(url, timeout=10).json()
        if not res.get("result"): return
        
        for update in res["result"][-5:]:
            msg = update.get("message", {})
            user_privat_id = msg.get("chat", {}).get("id")
            text = msg.get("text", "")
            
            if text == "/lista_config" and user_privat_id:
                info = f"📊 *CONFIG ACTIVĂ:*\n\n*Surse:* {len(config['rss_urls'])}\n*Keywords:* {', '.join(config['keywords'])}"
                # REPARAȚIE: Trimitem în privat celui care a întrebat
                trimite_tg(user_privat_id, info)
                break 
    except: pass

def main():
    config = incarca_config()
    proceseaza_comenzi(config)
    
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: istoric = f.read()

    for url in config["rss_urls"]:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            if entry.link not in istoric:
                full_text = (entry.title + " " + entry.get('summary', '')).lower()
                if any(k in full_text for k in config["keywords"]):
                    prompt = f"Rezuma in romana (max 800 ch, Bold, Emoji). SENTIMENT (🟢/🔴/🟡) la final: {entry.title} - {entry.get('summary', '')}"
                    try:
                        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
                        data = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}
                        res = requests.post("https://api.deepseek.com/v1/chat/completions", json=data, headers=headers, timeout=40).json()
                        
                        articol = res['choices'][0]['message']['content']
                        img = None
                        if 'media_content' in entry: img = entry.media_content[0]['url']
                        
                        # Știrile merg pe CANAL
                        trimite_tg(TG_CHAT_ID, articol, img)
                        
                        with open(DB_FILE, "a") as f: f.write(f"{entry.link}\n")
                    except: continue

if __name__ == "__main__":
    main()
