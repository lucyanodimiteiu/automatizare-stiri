import feedparser, requests, os
from newspaper import Article
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

RSS_URLS = ["https://www.digi24.ro/rss", "https://www.hotnews.ro/rss"]
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"

def traduce_text(text, limita=4000):
    try:
        if not text: return ""
        return GoogleTranslator(source='auto', target='ro').translate(text[:limita])
    except:
        return text

def trimite_telegram_complet(titlu, text, foto_url):
    # 1. Traducem totul
    titlu_ro = traduce_text(titlu)
    text_ro = traduce_text(text, limita=3500) # Luăm aproape tot articolul
    
    # 2. Trimitem Poza prima dată
    url_foto = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    requests.post(url_foto, data={"chat_id": CHAT_ID, "photo": foto_url})
    
    # 3. Trimitem Textul Complet ca mesaj separat sub poză
    mesaj_final = f"<b>{titlu_ro}</b>\n\n{text_ro}"
    url_msg = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url_msg, data={"chat_id": CHAT_ID, "text": mesaj_final, "parse_mode": "HTML"})

def extrage_si_trimite(link):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        articol = Article(link)
        articol.download()
        articol.parse()
        if articol.title:
            foto = articol.top_image if articol.top_image else "https://via.placeholder.com/500"
            trimite_telegram_complet(articol.title, articol.text, foto)
            return True
    except Exception as e:
        print(f"Eroare extragere: {e}")
        return False

# Verificăm istoricul
if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

# PROCESARE RSS
for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries[:3]:
        if entry.link not in istoric:
            if extrage_si_trimite(entry.link):
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")

# PROCESARE FINVIZ
try:
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = requests.get("https://finviz.com/news.ashx", headers=headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    links = soup.find_all('a', class_='nn-tab-link')
    for link in links[:5]:
        url_stire = link['href']
        if url_stire.startswith('/'): url_stire = "https://finviz.com" + url_stire
        if url_stire not in istoric:
            if extrage_si_trimite(url_stire):
                with open(DB_FILE, "a") as f: f.write(url_stire + "\n")
except Exception as e:
    print(f"Eroare Finviz: {e}")
