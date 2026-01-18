import feedparser, requests, os, time

# Configurare API DeepSeek
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")

# Configurare Telegram
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
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=30)
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Eroare DeepSeek: {e}")
        return None

def posteaza_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text})
        if res.status_code == 200:
            print("Postat pe Telegram cu succes!")
        else:
            print(f"Eroare Telegram: {res.text}")
    except Exception as e:
        print(f"Eroare conexiune Telegram: {e}")

# Gestiune istoric
if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

# Surse RSS
RSS_URLS = [
    "https://www.digi24.ro/rss",
    "https://finviz.com/news_rss.ashx",
    "https://feeds.content.dowjones.io/public/rss/mw_topstories"
]

for url in RSS_URLS:
    feed = feedparser.parse(url)
    for entry in feed.entries[:2]:
        if entry.link not in istoric:
            print(f"Procesam: {entry.title}")
            prompt = (
                f"Rescrie acest articol integral in romana, ca un jurnalist profesionist. "
                f"NU pune link-uri, NU mentiona sursa, NU scrie 'Iata stirea'. "
                f"Pune un titlu clar si apoi textul complet: {entry.title} - {entry.get('summary', '')}"
            )
            articol = cere_deepseek(prompt)
            if articol:
                posteaza_telegram(articol)
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                time.sleep(5)
