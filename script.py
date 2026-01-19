import feedparser, requests, os, time

# Configurare API DeepSeek si Telegram
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"

def cere_deepseek(prompt):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ești un jurnalist român profesionist. Traduci și rescrii știri internaționale într-o limbă română impecabilă."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=60)
        data = res.json()
        if 'choices' in data:
            return data['choices'][0]['message']['content']
        else:
            print(f"Eroare DeepSeek: {data.get('error', {}).get('message', 'Verifica creditul')}")
            return None
    except Exception as e:
        print(f"Eroare retea: {e}")
        return None

def posteaza_telegram(text):
    try:
        if len(text) > 4000:
            text = text[:4000] + "..."
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text})
        print("Mesaj trimis pe Telegram.")
    except Exception as e:
        print(f"Eroare Telegram: {e}")

if not os.path.exists(DB_FILE):
    open(DB_FILE, "w").close()

with open(DB_FILE, "r") as f:
    istoric = f.read().splitlines()

# SURSE MIXTE (ROMANIA + INTERNATIONAL)
RSS_URLS = [
    "https://www.digi24.ro/rss",            # RO
    "https://hotnews.ro/rss",               # RO
    "http://feeds.bbci.co.uk/news/world/rss.xml", # INTERNAȚIONAL (BBC)
    "https://www.reutersagency.com/feed/",   # INTERNAȚIONAL (Reuters)
    "https://search.cnbc.com/rs/search/view.xml?partnerId=2000&keywords=finance", # BANI/TECH
    "https://finviz.com/news_rss.ashx"      # BURSA/SUA
]

print("Verificăm sursele internaționale și românești...")

for url in RSS_URLS:
    feed = feedparser.parse(url)
    # Procesăm primele 2 știri noi din FIECARE sursă
    count = 0
    for entry in feed.entries:
        if count >= 2: break
        if entry.link not in istoric:
            print(f"Procesam: {entry.title}")
            
            # Promptul îi spune clar să TRADUCĂ dacă știrea e în engleză
            prompt = (
                f"Ești jurnalist. Traduce (dacă e cazul) și rescrie acest articol integral în limba română: "
                f"Titlu: {entry.title}. Rezumat: {entry.get('summary', '')}. "
                f"Reguli: Stil jurnalistic, fără link-uri, fără surse, minim 3 paragrafe."
            )
            
            articol = cere_deepseek(prompt)
            if articol:
                posteaza_telegram(articol)
                with open(DB_FILE, "a") as f:
                    f.write(entry.link + "\n")
                count += 1
                time.sleep(4)

print("Gata!")
