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
    titlu_ro = traduce_text(titlu)
    text_ro = traduce_text(text, limita=3500)
    
    # Pasul 1: Trimite poza
    url_foto = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    requests.post(url_foto, data={"chat_id": CHAT_ID, "photo": foto_url})
    
    # Pasul 2: Trimite textul
    mesaj_final = f"<b>{titlu_ro}</b>\n\n{text_ro}"
    url_msg = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url_msg, data={"chat_id": CHAT_ID, "text": mesaj_final, "parse_mode": "HTML"})

def extrage_si_trimite(link, istoric_titluri):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        articol = Article(link)
        articol.download()
        articol.parse()
        
        # VERIFICARE DUPLICAT DUPĂ TITLU
        if not articol.title or articol.title.strip() in istoric_titluri:
            return False, None

        foto = articol.top_image if articol.top_image else "https://via.placeholder.com/500"
        trimite_telegram_complet(articol.title, articol.text, foto)
        return True, articol.title.strip()
    except:
        return False, None

# Încărcăm istoricul (link-uri și titluri)
if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r", encoding="utf-8") as f: istoric = f.read().splitlines()

# Procesare RSS
for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries[:3]:
        if entry.link not in istoric and entry.title not in istoric:
            succes, titlu_salvat = extrage_si_trimite(entry.link, istoric)
            if succes:
                with open(DB_FILE, "a", encoding="utf-8") as f:
                    f.write(entry.link + "\n")
                    f.write(titlu_salvat + "\n")

# Procesare FINVIZ
try:
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = requests.get("https://finviz.com/news.ashx", headers=headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    links = soup.find_all('a', class_='nn-tab-link')
    for link in links[:8]:
        url_stire = link['href']
        titlu_finviz = link.text.strip()
        if url_stire.startswith('/'): url_stire = "https://finviz.com" + url_stire
        
        # Verificăm și link-ul și titlul înainte de a procesa
        if url_stire not in istoric and titlu_finviz not in istoric:
            succes, titlu_salvat = extrage_si_trimite(url_stire, istoric)
            if succes:
                with open(DB_FILE, "a", encoding="utf-8") as f:
                    f.write(url_stire + "\n")
                    f.write(titlu_salvat + "\n")
except Exception as e:
    print(f"Eroare Finviz: {e}")
