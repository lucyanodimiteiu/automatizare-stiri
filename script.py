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
        f"Include un titlu puternic la început. NU menționa sursa, NU pune link-uri, NU menționa autorul, editorul sau faptul că ești un AI. "
        f"Articolul trebuie să fie curat, gata de publicat ca text propriu: {titlu} - {rezumat_sursa}"
    )
    response = ai.generate_content(prompt)
    return response.text

def extrage_imagine(entry):
    # Căutăm imaginea în feed-ul RSS (Digi24/Hotnews)
    if 'media_content' in entry: return entry.media_content[0]['url']
    if 'links' in entry:
        for l in entry.links:
            if 'image' in l.get('type', ''): return l.get('href')
    return None

def posteaza_telegram(text, img):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/"
    if img:
        requests.post(url + "sendPhoto", data={"chat_id": TG_CHAT_ID, "caption": text[:1024], "photo": img, "parse_mode": "HTML"})
    else:
        requests.post(url + "sendMessage", data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"})

def posteaza_facebook(text, img):
    url = f"https://graph.facebook.com/{FB_ID}/"
    if img:
        requests.post(url + "photos", data={"message": text, "url": img, "access_token": FB_TOKEN})
    else:
        requests.post(url + "feed", data={"message": text, "access_token": FB_TOKEN})

if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

RSS_URLS = ["https://www.digi24.ro/rss", "https://www.hotnews.ro/rss"]

for url in RSS_URLS:
    feed = feedparser.parse(url)
    for entry in feed.entries[:2]:
        if entry.link not in istoric:
            try:
                articol_integral = prelucreaza_articol_complet(entry.title, entry.summary)
                imagine = extrage_imagine(entry)
                
                posteaza_telegram(articol_integral, imagine)
                posteaza_facebook(articol_integral, imagine)
                
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
            except Exception as e:
                print(f"Eroare: {e}")
