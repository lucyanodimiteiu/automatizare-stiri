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
        "messages": [
            {"role": "system", "content": "Ești un jurnalist român care scrie articole complete, profesionale și obiective."},
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
            print(f"Eroare API: {data}")
            return None
    except Exception as e:
        print(f"Eroare rețea: {e}")
        return None

def posteaza_telegram(text):
    try:
        # Telegram suportă mesaje de max 4096 caractere. 
        # DeepSeek s-ar putea să scrie mult, așa că tăiem dacă e cazul.
        if len(text) > 4000:
            text = text[:4000] + "..."
            
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"})
        
        # Dacă Markdown dă eroare (din cauza caracterelor speciale), trimitem text simplu
        if res.status_code != 200:
            requests.post(url, data={"chat_id": TG_CHAT_ID, "text": text})
            
        print("Postat pe Telegram!")
    except Exception as e:
        print(f"Eroare Telegram: {e}")

# Gestiune istoric
if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

# Surse RSS (Poți adăuga oricâte aici)
RSS_URLS = [
    "https://www.digi24.ro/rss",
    "https://hotnews.ro/rss",
    "https://finviz.com/news_rss.ashx"
]

print("Verificăm știri noi...")

for url in RSS_URLS:
    feed = feedparser.parse(url)
    # Procesăm ultimele 3 știri din fiecare sursă
    for entry in feed.entries[:3]:
        if entry.link not in istoric:
            print(f"Procesăm: {entry.title}")
            
            prompt = (
                f"Scrie un articol de știri complet în limba română bazat pe acest subiect: {entry.title}. "
                f"Rezumat sursă: {entry.get('summary', '')}. "
                f"Cerințe: Stil jurnalistic profesionist, minim 3 paragrafe, fără link-uri, fără menționarea sursei, fără introduceri de tip 'Iată articolul'."
            )
            
            articol = cere_deepseek(prompt)
            if articol:
                posteaza_telegram(articol)
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                # O mică pauză să nu fim blocați de Telegram pentru spam
                time.sleep(3)

print("Rulare finalizată.")
