import feedparser, requests, os, google.generativeai as genai

# Configurare AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
ai = genai.GenerativeModel('gemini-1.5-flash')

# Configurare Social Media
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FB_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_ID = os.getenv("FB_PAGE_ID")
DB_FILE = "stiri_trimise.txt"

def prelucreaza_articol_complet(titlu, rezumat_sursa):
    prompt = (
        f"Ești un jurnalist profesionist. Rescrie următorul subiect într-un articol complet, lung și detaliat în limba română. "
        f"Dacă știrea este în engleză, traducerea trebuie să fie impecabilă. Include un titlu puternic la început. "
        f"NU menționa sursa, NU pune link-uri, NU menționa autorul, site-ul original sau faptul că ești un AI. "
        f"Articolul trebuie să fie curat și gata de publicat: {titlu} - {rezumat_sursa}"
    )
    response = ai.generate_content(prompt)
    return response.text

def extrage_imagine(entry):
    # Căutăm imaginea în diverse formate de feed (Digi24, Finviz, MarketWatch)
    if 'media_content' in entry: return entry.media_content[0]['url']
    if 'media_thumbnail' in entry: return entry.media_thumbnail[0]['url']
    if 'links' in entry:
        for l in entry.links:
            if 'image' in l.get('type', ''): return l.get('href')
    return None

def posteaza_telegram(text, img):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/"
    # Telegram limitează descrierea pozei la 1024 caractere. Dacă e mai lung, trimitem text separat.
    if img:
        res = requests.post(url + "sendPhoto", data={"chat_id": TG_CHAT_ID, "caption": text[:1020], "photo": img})
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

# Sursele tale actualizate
RSS_URLS = [
    "https://www.digi24.ro/rss",
    "https://www.hotnews.ro/rss",
    "https://finviz.com/news_rss.ashx",
    "https://feeds.content.dowjones.io/public/rss/mw_topstories"
]

for url in RSS_URLS:
    feed = feedparser.parse(url)
    for entry in feed.entries[:3]:
        if entry.link not in istoric:
            try:
                # Folosim summary sau description în funcție de ce oferă feed-ul
                desc = entry.get('summary', entry.get('description', ''))
                articol_integral = prelucreaza_articol_complet(entry.title, desc)
                imagine = extrage_imagine(entry)
                
                posteaza_telegram(articol_integral, imagine)
                posteaza_facebook(articol_integral, imagine)
                
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
            except Exception as e:
                print(f"Eroare la procesarea {entry.link}: {e}")
