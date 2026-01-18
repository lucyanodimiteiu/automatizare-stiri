import feedparser
import requests
import os
import re
from newspaper import Article

# Sursele tale
RSS_URLS = ["https://www.digi24.ro/rss", "https://www.hotnews.ro/rss"]
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"

def curata_continut(text):
    if not text:
        return ""
    # Elimină spațiile multiple și tag-urile reziduale
    text = re.sub(r'\s+', ' ', text)
    # Lista de "stop" - taie tot ce urmează după aceste cuvinte (Editori/Autori)
    semne_oprire = ["Editor :", "Autor :", "Ediția", "Foto:", "Sursa:", "Redactor:", "Citește și:", "Urmărește-ne și pe"]
    for semn in semne_oprire:
        if semn in text:
            text = text.split(semn)[0]
    return text.strip()

def trimite_telegram(titlu, continut, imagine_url):
    # Telegram are limită de 1024 caractere la mesajele cu poză
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

# Verificare istoric
if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries[:3]:
        if entry.link not in istoric:
            try:
                # Extragem tot articolul de pe site
                articol = Article(entry.link)
                articol.download()
                articol.parse()
                
                titlu = articol.title
                text_complet = curata_continut(articol.text)
                poza = articol.top_image
                
                # Trimitem la Telegram
                trimite_telegram(titlu, text_complet, poza)
                
                # Salvăm în DB ca să nu se repete
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                istoric.append(entry.link)
            except Exception as e:
                print(f"Eroare la {entry.link}: {e}")
                continue
