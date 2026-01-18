import feedparser, requests, os, re
from newspaper import Article
from deep_translator import GoogleTranslator

RSS_URLS = [
    "https://www.digi24.ro/rss", 
    "https://www.hotnews.ro/rss",
    "https://www.marketwatch.com/rss/topstories",
    "https://www.pv-magazine.com/feed/",
    "https://3dprintingindustry.com/feed/",
    "https://www.technologyreview.com/feed/",
    "https://cointelegraph.com/rss",
    "https://www.exhibitionworld.co.uk/rss.xml"
]

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"

def tradu_text(text):
    if not text or len(text) < 5: return text
    try:
        # Spargem textul în bucăți de 4000 caractere pentru traducere (limita Google)
        translator = GoogleTranslator(source='auto', target='ro')
        if len(text) > 4000:
            parti = [text[i:i+4000] for i in range(0, len(text), 4000)]
            return " ".join([translator.translate(p) for p in parti])
        return translator.translate(text)
    except:
        return text

def curata_continut(text):
    if not text: return ""
    text = re.sub(r'\s+', ' ', text)
    semne_oprire = ["Editor :", "Autor :", "Ediția", "Foto:", "Sursa:", "Copyright", "All rights reserved", "Read more"]
    for semn in semne_oprire:
        if semn in text: text = text.split(semn)[0]
    return text.strip()

def trimite_telegram(titlu, text_complet, imagine_url):
    # MESAJ 1: Poza + Titlu + Primii 400 de caractere
    intro = f"<b>{titlu}</b>\n\n{text_complet[:400]}..."
    url_foto = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    
    r = requests.post(url_foto, data={"chat_id": CHAT_ID, "caption": intro, "photo": imagine_url, "parse_mode": "HTML"})
    
    # MESAJ 2: Restul articolului (până la 4000 caractere) ca răspuns la primul
    if r.status_code == 200:
        msg_id = r.json()['result']['message_id']
        rest_articol = text_complet[400:4000] # Luăm grosul articolului
        
        if len(rest_articol) > 50:
            url_msg = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url_msg, data={
                "chat_id": CHAT_ID, 
                "text": rest_articol, 
                "reply_to_message_id": msg_id,
                "parse_mode": "HTML"
            })

if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries[:2]:
        if entry.link not in istoric:
            try:
                articol = Article(entry.link)
                articol.download()
                articol.parse()
                
                titlu = articol.title
                text_lung = curata_continut(articol.text)
                
                if not any(x in entry.link for x in ["digi24.ro", "hotnews.ro"]):
                    titlu = tradu_text(titlu)
                    text_lung = tradu_text(text_lung)
                
                trimite_telegram(titlu, text_lung, articol.top_image)
                
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                istoric.append(entry.link)
            except: continue
