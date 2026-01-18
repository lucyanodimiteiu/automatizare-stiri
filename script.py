import feedparser, requests, os, re
from newspaper import Article
from deep_translator import GoogleTranslator

# SURSE FILTRATE PE DOMENII SERIOASE
RSS_URLS = [
    # ROMÂNIA (Filtre pe Economie, Finante, Aparare)
    "https://www.digi24.ro/rss/stiri/economie",
    "https://www.digi24.ro/rss/stiri/externe/aparare-si-securitate",
    "https://www.hotnews.ro/rss/economie",
    "https://www.hotnews.ro/rss/finante_banci",
    
    # INTERNAȚIONAL (Traduse automat)
    "https://www.marketwatch.com/rss/topstories",
    "https://www.pv-magazine.com/feed/",          # Fotovoltaice & Baterii
    "https://3dprintingindustry.com/feed/",       # Imprimare 3D
    "https://www.technologyreview.com/feed/",      # Inovații Tech
    "https://cointelegraph.com/rss",               # Crypto
    "https://www.exhibitionworld.co.uk/rss.xml"    # Târguri & Expoziții
]

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"

def tradu_text(text):
    if not text or len(text) < 5: return text
    try:
        translator = GoogleTranslator(source='auto', target='ro')
        # Dacă textul e foarte lung, îl traducem în bucăți
        if len(text) > 4000:
            parti = [text[i:i+4000] for i in range(0, len(text), 4000)]
            return " ".join([translator.translate(p) for p in parti])
        return translator.translate(text)
    except:
        return text

def curata_continut(text):
    if not text: return ""
    text = re.sub(r'\s+', ' ', text)
    # Lista de curățare pentru a elimina semnăturile editorilor
    semne_oprire = ["Editor :", "Autor :", "Ediția", "Foto:", "Sursa:", "Copyright", "All rights reserved", "Read more", "Reporting by"]
    for semn in semne_oprire:
        if semn in text: text = text.split(semn)[0]
    return text.strip()

def trimite_telegram(titlu, text_complet, imagine_url):
    # MESAJ 1: Poza + Titlu + Începutul articolului (max 1024 caractere captație)
    intro = f"<b>{titlu}</b>\n\n{text_complet[:400]}..."
    url_foto = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    
    r = requests.post(url_foto, data={"chat_id": CHAT_ID, "caption": intro, "photo": imagine_url, "parse_mode": "HTML"})
    
    # MESAJ 2: Restul articolului (până la 4000 caractere) ca răspuns la primul (Reply)
    if r.status_code == 200:
        msg_id = r.json()['result']['message_id']
        rest_articol = text_complet[400:4000] 
        
        if len(rest_articol) > 50:
            url_msg = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url_msg, data={
                "chat_id": CHAT_ID, 
                "text": rest_articol, 
                "reply_to_message_id": msg_id,
                "parse_mode": "HTML"
            })

# Incarcare istoric
if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries[:2]: # Luăm 2 știri noi per sursă
        if entry.link not in istoric:
            try:
                articol = Article(entry.link)
                articol.download()
                articol.parse()
                
                titlu = articol.title
                text_lung = curata_continut(articol.text)
                
                # Traducem doar dacă nu sunt surse românești
                if not any(x in entry.link for x in ["digi24.ro", "hotnews.ro"]):
                    titlu = tradu_text(titlu)
                    text_lung = tradu_text(text_lung)
                
                if len(text_lung) > 100: # Verificăm să nu trimitem știri goale
                    trimite_telegram(titlu, text_lung, articol.top_image)
                    
                    with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                    istoric.append(entry.link)
            except:
                continue
