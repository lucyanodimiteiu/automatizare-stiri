import feedparser, requests, os
from google import genai

# Configurare AI - Forțăm modelul stabil
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-1.5-flash" # Modelul stabil

# Configurare Social Media
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FB_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_ID = os.getenv("FB_PAGE_ID")
DB_FILE = "stiri_trimise.txt"

def prelucreaza_articol_complet(titlu, rezumat_sursa):
    prompt = (
        f"Ești un jurnalist profesionist. Rescrie subiectul următor într-un articol complet și detaliat în limba română. "
        f"Include un titlu puternic. NU menționa sursa, NU pune link-uri, NU menționa autorul sau faptul că ești un AI. "
        f"Textul să fie curat și gata de publicat: {titlu} - {rezumat_sursa}"
    )
    # Am adăugat configurarea de model stabil aici
    response = client.models.generate_content(
        model=MODEL_ID, 
        contents=prompt
    )
    return response.text

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
        # Trimitem poza cu prima parte a textului (limită 1024 caractere)
        requests.post(url + "sendPhoto", data={"chat_id": TG_CHAT_ID, "caption": text[:1020], "photo": img})
        # Dacă textul e mai lung, trimitem restul ca mesaj separat
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
            try:
                desc = entry.get('summary', entry.get('description', ''))
                articol_integral = prelucreaza_articol_complet(entry.title, desc)
                imagine = extrage_imagine(entry)
                
                posteaza_telegram(articol_integral, imagine)
                posteaza_facebook(articol_integral, imagine)
                
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
            except Exception as e:
                print(f"Eroare: {e}")
