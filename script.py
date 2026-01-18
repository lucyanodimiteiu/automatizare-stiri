import feedparser, requests, os, re

# Configurare surse
RSS_URLS = ["https://www.digi24.ro/rss", "https://www.hotnews.ro/rss"]
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
DB_FILE = "stiri_trimise.txt"

def trimite_telegram(titlu, descriere, link):
    # Link ascuns pentru poza + Titlu Bold + Descriere
    mesaj = f'<a href="{link}">\u200b</a><b>{titlu}</b>\n\n{descriere}'
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload)
    except:
        pass

def trimite_facebook(titlu, descriere, link):
    if FB_PAGE_ID and FB_PAGE_TOKEN:
        url = f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
        payload = {
            "message": f"{titlu}\n\n{descriere}",
            "link": link,
            "access_token": FB_PAGE_TOKEN
        }
        try:
            requests.post(url, data=payload)
        except:
            pass

if not os.path.exists(DB_FILE): 
    open(DB_FILE, "w").close()

with open(DB_FILE, "r") as f: 
    istoric = f.read().splitlines()

for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries:
        if entry.link not in istoric:
            titlu = entry.title
            descriere = entry.summary if 'summary' in entry else ""
            
            # 1. Ștergem orice cod HTML
            descriere_curata = re.sub('<[^<]+?>', '', descriere)
            
            # 2. Ștergem semnătura sursei (ex: "Digi24", "Hotnews") dacă apare la final
            # tăiem textul după cuvinte cheie tipice sau eliminăm ultimele resturi
            surse_de_sters = ["Digi24", "HotNews.ro", "HotNews", "Sursa:"]
            for sursa in surse_de_sters:
                descriere_curata = descriere_curata.replace(sursa, "")

            # 3. Limităm lungimea și curățăm spațiile goale
            descriere_curata = descriere_curata.strip()[:400]
            
            trimite_telegram(titlu, descriere_curata, entry.link)
            trimite_facebook(titlu, descriere_curata, entry.link)
            
            with open(DB_FILE, "a") as f: 
                f.write(entry.link + "\n")
