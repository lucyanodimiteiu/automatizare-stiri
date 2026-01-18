import feedparser, requests, os, re

# Configurare surse
RSS_URLS = ["https://www.digi24.ro/rss", "https://www.hotnews.ro/rss"]
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
DB_FILE = "stiri_trimise.txt"

def trimite_telegram(titlu, descriere, link):
    # Folosim un link ascuns într-un spațiu invizibil la începutul mesajului pentru a forța poza
    mesaj = f'<a href="{link}">\u200b</a><b>{titlu}</b>\n\n{descriere}'
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML",
        "disable_web_page_preview": False # Trebuie să fie False pentru a vedea poza
    }
    requests.post(url, data=payload)

def trimite_facebook(titlu, descriere, link):
    if FB_PAGE_ID and FB_PAGE_TOKEN:
        url = f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
        # Trimitem link-ul separat în parametrul 'link', astfel poza apare automat
        # dar textul din 'message' rămâne curat
        payload = {
            "message": f"{titlu}\n\n{descriere}",
            "link": link,
            "access_token": FB_PAGE_TOKEN
        }
        requests.post(url, data=payload)

if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries[:5]:
        if entry.link not in istoric:
            # Curățăm titlul și descrierea
            titlu = entry.title
            descriere = entry.summary if 'summary' in entry else ""
            descriere_curata = re.sub('<[^<]+?>', '', descriere)[:300] # Limităm la 300 caractere
            
            # Trimitem pe ambele platforme
            trimite_telegram(titlu, descriere_curata, entry.link)
            trimite_facebook(titlu, descriere_curata, entry.link)
            
            with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
