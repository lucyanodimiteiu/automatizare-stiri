import feedparser, requests, os, json

# Configurare API
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FB_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_ID = os.getenv("FB_PAGE_ID")
DB_FILE = "stiri_trimise.txt"

def prelucreaza_articol_complet(titlu, rezumat_sursa):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = (
        f"Ești un jurnalist profesionist. Rescrie subiectul următor într-un articol complet și detaliat în limba română. "
        f"Include un titlu puternic la început. NU menționa sursa, NU pune link-uri, NU menționa autorul sau faptul că ești un AI. "
        f"Textul să fie curat și gata de publicat: {titlu} - {rezumat_sursa}"
    )
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=payload)
    res_json = response.json()
    
    try:
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except:
        print(f"Eroare Gemini: {res_json}")
        return None

def extrage_imagine(entry):
    if 'media_content' in entry: return entry.media_content[0]['url']
    if 'media_thumbnail' in entry: return entry.media_thumbnail[0]['url']
    if 'links' in entry:
        for l in entry.links:
            if 'image' in l.get('type', ''): return l.get('href')
    return None

def posteaza_telegram(text, img):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/"
    if img:
        requests.post(url + "sendPhoto", data={"chat_id": TG_CHAT_ID, "caption": text[:1020], "photo": img})
        if len(text) > 1020:
            requests.post(url + "sendMessage", data={"chat_id": TG_CHAT_ID, "text": text[1020:]})
    else:
        requests.post(url + "sendMessage", data={"chat_id": TG_CHAT_ID, "text": text})

def posteaza_facebook(text, img):
    url = f"https://graph.facebook.com/{FB_ID}/"
    if img:
        requests.post(url + "photos", data={"message": text, "url": img, "access_token": FB_TOKEN})
    else:
        requests.post(url + "feed", data={"message": text, "access_token": FB_TOKEN})

if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

RSS_URLS = [
    "https://www.digi24.ro/rss",
    "https://hotnews.ro/rss",
    "https://finviz.com/news_rss.ashx",
    "https://feeds.content.dowjones.io/public/rss/mw_topstories"
]

for url in RSS_URLS:
    feed = feedparser.parse(url)
    for entry in feed.entries[:2]:
        if entry.link not in istoric:
            desc = entry.get('summary', entry.get('description', ''))
            articol_integral = prelucreaza_articol_complet(entry.title, desc)
            
            if articol_integral:
                imagine = extrage_imagine(entry)
                posteaza_telegram(articol_integral, imagine)
                posteaza_facebook(articol_integral, imagine)
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
