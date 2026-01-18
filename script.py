import feedparser, requests, os, time

# Configurare API-uri
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FB_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_ID = os.getenv("FB_PAGE_ID")
DB_FILE = "stiri_trimise.txt"

def cere_ai(prompt):
    # 1. Incerci DeepSeek (Cel mai stabil)
    if DEEPSEEK_KEY:
        try:
            res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
                headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, timeout=20)
            return res.json()['choices'][0]['message']['content']
        except: pass

    # 2. Incerci GPT-4o mini (Backup rapid)
    if OPENAI_KEY:
        try:
            res = requests.post("https://api.openai.com/v1/chat/completions",
                json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]},
                headers={"Authorization": f"Bearer {OPENAI_KEY}"}, timeout=20)
            return res.json()['choices'][0]['message']['content']
        except: pass

    # 3. Incerci Gemini 2.0 (Ultima varianta)
    url_gem = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    try:
        res = requests.post(url_gem, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=20)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except: return None

def posteaza(text, img):
    # Telegram
    try:
        url_tg = f"https://api.telegram.org/bot{TG_TOKEN}/"
        if img: requests.post(url_tg + "sendPhoto", data={"chat_id": TG_CHAT_ID, "caption": text[:1020], "photo": img})
        else: requests.post(url_tg + "sendMessage", data={"chat_id": TG_CHAT_ID, "text": text})
    except: print("Eroare Telegram")

    # Facebook
    try:
        url_fb = f"https://graph.facebook.com/{FB_ID}/"
        if img: requests.post(url_fb + "photos", data={"message": text, "url": img, "access_token": FB_TOKEN})
        else: requests.post(url_fb + "feed", data={"message": text, "access_token": FB_TOKEN})
    except: print("Eroare Facebook")

if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

RSS_URLS = ["https://www.digi24.ro/rss", "https://finviz.com/news_rss.ashx", "https://feeds.content.dowjones.io/public/rss/mw_topstories"]

for url in RSS_URLS:
    feed = feedparser.parse(url)
    for entry in feed.entries[:2]:
        if entry.link not in istoric:
            prompt = f"Rescrie integral in romana, fara sursa sau link. Titlu si articol: {entry.title} - {entry.get('summary', '')}"
            articol = cere_ai(prompt)
            if articol:
                posteaza(articol, None) # Schimba cu extrage_imagine(entry) daca vrei poze
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                time.sleep(5) # Pauza anti-blocaj
