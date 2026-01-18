import feedparser, requests, os
from newspaper import Article

RSS_URLS = ["https://www.digi24.ro/rss", "https://www.hotnews.ro/rss"]
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"

def trimite_telegram_cu_poza(titlu, text, foto_url):
    # Trimitem poza cu titlul si continutul in descriere (caption)
    # Limitam textul la 1000 caractere (limita Telegram pentru caption la poza)
    mesaj = f"<b>{titlu}</b>\n\n{text[:1000]}..."
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    data = {"chat_id": CHAT_ID, "photo": foto_url, "caption": mesaj, "parse_mode": "HTML"}
    requests.post(url, data=data)

if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries[:3]: # Luam ultimele 3 stiri
        if entry.link not in istoric:
            try:
                # Extragem continutul complet al articolului
                articol = Article(entry.link)
                articol.download()
                articol.parse()
                
                # Trimitem pe Telegram
                trimite_telegram_cu_poza(articol.title, articol.text, articol.top_image)
                
                # Salvam in istoric ca sa nu o mai trimitem
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
            except:
                print(f"Eroare la procesarea stirii: {entry.link}")
