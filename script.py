import feedparser
import requests
import os
import sqlite3
import google.generativeai as genai
import time

# ================= CONFIG =================
RSS_URLS = [
    "https://www.digi24.ro/rss",
    "https://www.hotnews.ro/rss"
    ]

DB_FILE = "stiri.db"

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FB_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_ID = os.getenv("FB_PAGE_ID")

# ============== AI CONFIG =================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
ai = genai.GenerativeModel("gemini-1.5-flash")

# ============== DATABASE ==================
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS stiri (
    link TEXT PRIMARY KEY,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# ============== FUNCTIONS =================
def exista(link):
    cursor.execute("SELECT 1 FROM stiri WHERE link = ?", (link,))
    return cursor.fetchone() is not None

def salveaza(link):
    cursor.execute("INSERT INTO stiri (link) VALUES (?)", (link,))
    conn.commit()

def genereaza_articol(titlu, rezumat):
    prompt = f"""
Ești jurnalist profesionist.
Scrie un articol complet în limba română.

REGULI STRICTE:
- NU inventa informații
- NU adăuga date care nu sunt în text
- Fără surse, fără link-uri
- Include TITLU la început
- Ton neutru, informativ

Titlu:
{titlu}

Rezumat:
{rezumat}
"""
    r = ai.generate_content(prompt)
    return r.text.strip()

def extrage_imagine(entry):
    if "media_content" in entry:
        return entry.media_content[0].get("url")
    if "links" in entry:
        for l in entry.links:
            if "image" in l.get("type", ""):
                return l.get("href")
    return None

def telegram_post(text, img):
    base = f"https://api.telegram.org/bot{TG_TOKEN}/"
    chunks = [text[i:i+3500] for i in range(0, len(text), 3500)]

    if img:
        r = requests.post(
            base + "sendPhoto",
            data={"chat_id": TG_CHAT_ID, "caption": chunks[0]},
            files={"photo": requests.get(img).content}
        )
        if r.status_code != 200:
            raise Exception("Telegram photo failed")
        chunks = chunks[1:]

    for c in chunks:
        r = requests.post(
            base + "sendMessage",
            data={"chat_id": TG_CHAT_ID, "text": c}
        )
        if r.status_code != 200:
            raise Exception("Telegram message failed")
        time.sleep(1)

def facebook_post(text, img):
    url = f"https://graph.facebook.com/{FB_ID}/"
    data = {"message": text, "access_token": FB_TOKEN}

    if img:
        data["url"] = img
        r = requests.post(url + "photos", data=data)
    else:
        r = requests.post(url + "feed", data=data)

    if r.status_code not in (200, 201):
        raise Exception("Facebook post failed")

# ============== MAIN ======================
for rss in RSS_URLS:
    feed = feedparser.parse(rss)
    for entry in feed.entries[:2]:
        if exista(entry.link):
            continue

        try:
            articol = genereaza_articol(entry.title, entry.summary)
            imagine = extrage_imagine(entry)

            telegram_post(articol, imagine)
            facebook_post(articol, imagine)

            salveaza(entry.link)
            print("✔ Publicat:", entry.title)

        except Exception as e:
            print("✖ Eroare:", e)

conn.close()
