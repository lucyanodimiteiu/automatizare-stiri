import feedparser, requests, os, re

# Configurare surse
RSS_URLS = ["https://www.digi24.ro/rss", "https://www.hotnews.ro/rss"]
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
DB_FILE = "stiri_trimise.txt"

def trimite_telegram(titlu, descriere, link):
    # Truc pentru poza: un link ascuns intr-un caracter invizibil la inceput
    mesaj = f'<a href="{link}">\u200b</a><b>{titlu}</b>\n\n{descriere}'
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
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

# Verificam ce am trimis deja
if not os.path.exists(DB_FILE): 
    open(DB_FILE, "w").close()

with open(DB_FILE, "r") as f: 
    istoric = f.read().splitlines()

# Procesam TOATE stirile gasite in RSS
for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    # Am scos [:5], acum proceseaza tot ce gaseste
    for entry in feed.entries:
        if entry.link not in istoric:
            # Curatam textul
            titlu = entry.title
            descriere = entry.summary if 'summary' in entry else ""
            descriere_curata = re.sub('<[^<]+?>', '', descriere)[:400] # Luam primele 400 caractere
            
            # Trimitem
            trimite_telegram(titlu, descriere_curata, entry.link)
            trimite_facebook(titlu, descriere_curata, entry.link)
            
            # Salvam in istoric ca sa nu o mai trimitem a doua oara
            with open(DB_FILE, "a") as f: 
                f.write(entry.link + "\n")
