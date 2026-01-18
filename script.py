import feedparser, requests, os, json

# Configurare API-uri
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FB_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_ID = os.getenv("FB_PAGE_ID")
DB_FILE = "stiri_trimise.txt"

def cere_ai(prompt):
    # Incercam intai DeepSeek (Mult mai stabil pentru cereri bulk)
    if DEEPSEEK_KEY:
        try:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }
            res = requests.post(url, json=payload, headers=headers, timeout=30)
            return res.json()['choices'][0]['message']['content']
        except:
            print("DeepSeek indisponibil, incercam Gemini...")

    # Backup: Gemini 2.0
    url_gem = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    payload_gem = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url_gem, json=payload_gem, timeout=30)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Toate AI-urile au esuat: {e}")
        return None

def prelucreaza_articol(titlu, rezumat_sursa):
    prompt = (
        f"Esti jurnalist. Rescrie integral in romana, fara sa mentionezi sursa, link-ul sau autorul. "
        f"Titlu si articol complet: {titlu} - {rezumat_sursa}"
    )
    return cere_ai(prompt)

def extrage_imagine(entry):
    if 'media_content' in entry: return entry.media_content[0]['url']
    if 'media_thumbnail' in entry: return entry.media_thumbnail[0]['url']
    if 'links' in entry:
        for l in entry.links:
            if 'image' in l.get('type', ''): return l.get('href')
    return None

def posteaza(text, img):
    # Telegram
    url_tg = f"https://api.telegram.org/bot{TG_TOKEN}/"
    if img:
        requests.post(url_tg + "sendPhoto", data={"chat_id": TG_CHAT_ID, "caption": text[:1020], "photo": img})
    else:
        requests.post(url_tg + "sendMessage", data={"chat_id": TG_CHAT_ID, "text": text})
    
    # Facebook
    url_fb = f"https://graph.facebook.com/{FB_ID}/"
    if img:
        requests.post(url_fb + "photos", data={"message": text, "url": img, "access_token": FB_TOKEN})
    else:
        requests.post(url_fb + "feed", data={"message": text, "access_token": FB_TOKEN})

if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

RSS_URLS = ["https://www.digi24.ro/rss", "https://finviz.com/news_rss.ashx"]

for url in RSS_URLS:
    feed = feedparser.parse(url)
    for entry in feed.entries[:2]:
        if entry.link not in istoric:
            articol = prelucreaza_articol(entry.title, entry.get('summary', ''))
            if articol:
                posteaza(articol, extrage_imagine(entry))
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
