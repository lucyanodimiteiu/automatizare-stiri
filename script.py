#!/usr/bin/env python3
"""
Script premium de rezumat știri conform specificațiilor Luci.
Folosește DeepSeek API pentru a genera rezumate structurate cu imagini.
"""
import feedparser
import requests
import os
import json
import re
import sys
import random
from urllib.parse import urlparse

# Configurare căi relative
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "stiri_trimise.txt")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config_bot.json")

# Configurare API - variabile de mediu (setate în GitHub Secrets)
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEKAPIKEY")
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DEFAULT_CONFIG = {
    "rss_urls": [
        "https://www.digi24.ro/rss/stiri/economie", 
        "http://feeds.marketwatch.com/marketwatch/topstories/",
        "https://www.reutersagency.com/feed/?best-topics=business"
    ],
    "keywords": ["economie", "finante", "bursa", "tech", "market", "fed", "bitcoin", "trump"],
    "limit_chars": 800
}

# Bibliotecă de imagini Unsplash (gratuit, fără copyright)
IMAGE_LIBRARY = {
    "#AI": [
        "https://images.unsplash.com/photo-1503023345310-bd7c1de61c7d",
        "https://images.unsplash.com/photo-1535223289827-42f1e9919769",
        "https://images.unsplash.com/photo-1581091012184-5c1d7b1f5a5b"
    ],
    "#Tech": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475",
        "https://images.unsplash.com/photo-1519389950473-47ba0277781c",
        "https://images.unsplash.com/photo-1518770660439-4636190af475"
    ],
    "#EnergieVerde": [
        "https://images.unsplash.com/photo-1509395176047-4a66953fd231",
        "https://images.unsplash.com/photo-1509395176047-4a66953fd231",
        "https://images.unsplash.com/photo-1509395176047-4a66953fd231"
    ],
    "#Eolian": [
        "https://images.unsplash.com/photo-1509395176047-4a66953fd231",
        "https://images.unsplash.com/photo-1509395176047-4a66953fd231",
        "https://images.unsplash.com/photo-1509395176047-4a66953fd231"
    ],
    "#Macro": [
        "https://images.unsplash.com/photo-1520607162513-77705c0f0d4a",
        "https://images.unsplash.com/photo-1507679799987-c73779587ccf",
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e"
    ],
    "#Finanțe": [
        "https://images.unsplash.com/photo-1520607162513-77705c0f0d4a",
        "https://images.unsplash.com/photo-1507679799987-c73779587ccf",
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e"
    ],
    "#Startup": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475",
        "https://images.unsplash.com/photo-1519389950473-47ba0277781c",
        "https://images.unsplash.com/photo-1518770660439-4636190af475"
    ],
    "#Crypto": [
        "https://images.unsplash.com/photo-1621416894562-7a5e768f8b1a",
        "https://images.unsplash.com/photo-1621416894562-7a5e768f8b1a",
        "https://images.unsplash.com/photo-1621416894562-7a5e768f8b1a"
    ],
    "#Bitcoin": [
        "https://images.unsplash.com/photo-1621416894562-7a5e768f8b1a",
        "https://images.unsplash.com/photo-1621416894562-7a5e768f8b1a",
        "https://images.unsplash.com/photo-1621416894562-7a5e768f8b1a"
    ],
    "#Semiconductori": [
        "https://images.unsplash.com/photo-1581091870627-3b6f8c2a9f5c",
        "https://images.unsplash.com/photo-1581091870627-3b6f8c2a9f5c",
        "https://images.unsplash.com/photo-1581091870627-3b6f8c2a9f5c"
    ],
    "#Auto": [
        "https://images.unsplash.com/photo-1503376780353-7e6692767b70",
        "https://images.unsplash.com/photo-1503376780353-7e6692767b70",
        "https://images.unsplash.com/photo-1503376780353-7e6692767b70"
    ],
    "#Cybersecurity": [
        "https://images.unsplash.com/photo-1555949963-aa79dcee981c",
        "https://images.unsplash.com/photo-1555949963-aa79dcee981c",
        "https://images.unsplash.com/photo-1555949963-aa79dcee981c"
    ],
    "#Geopolitică": [
        "https://images.unsplash.com/photo-1509395176047-4a66953fd231",
        "https://images.unsplash.com/photo-1509395176047-4a66953fd231",
        "https://images.unsplash.com/photo-1509395176047-4a66953fd231"
    ],
    "#Energie": [
        "https://images.unsplash.com/photo-1509395176047-4a66953fd231",
        "https://images.unsplash.com/photo-1509395176047-4a66953fd231",
        "https://images.unsplash.com/photo-1509395176047-4a66953fd231"
    ]
}

# Mapping cuvinte cheie -> tag-uri
KEYWORD_TO_TAG = {
    "ai": "#AI",
    "inteligență": "#AI",
    "artificial": "#AI",
    "machine learning": "#AI",
    "llm": "#AI",
    "chatgpt": "#AI",
    "openai": "#AI",
    "tech": "#Tech",
    "tehnologie": "#Tech",
    "gadget": "#Tech",
    "innovation": "#Tech",
    "inovație": "#Tech",
    "crypto": "#Crypto",
    "criptomonede": "#Crypto",
    "bitcoin": "#Bitcoin",
    "ethereum": "#Crypto",
    "blockchain": "#Crypto",
    "finanțe": "#Finanțe",
    "economie": "#Macro",
    "bursa": "#Macro",
    "market": "#Macro",
    "fed": "#Macro",
    "inflație": "#Macro",
    "solar": "#EnergieVerde",
    "fotovoltaic": "#EnergieVerde",
    "renewable": "#EnergieVerde",
    "energie": "#Energie",
    "energy": "#Energie",
    "eolian": "#Eolian",
    "wind": "#Eolian",
    "auto": "#Auto",
    "mașină": "#Auto",
    "electric": "#Auto",
    "semiconductori": "#Semiconductori",
    "chip": "#Semiconductori",
    "cybersecurity": "#Cybersecurity",
    "securitate": "#Cybersecurity",
    "hack": "#Cybersecurity",
    "geopolitică": "#Geopolitică",
    "conflict": "#Geopolitică",
    "startup": "#Startup",
    "finanțare": "#Startup"
}

def incarca_config():
    """Încarcă configurația din fișier."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                conf = json.load(f)
                if conf and "rss_urls" in conf:
                    return conf
        except:
            pass
    return DEFAULT_CONFIG

def salveaza_config(config):
    """Salvează configurația."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def verifica_comenzi_telegram(config):
    """Verifică comenzile primite pe Telegram și actualizează config."""
    if not TG_TOKEN:
        return config
    url = f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("ok"):
            for result in res.get("result", []):
                msg = result.get("message", {})
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")
                if text == "/lista_config":
                    txt = f"📊 CONFIG:\nSurse: {len(config['rss_urls'])}\nKeywords: {', '.join(config['keywords'][:10])}..."
                    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": chat_id, "text": txt})
                elif text.startswith("/adauga_keyword"):
                    k = text.replace("/adauga_keyword ", "").strip().lower()
                    if k and k not in config["keywords"]:
                        config["keywords"].append(k)
                        salveaza_config(config)
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": chat_id, "text": f"✅ Adaugat: {k}"})
    except:
        pass
    return config

def verifica_duplicat_ai(titlu, istoric):
    """Folosește AI pentru a verifica dacă titlul este duplicat."""
    if not istoric or not DEEPSEEK_KEY:
        return False
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    try:
        res = requests.post(url, json={"model": "deepseek-chat", "messages": [{"role": "user", "content": f"Titlu: {titlu}. Istoric: {istoric}. Daca e acelasi subiect, zi DA, altfel NU."}], "temperature": 0.1}, headers=headers, timeout=10).json()
        return "DA" in res['choices'][0]['message']['content'].upper()
    except:
        return False

def extrage_imagine(entry):
    """Extrage URL‑ul unei imagini din intrarea RSS."""
    # Încearcă media:content
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if media.get('type', '').startswith('image/'):
                return media['url']
    # Încearcă enclosures
    if hasattr(entry, 'enclosures'):
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image/'):
                return enc['href']
    # Încearcă linkuri în summary
    if hasattr(entry, 'summary'):
        img_matches = re.findall(r'<img[^>]+src="([^">]+)"', entry.summary)
        if img_matches:
            return img_matches[0]
    return None

def determina_tag(titlu, descriere):
    """Determină tag‑ul principal în funcție de cuvinte cheie."""
    text = (titlu + ' ' + descriere).lower()
    for kw, tag in KEYWORD_TO_TAG.items():
        if kw in text:
            return tag
    return "#Tech"  # default

def alege_imagine(tag):
    """Alege o imagine random din bibliotecă pentru tag‑ul dat."""
    if tag in IMAGE_LIBRARY and IMAGE_LIBRARY[tag]:
        return random.choice(IMAGE_LIBRARY[tag])
    return "https://images.unsplash.com/photo-1518770660439-4636190af475"  # default tech

def genereaza_rezumat_premium(titlu, descriere, tag, limit_chars):
    """Generează un text jurnalistic șlefuit, cursiv, fără numerotare."""
    if not DEEPSEEK_KEY:
        return None
    
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    
    prompt = f"""
Ești un jurnalist de elită, cu zeci de ani de experiență în publicații de prestigiu (stil Bloomberg/Reuters). 
Analizează știrea de mai jos și scrie un text impecabil, șlefuit și autoritar.

REGULI CRITICE:
1. FĂRĂ NUMEROTARE: Nu folosi cifre (1, 2, 3), liste cu puncte sau bullet-uri. Textul trebuie să fie un flux narativ de 2-3 paragrafe scurte.
2. TON: Extrem de profesionist, analitic și sobru.
3. STRUCTURĂ: 
   - Titlu impactant la început (un singur emoji relevant).
   - Introducere care pune contextul în perspectivă.
   - Corpul textului care explică datele relevante (cifre, companii, impact).
4. DATE: Păstrează cifrele esențiale, dar integrează-le natural în fraze.
5. FĂRĂ DESCRIERE IMAGINE: Nu menționa nimic despre poză în text.
6. TAG-URI: Maxim două la final.

ȘTIREA: {titlu} - {descriere}
TAG: {tag}

REDACTEAZĂ DOAR TEXTUL FINAL ÎN LIMBA ROMÂNĂ.
"""
    try:
        response = requests.post(url, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": 1000
        }, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"Eroare DeepSeek: {e}")
        return None

def trimite_pe_telegram(imagine_url, rezumat_text):
    """Trimite imaginea cu rezumatul pe Telegram."""
    if not TG_TOKEN or not TG_CHAT_ID:
        print("⚠️  Token sau chat ID Telegram lipsă.")
        return False
    
    # Dacă avem imagine, trimitem foto cu caption
    if imagine_url and imagine_url.startswith('http'):
        # Trimite foto
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        data = {
            "chat_id": TG_CHAT_ID,
            "photo": imagine_url,
            "caption": rezumat_text,
            "parse_mode": "Markdown"
        }
        try:
            resp = requests.post(url, data=data, timeout=30)
            if resp.status_code == 200:
                return True
        except:
            pass  # Fallback la text
    
    # Fallback: trimite doar text
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {
        "chat_id": TG_CHAT_ID,
        "text": rezumat_text,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, data=data, timeout=30)
        return resp.status_code == 200
    except Exception as e:
        print(f"Eroare trimitere Telegram: {e}")
        return False

def main():
    """Funcția principală."""
    config = incarca_config()
    config = verifica_comenzi_telegram(config)
    
    # Încarcă istoric
    if not os.path.exists(DB_FILE):
        open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f:
        lines = f.read().splitlines()
    istoric_links = {l.split('|')[0] for l in lines if '|' in l}
    titluri_vechi = [l.split('|')[1] for l in lines[-20:] if '|' in l]
    
    # Parcurge feedurile
    for rss_url in config["rss_urls"]:
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:10]:  # primele 10
                # Verifică dacă e nou
                if entry.link in istoric_links:
                    continue
                
                # Verifică cuvinte cheie
                text = (entry.title + ' ' + entry.get('summary', '')).lower()
                if not any(kw.lower() in text for kw in config["keywords"]):
                    continue
                
                # Verifică duplicat cu AI (opțional)
                if verifica_duplicat_ai(entry.title, titluri_vechi):
                    print(f"Duplicat detectat: {entry.title[:50]}")
                    continue
                
                # Determină tag
                tag = determina_tag(entry.title, entry.get('summary', ''))
                
                # Extrage imagine (dacă există)
                imagine_url = extrage_imagine(entry)
                if not imagine_url:
                    imagine_url = alege_imagine(tag)
                
                # Generează rezumat
                rezumat = genereaza_rezumat_premium(entry.title, entry.get('summary', ''), tag, config.get("limit_chars", 800))
                if not rezumat:
                    print("Nu s‑a putut genera rezumatul.")
                    continue
                
                # Trimite pe Telegram
                success = trimite_pe_telegram(imagine_url, rezumat)
                if success:
                    # Salvează în istoric
                    with open(DB_FILE, "a") as f:
                        f.write(f"{entry.link}|{entry.title}\n")
                    print(f"✅ Trimis: {entry.title[:50]}...")
                    return  # Oprește după primul articol
                else:
                    print("❌ Eroare la trimitere Telegram.")
        except Exception as e:
            print(f"Eroare procesare feed {rss_url}: {e}")
            continue

if __name__ == "__main__":
    main()