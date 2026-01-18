import feedparser, requests, os, re
from newspaper import Article
import google.generativeai as genai
import nltk

# Configurare componente necesare pentru extragerea textului
try:
    nltk.download('punkt')
    nltk.download('punkt_tab')
except:
    pass

# Configurare Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

RSS_URLS = [
    "https://www.digi24.ro/rss/stiri/economie",
    "https://www.hotnews.ro/rss/economie",
    "https://www.marketwatch.com/rss/topstories",
    "https://www.pv-magazine.com/feed/",
    "https://cointelegraph.com/rss"
]

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"

def editeaza_cu_ai(titlu, text_brut):
    # Dacă textul extras e prea scurt, ne bazăm pe titlu
    context = text_brut if len(text_brut) > 200 else "Rezuma aceasta stire bazandu-te pe titlu."
    
    prompt = f"""
    Rescrie următoarea știre pentru un canal de Telegram de elită, în limba română.
    Titlu original: {titlu}
    Text: {context}
    
    REGULI:
    1. Folosește limba română impecabilă și un ton profesional.
    2. Titlul să fie bold cu un emoji relevant la început.
    3. Rezumă în 3 idei principale (bullet points) scurte și clare.
    4. Nu include link-uri în interiorul textului sau nume de jurnaliști.
    5. Finalizează cu o concluzie de o singură propoziție.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return f"<b>{titlu}</b>\n\n(Stire in curs de procesare...)"

def trimite_telegram(text_editat, imagine_url, sursa_url):
    # Curățăm link-ul de trackere gen edir.ro
    sursa_curata = sursa_url.split('?')[0]
    mesaj_final = f"{text_editat}\n\n🔗 <a href='{sursa_curata}'>Sursa originală</a>"
    
    if imagine_url and len(imagine_url) > 5:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        payload = {
            "chat_id": CHAT_ID, 
            "caption": mesaj_final[:1024], 
            "photo": imagine_url, 
            "parse_mode": "HTML"
        }
    else:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID, 
            "text": mesaj_final[:4096], 
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
    requests.post(url, data=payload)

# Pornire procesare
if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries[:3]:
        # Curățăm link-ul pentru verificare în baza de date
        link_id = entry.link.split('?')[0]
        
        if link_id not in istoric:
            try:
                # Extragem conținutul complet al articolului
                articol = Article(entry.link)
                articol.download()
                articol.parse()
                
                # Procesăm cu Gemini
                text_ai = editeaza_cu_ai(articol.title, articol.text)
                
                # Trimitem pe Telegram
                trim
