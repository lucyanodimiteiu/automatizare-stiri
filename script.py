import feedparser
import requests
import os
import re
from newspaper import Article
from deep_translator import GoogleTranslator

# LISTA TA EXTINSĂ DE SURSE
RSS_URLS = [
    "https://www.digi24.ro/rss", 
    "https://www.hotnews.ro/rss",
    "https://www.marketwatch.com/rss/topstories",
    "https://www.pv-magazine.com/feed/",          # Panouri & Baterii
    "https://3dprintingindustry.com/feed/",       # Imprimare 3D
    "https://www.technologyreview.com/feed/",      # Inovatii Tech
    "https://cointelegraph.com/rss"                # Crypto
]

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"

def tradu_text(text):
    if not text or len(text) < 5: return text
    try:
        # GoogleTranslator are limita de 5000 caractere, deci taiem textul daca e prea lung
        return GoogleTranslator(source='auto', target='ro').translate(text[:4500])
    except:
        return text

def curata_continut(text):
    if not text: return ""
    text = re.sub(r'\s+', ' ', text)
    # Cuvinte de oprire extinse (Romana + Engleza)
    semne_oprire = [
        "Editor :", "Autor :", "Ediția", "Foto:", "Sursa:", 
        "Redactor:", "Citește și:", "Copyright ©", "All rights reserved",
        "Read more", "Sharing is caring", "Follow us", "Reporting by"
    ]
    for semn in semne_oprire:
        if semn in text:
            text = text.split(semn)[0]
    return text.strip()

def trimite_telegram(titlu, continut, imagine_url):
    # Pregatim mesajul (Max 1024 caractere pentru poze)
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
    for entry in feed.entries[:2]: # Luam doar primele 2 stiri din fiecare sursa ca sa nu blocam procesul
        if entry.link not in istoric:
            try:
                articol = Article(entry.link)
                articol.download()
                articol.parse()
                
                titlu = articol.title
                text_complet = curata_continut(articol.text)
                
                # TRADUCERE AUTOMATA: Daca sursa NU este Digi24 sau Hotnews, traduce tot
                if not any(x in entry.link for x in ["digi24.ro", "hotnews.ro"]):
                    titlu = tradu_text(titlu)
                    text_complet = tradu_text(text_complet)
                
                poza = articol.top_image
                trimite_telegram(titlu, text_complet, poza)
                
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                istoric.append(entry.link)
            except:
                continue
