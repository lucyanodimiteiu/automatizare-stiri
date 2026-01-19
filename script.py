import feedparser
import requests
import os
import time
import re

# Configurare API din GitHub Secrets
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"

def cere_deepseek(titlu, rezumat_sursa):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    
    prompt = (
        f"Ești un jurnalist economic și tech. Rezumă această știre pentru un canal de Telegram.\n"
        f"TITLU: {titlu}\n"
        f"INFO: {rezumat_sursa}\n\n"
        f"CERINȚE:\n"
        f"1. Lungime: 500-800 caractere.\n"
        f"2. Titlu cu bold la început: **TITLU AICI**.\n"
        f"3. Folosește bullet points (•) și emoji-uri.\n"
        f"4. NU pune link-uri, surse sau referințe la alte site-uri.\n"
        f"5. Scrie direct în limba română."
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6
    }
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=60)
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content']
    except:
        return None

def extrage_imagine(entry):
    if 'media_content' in entry: return entry.media_content[0]['url']
    if 'enclosures' in entry and len(entry.enclosures) > 0: return entry.enclosures[0]['href']
    if 'media_thumbnail' in entry: return entry.media_thumbnail[0]['url']
    img_match = re.search(r'<img [^>]*src="([^"]+)"', entry.get('summary', ''))
    return img_match.group(1) if img_match else None

def posteaza_telegram(text, imagine_url):
    base_url = f"https://api.telegram.org/bot{TG_TOKEN}"
    try:
        if imagine_url:
            requests.post(f"{base_url}/sendPhoto", data={
                "chat_id": TG_CHAT_ID,
                "photo": imagine_url,
                "caption": text,
                "parse_mode": "Markdown"
            }, timeout=30)
        else:
            requests.post(f"{base_url}/sendMessage", data={
                "chat_id": TG_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown"
            }, timeout=30)
    except Exception as e:
        print(f"Eroare Telegram: {e}")

def main():
    if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f: istoric = set(f.read().splitlines())

    RSS_URLS = [
        "https://www.digi24.ro/rss/stiri/economie", 
        "https://www.digi24.ro/rss/stiri/sci-tech",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://finviz.com/news_rss.ashx"
    ]
    
    KEYWORDS = ["economie", "finante", "tehnologie", "tech", "industrie", "bursa", "profit", "business", "market", "trade", "industry", "bani", "digital"]
    
    gasit_si_postat = False

    for url in RSS_URLS:
        if gasit_si_postat: break 
        
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            if entry.link not in istoric:
                text_analiza = (entry.title + " " + entry.get('summary', '')).lower()
                
                if any(key in text_analiza for key in KEYWORDS):
                    articol = cere_deepseek(entry.title, entry.get('summary', ''))
                    if articol:
                        img = extrage_imagine(entry)
                        posteaza_telegram(articol, img)
                        with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                        gasit_si_postat = True
                        break

if __name__ == "__main__":
    main()
