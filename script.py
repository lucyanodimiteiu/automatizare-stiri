#!/usr/bin/env python3
"""
Script premium de rezumat știri conform specificațiilor Luci.
Folosește DeepSeek API pentru a genera rezumate structurate cu imagini.
FIX: sistem robust de fallback pentru imagini (3 nivele)
"""
import feedparser
import requests
import os
import json
import re
import sys
import random
import time
from urllib.parse import urlparse, quote

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

# ─── Imagini statice per tag (Unsplash CDN - întotdeauna disponibile) ─────────
# Format: ?w=800&q=80 => resize automat, fără copyright
IMAGE_LIBRARY = {
    "#AI": [
        "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=800&q=80",
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800&q=80",
        "https://images.unsplash.com/photo-1593508512255-86ab42a8e620?w=800&q=80",
    ],
    "#Tech": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80",
        "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800&q=80",
        "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=800&q=80",
    ],
    "#Crypto": [
        "https://images.unsplash.com/photo-1621416894562-7a5e768f8b1a?w=800&q=80",
        "https://images.unsplash.com/photo-1622630998477-20aa696ecb05?w=800&q=80",
        "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800&q=80",
    ],
    "#Bitcoin": [
        "https://images.unsplash.com/photo-1591994843349-f415893b3a6b?w=800&q=80",
        "https://images.unsplash.com/photo-1640826514546-7b7e7ab0b3f3?w=800&q=80",
    ],
    "#Macro": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80",
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=800&q=80",
        "https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?w=800&q=80",
    ],
    "#Finanțe": [
        "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=800&q=80",
        "https://images.unsplash.com/photo-1565514020179-026b92b2d70b?w=800&q=80",
    ],
    "#EnergieVerde": [
        "https://images.unsplash.com/photo-1509391366360-2e959784a276?w=800&q=80",
        "https://images.unsplash.com/photo-1508514177221-188b1cf16e9d?w=800&q=80",
    ],
    "#Eolian": [
        "https://images.unsplash.com/photo-1466611653911-95081537e5b7?w=800&q=80",
        "https://images.unsplash.com/photo-1532601224476-15c79f2f7a51?w=800&q=80",
    ],
    "#Energie": [
        "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?w=800&q=80",
        "https://images.unsplash.com/photo-1545173168-9f1947eebb7f?w=800&q=80",
    ],
    "#Auto": [
        "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800&q=80",
        "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800&q=80",
    ],
    "#Semiconductori": [
        "https://images.unsplash.com/photo-1618044733300-9472054094ee?w=800&q=80",
        "https://images.unsplash.com/photo-1601132359864-791a4a5d4a8c?w=800&q=80",
    ],
    "#Cybersecurity": [
        "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800&q=80",
        "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
    ],
    "#Geopolitică": [
        "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&q=80",
        "https://images.unsplash.com/photo-1523995462485-3d171b5c8fa9?w=800&q=80",
    ],
    "#Startup": [
        "https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=800&q=80",
        "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800&q=80",
    ],
}

# ─── Imagine absolute fallback (garantat funcționale) ─────────────────────────
FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&q=80",  # news generic
    "https://images.unsplash.com/photo-1586339949916-3e9457bef6d3?w=800&q=80",  # newspaper
    "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=800&q=80",  # media
]

# Mapping cuvinte cheie -> tag-uri
KEYWORD_TO_TAG = {
    "ai": "#AI", "inteligență": "#AI", "artificial": "#AI",
    "machine learning": "#AI", "llm": "#AI", "chatgpt": "#AI", "openai": "#AI",
    "tech": "#Tech", "tehnologie": "#Tech", "gadget": "#Tech",
    "innovation": "#Tech", "inovație": "#Tech",
    "crypto": "#Crypto", "criptomonede": "#Crypto", "ethereum": "#Crypto", "blockchain": "#Crypto",
    "bitcoin": "#Bitcoin",
    "finanțe": "#Finanțe", "finante": "#Finanțe",
    "economie": "#Macro", "bursa": "#Macro", "market": "#Macro",
    "fed": "#Macro", "inflație": "#Macro",
    "solar": "#EnergieVerde", "fotovoltaic": "#EnergieVerde", "renewable": "#EnergieVerde",
    "energie": "#Energie", "energy": "#Energie",
    "eolian": "#Eolian", "wind": "#Eolian",
    "auto": "#Auto", "mașină": "#Auto", "electric": "#Auto",
    "semiconductori": "#Semiconductori", "chip": "#Semiconductori",
    "cybersecurity": "#Cybersecurity", "securitate": "#Cybersecurity", "hack": "#Cybersecurity",
    "geopolitică": "#Geopolitică", "conflict": "#Geopolitică",
    "startup": "#Startup", "finanțare": "#Startup",
}


# ─── Config ───────────────────────────────────────────────────────────────────

def incarca_config():
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
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


# ─── Telegram comenzi ─────────────────────────────────────────────────────────

def verifica_comenzi_telegram(config):
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
                    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                                  data={"chat_id": chat_id, "text": txt})
                elif text.startswith("/adauga_keyword"):
                    k = text.replace("/adauga_keyword ", "").strip().lower()
                    if k and k not in config["keywords"]:
                        config["keywords"].append(k)
                        salveaza_config(config)
                        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                                      data={"chat_id": chat_id, "text": f"✅ Adaugat: {k}"})
    except:
        pass
    return config


# ─── AI duplicate check ───────────────────────────────────────────────────────

def verifica_duplicat_ai(titlu, istoric):
    if not istoric or not DEEPSEEK_KEY:
        return False
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    try:
        res = requests.post(url, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": f"Titlu: {titlu}. Istoric: {istoric}. Daca e acelasi subiect, zi DA, altfel NU."}],
            "temperature": 0.1
        }, headers=headers, timeout=10).json()
        return "DA" in res['choices'][0]['message']['content'].upper()
    except:
        return False


# ─── IMAGINE - sistem cu 3 nivele de fallback ─────────────────────────────────

def verifica_url_imagine(url, timeout=8):
    """Verifică dacă un URL de imagine este accesibil (returnează True/False)."""
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        content_type = resp.headers.get("Content-Type", "")
        return resp.status_code == 200 and "image" in content_type
    except:
        return False

def extrage_imagine_rss(entry):
    """Nivel 1: Extrage imaginea direct din RSS feed."""
    # media:content
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if media.get('type', '').startswith('image/'):
                url = media.get('url', '')
                if url:
                    return url
    # enclosures
    if hasattr(entry, 'enclosures'):
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image/'):
                url = enc.get('href', '')
                if url:
                    return url
    # img în summary HTML
    if hasattr(entry, 'summary'):
        imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', entry.summary)
        if imgs:
            return imgs[0]
    return None

def genereaza_imagine_pollinations(titlu):
    """Nivel 2: Generează imagine AI cu Pollinations (gratis, fără key)."""
    # Prompt scurt în engleză pentru rezultate mai bune
    prompt = f"professional news photo, {titlu[:80]}, photorealistic, high quality"
    prompt_encoded = quote(prompt)
    # Seed random pentru a evita cache
    seed = random.randint(1000, 9999)
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=800&height=450&nologo=true&seed={seed}"
    print(f"🎨 Pollinations: generez imagine... ({url[:80]}...)")
    # Pollinations are nevoie de GET (nu HEAD) pentru a genera
    try:
        resp = requests.get(url, timeout=20, stream=True)
        if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
            return url
    except Exception as e:
        print(f"   ⚠️  Pollinations a picat: {e}")
    return None

def alege_imagine_statica(tag):
    """Nivel 3: Alege imagine statică din librărie Unsplash (garantat funcțională)."""
    pool = IMAGE_LIBRARY.get(tag, []) or IMAGE_LIBRARY.get("#Tech", [])
    if pool:
        return random.choice(pool)
    return random.choice(FALLBACK_IMAGES)

def obtine_imagine(entry, titlu, tag):
    """
    Sistem cu 3 nivele de fallback:
    1. Imagine din RSS feed
    2. Generare AI cu Pollinations
    3. Imagine statică Unsplash per tag
    """
    # NIVEL 1: RSS
    img = extrage_imagine_rss(entry)
    if img:
        print(f"   📷 Nivel 1 (RSS): {img[:60]}...")
        return img

    # NIVEL 2: Pollinations AI
    img = genereaza_imagine_pollinations(titlu)
    if img:
        print(f"   🎨 Nivel 2 (Pollinations AI): imagine generată")
        return img

    # NIVEL 3: Static Unsplash
    img = alege_imagine_statica(tag)
    print(f"   🖼️  Nivel 3 (Static Unsplash): {img[:60]}...")
    return img


# ─── Tag ──────────────────────────────────────────────────────────────────────

def determina_tag(titlu, descriere):
    text = (titlu + ' ' + descriere).lower()
    for kw, tag in KEYWORD_TO_TAG.items():
        if kw in text:
            return tag
    return "#Tech"


# ─── Rezumat DeepSeek ─────────────────────────────────────────────────────────

def genereaza_rezumat_premium(titlu, descriere, tag, limit_chars):
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


# ─── Trimitere Telegram ───────────────────────────────────────────────────────

def trimite_pe_telegram(imagine_url, rezumat_text):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("⚠️  Token sau chat ID Telegram lipsă.")
        return False

    # Încearcă sendPhoto
    if imagine_url:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        data = {
            "chat_id": TG_CHAT_ID,
            "photo": imagine_url,
            "caption": rezumat_text[:1024],  # Telegram limită caption 1024 chars
            "parse_mode": "Markdown"
        }
        try:
            resp = requests.post(url, data=data, timeout=30)
            result = resp.json()
            if result.get("ok"):
                print("   ✅ Imagine trimisă cu succes!")
                return True
            else:
                # Afișează eroarea Telegram pentru debug
                print(f"   ⚠️  sendPhoto eșuat: {result.get('description', 'unknown error')}")
        except Exception as e:
            print(f"   ⚠️  Eroare sendPhoto: {e}")

    # Dacă caption e prea lung, trimite foto + text separat
    if imagine_url:
        try:
            url_foto = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
            resp = requests.post(url_foto, data={
                "chat_id": TG_CHAT_ID,
                "photo": imagine_url
            }, timeout=30)
            if resp.json().get("ok"):
                # Trimite textul separat
                url_text = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                requests.post(url_text, data={
                    "chat_id": TG_CHAT_ID,
                    "text": rezumat_text,
                    "parse_mode": "Markdown"
                }, timeout=30)
                print("   ✅ Foto + text trimise separat!")
                return True
        except Exception as e:
            print(f"   ⚠️  Eroare foto separat: {e}")

    # Fallback final: doar text
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {
        "chat_id": TG_CHAT_ID,
        "text": rezumat_text,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, data=data, timeout=30)
        if resp.json().get("ok"):
            print("   ⚠️  Trimis fără imagine (doar text).")
            return True
    except Exception as e:
        print(f"Eroare trimitere Telegram: {e}")
    return False


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    config = incarca_config()
    config = verifica_comenzi_telegram(config)

    # Încarcă istoric
    if not os.path.exists(DB_FILE):
        open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f:
        lines = f.read().splitlines()
    istoric_links = {l.split('|')[0] for l in lines if '|' in l}
    titluri_vechi = [l.split('|')[1] for l in lines[-20:] if '|' in l]

    for rss_url in config["rss_urls"]:
        try:
            print(f"\n📡 Procesez feed: {rss_url}")
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:10]:
                if entry.link in istoric_links:
                    continue

                text = (entry.title + ' ' + entry.get('summary', '')).lower()
                if not any(kw.lower() in text for kw in config["keywords"]):
                    continue

                if verifica_duplicat_ai(entry.title, titluri_vechi):
                    print(f"   🔁 Duplicat: {entry.title[:50]}")
                    continue

                print(f"\n📰 Articol găsit: {entry.title[:60]}")

                tag = determina_tag(entry.title, entry.get('summary', ''))
                print(f"   🏷️  Tag: {tag}")

                # Obține imagine (3 nivele fallback)
                imagine_url = obtine_imagine(entry, entry.title, tag)

                # Generează rezumat
                rezumat = genereaza_rezumat_premium(
                    entry.title,
                    entry.get('summary', ''),
                    tag,
                    config.get("limit_chars", 800)
                )
                if not rezumat:
                    print("   ❌ Nu s-a putut genera rezumatul.")
                    continue

                # Trimite pe Telegram
                success = trimite_pe_telegram(imagine_url, rezumat)
                if success:
                    with open(DB_FILE, "a") as f:
                        f.write(f"{entry.link}|{entry.title}\n")
                    print(f"   ✅ Trimis cu succes: {entry.title[:50]}")
                    return  # Oprește după primul articol reușit
                else:
                    print("   ❌ Eroare la trimitere Telegram.")

        except Exception as e:
            print(f"Eroare procesare feed {rss_url}: {e}")
            continue

    print("\n✅ Run complet.")

if __name__ == "__main__":
    main()
