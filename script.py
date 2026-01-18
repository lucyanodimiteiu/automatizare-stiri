import feedparser, requests, os, re
from newspaper import Article
import google.generativeai as genai
import nltk

# LINIILE OBLIGATORII pentru serverele GitHub
nltk.download('punkt')
nltk.download('punkt_tab')

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
    prompt = f"""
    Rescrie următoarea știre pentru un canal de Telegram de elită.
    Titlu original: {titlu}
    Text: {text_brut}
    
    REGULI:
    1. Folosește limba română impecabilă.
    2. Titlul să fie bold și să conțină un emoji relevant.
    3. Rezumă totul în 3-4 idei principale (bullet points).
    4. Nu include link-uri, nume de jurnaliști sau reclame.
    5. Menține un ton profesional și informativ.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return f"<b>{titlu}</b>\n\n{text_brut[:500]}..."

def trimite_telegram(text_editat, imagine_url):
    # Verificăm dacă avem o imagine, altfel trimitem doar text
    if imagine_url:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        payload = {
            "chat_id": CHAT_ID, 
            "caption": text_editat[:1024], 
            "photo": imagine_url, 
            "parse_mode": "HTML"
        }
    else:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID, 
            "text": text_editat[:4096], 
            "parse_mode": "HTML"
        }
    requests.post(url, data=payload)

if not os.path.exists(DB_FILE): open(DB_FILE, "w").close()
with open(DB_FILE, "r") as f: istoric = f.read().splitlines()

for rss_url in RSS_URLS:
    feed = feedparser.parse(rss_url)
    for entry in feed.entries[:2]:
        if entry.link not in istoric:
            try:
                articol = Article(entry.link)
                articol.download()
                articol.parse()
                
                text_final = editeaza_cu_ai(articol.title, articol.text)
                
                # Trimitem știrea
                trimite_telegram(text_final, articol.top_image)
                
                # Salvăm în istoric
                with open(DB_FILE, "a") as f: f.write(entry.link + "\n")
                istoric.append(entry.link)
            except Exception as e:
                print(f"Eroare la {entry.link}: {e}")
                continue
