import feedparser, requests, os, time

# Configurare API DeepSeek si Telegram
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"

def cere_deepseek(prompt):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ești un jurnalist român profesionist. Scrii articole clare și obiective."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=60)
        return res.json()['choices'][0]['message']['content']
    except:
        return None

def extrage_imagine(entry):
    """Încearcă să găsească link-ul imaginii în diverse formate RSS."""
    # 1. Caută în media_content (format standard)
    if 'media_content' in entry and len(entry.media_content) > 0:
        return entry.media_content[0]['url']
    # 2. Caută în media_thumbnail
    if 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        return entry.media_thumbnail[0]['url']
    # 3. Caută în enclosure
    if 'enclosures' in entry and len(entry.enclosures) > 0:
        return entry.enclosures[0]['href']
    # 4. Caută în link-uri (unele site-uri pun imaginea ca link de tip image/jpeg)
    if 'links' in entry:
        for link in entry.links:
            if 'image' in link.get('type', ''):
                return link.get('href')
    return None

def posteaza_telegram(text, imagine_url):
    try:
        if len(text) > 1024: # Limita pentru caption la poze este mai mică (1024)
            caption = text[:1020] + "..."
        else:
            caption = text

        if imagine_url:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
            res = requests.post(url, data={"chat_id": TG_CHAT_ID, "photo": imagine_url, "caption": caption})
            if res.status_code == 200:
                print("Postat cu poză.")
                return
        
        # Dacă nu avem poză sau trimiterea pozei a eșuat, trimitem doar text
        url_msg = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url_msg, data={"chat_id": TG_CHAT_ID, "text": text[:4000]})
        print("Postat doar text.")
    except Exception as e:
        print(f"Eroare Telegram: {e}")

if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

RSS_URLS = [
    "https://www.digi24.ro/rss",
    "https://hotnews.ro/rss",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://finviz.com/news_rss.ashx"
]

for url in RSS_URLS:
    feed = feedparser.parse(url)
    for entry in feed.entries[:2]:
        if entry.link not in istoric:
            print(f"Procesăm: {entry.title}")
            
            # Extragem poza înainte de a apela AI-ul
            img = extrage_imagine(entry)
            
            prompt = f"Rescrie integral în română, stil jurnalistic, fără link sau sursă: {entry.title} - {entry.get('summary', '')}"
            articol = cere_deepseek(prompt)
            
            if articol:
                posteaza_telegram(articol, img)
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                time.sleep(5)
