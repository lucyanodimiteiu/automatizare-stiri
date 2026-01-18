import feedparser, requests, os, re
from newspaper import Article
from bs4 import BeautifulSoup

RSS_URLS = ["https://www.digi24.ro/rss", "https://www.hotnews.ro/rss"]
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"

def trimite_postare_curata(titlu, text, foto_url):
    # Telegram permite max 1024 caractere la caption-ul pozei
    descriere = f"<b>{titlu}</b>\n\n{text[:900]}..."
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    data = {"chat_id": CHAT_ID, "photo": foto_url, "caption": descriere, "parse_mode": "HTML"}
    requests.post(url, data=data)

def extrage_si_trimite(link):
    try:
        articol = Article(link)
        articol.download()
        articol.parse()
        if articol.title and (articol.top_image or articol.meta_img):
            foto = articol.top_image if articol.top_image else articol.meta_img
            trimite_postare_curata(articol.title, articol.text, foto)
            return True
    except:
        return False
    return False

# 1. PROCESARE RSS (Digi24, Hotnews)
if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries[:3]:
        if entry.link not in istoric:
            if extrage_si_trimite(entry.link):
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")

# 2. PROCESARE FINVIZ (Scraping)
try:
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = requests.get("https://finviz.com/news.ashx", headers=headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    # Finviz pune stirile in link-uri cu clasa "nn-tab-link"
    links = soup.find_all('a', class_='nn-tab-link')
    
    for link in links[:5]: # Luam ultimele 5 de pe Finviz
        url_stire = link['href']
        if url_stire not in istoric:
            if extrage_si_trimite(url_stire):
                with open(DB_FILE, "a") as f: f.write(url_stire + "\n")
except Exception as e:
    print(f"Eroare Finviz: {e}")
