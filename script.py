import feedparser, requests, os, re

RSS_URLS = ["https://www.digi24.ro/rss", "https://www.hotnews.ro/rss"]
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"

def curata_text(text):
    # Elimină tag-urile HTML
    text = re.sub('<[^<]+?>', '', text)
    # Taie textul dacă găsește mențiuni de editor/autor la final
    semne_oprire = ["Editor :", "Autor :", "Ediția", "Foto:", "Sursa:"]
    for semn in semne_oprire:
        if semn in text:
            text = text.split(semn)[0]
    return text.strip()

def trimite_telegram(titlu, descriere):
    text_final = f"<b>{titlu}</b>\n\n{descriere}"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text_final, "parse_mode": "HTML"})

if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries[:5]:
        # Verificăm ID-ul unic al știrii ca să nu se dubleze
        stire_id = entry.link
        if stire_id not in istoric:
            titlu = entry.title
            # Luăm descrierea și o curățăm de editori
            descriere = curata_text(entry.summary if 'summary' in entry else "")
            
            trimite_telegram(titlu, descriere)
            
            # Salvăm imediat în istoric
            with open(DB_FILE, "a") as f: f.write(stire_id + "\n")
            istoric.append(stire_id)
