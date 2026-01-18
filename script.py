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
    # Incercam DeepSeek (daca ai pus cheia)
    if DEEPSEEK_KEY:
        try:
            res = requests.post("https://api.deepseek.com/v1/chat/completions", 
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
                headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, timeout=25)
            return res.json()['choices'][0]['message']['content']
        except: print("DeepSeek Offline...")

    # Incercam Gemini 2.0 (Stabil)
    url_gem = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    try:
        res = requests.post(url_gem, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=25)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except: 
        print("Gemini Quota Exceeded...")
        return None

def posteaza(text):
    # Telegram
    tg_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(tg_url, data={"chat_id": TG_CHAT_ID, "text": text})
    
    # Facebook
    fb_url = f"https://graph.facebook.com/{FB_ID}/feed"
    requests.post(fb_url, data={"message": text, "access_token": FB_TOKEN})

# Citire istoric
if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

RSS_URLS = ["https://www.digi24.ro/rss", "https://finviz.com/news_rss.ashx"]

for url in RSS_URLS:
    feed = feedparser.parse(url)
    for entry in feed.entries[:2]:
        if entry.link not in istoric:
            print(f"Procesam: {entry.title}")
            prompt = f"Scrie un articol de stiri complet in romana, fara link-uri sau surse, bazat pe: {entry.title} - {entry.get('summary', '')}"
            articol = cere_ai(prompt)
            if articol:
                posteaza(articol)
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                print("Postat cu succes!")
                time.sleep(2)
             
