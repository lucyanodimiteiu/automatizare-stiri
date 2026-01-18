import feedparser
import requests
import os
import re
from newspaper import Article
from deep_translator import GoogleTranslator

# Sursele tale
RSS_URLS = [
    "https://www.digi24.ro/rss", 
    "https://www.hotnews.ro/rss",
    "https://www.marketwatch.com/rss/topstories"
]

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"

def tradu_text(text):
    try:
        # Traduce din orice limbă detectată în Română
        return GoogleTranslator(source='auto', target='ro').translate(text)
    except:
        return text # Dacă traducerea eșuează, trimite textul original

def curata_continut(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    semne_oprire = [
        "Editor :", "Autor :", "Ediția", "Foto:", "Sursa:", 
        "Redactor:", "Citește și:", "Urmărește-ne și pe",
        "Copyright ©", "All rights reserved", "Write to ", "Reporting by"
    ]
    for semn in semne_oprire:
        if semn in text:
            text = text.split(semn)[0]
    return text.strip()

def trimite_telegram(titlu, continut, imagine_url):
    mesaj_final = f"<b>{titlu}</b>\n\n{continut}"
    if len(mesaj_final) > 1000:
        mesaj_final = mesaj_final[:997] + "..."

    if imagine_url:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        payload = {"chat_id": CHAT_ID, "caption": mesaj_final, "photo": imagine_url, "parse_mode": "HTML"}
    else:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": mesaj_final, "parse_mode": "HTML"}
    
    requests.post(url, data=payload)

if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries[:3]:
        if entry.link not in istoric:
            try:
                articol = Article(entry.link)
                articol.download()
                articol.parse()
                
                # Extragem titlul și textul
                titlu_original = articol.title
                text_original = curata_continut(articol.text)
                
                # Traducem dacă sursa este MarketWatch (sau dacă vrei pentru toate)
                if "marketwatch.com" in entry.link:
                    titlu = tradu_text(titlu_original)
                    text_complet = tradu_text(text_original)
                else:
                    titlu = titlu_original
                    text_complet = text_original
                
                poza = articol.top_image
                trimite_telegram(titlu, text_complet, poza)
                
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                istoric.append(entry.link)
            except:
                continue
