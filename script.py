#!/usr/bin/env python3
"""
Script premium de rezumat știri - Luci v3
FIX: imagini unice per știre (anti-duplicat), 3 nivele fallback
"""
import feedparser
import requests
import os
import json
import re
import random
from urllib.parse import quote

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "stiri_trimise.txt")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config_bot.json")

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

# ─── Librărie imagini statice Unsplash (garantat funcționale, diverse) ────────
IMAGE_LIBRARY = {
    "#AI": [
        "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=800&q=80",
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800&q=80",
        "https://images.unsplash.com/photo-1593508512255-86ab42a8e620?w=800&q=80",
        "https://images.unsplash.com/photo-1655720031554-a929595ffad7?w=800&q=80",
        "https://images.unsplash.com/photo-1531746790731-6c087fecd65a?w=800&q=80",
    ],
    "#Tech": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80",
        "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800&q=80",
        "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=800&q=80",
        "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800&q=80",
        "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&q=80",
    ],
    "#Crypto": [
        "https://images.unsplash.com/photo-1621416894562-7a5e768f8b1a?w=800&q=80",
        "https://images.unsplash.com/photo-1622630998477-20aa696ecb05?w=800&q=80",
        "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800&q=80",
    ],
    "#Bitcoin": [
        "https://images.unsplash.com/photo-1591994843349-f415893b3a6b?w=800&q=80",
        "https://images.unsplash.com/photo-1640826514546-7b7e7ab0b3f3?w=800&q=80",
        "https://images.unsplash.com/photo-1518546305927-5a555bb7020d?w=800&q=80",
    ],
    "#Macro": [
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80",
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=800&q=80",
        "https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?w=800&q=80",
        "https://images.unsplash.com/photo-1535320903710-d993d3d77d29?w=800&q=80",
    ],
    "#Finanțe": [
        "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=800&q=80",
        "https://images.unsplash.com/photo-1565514020179-026b92b2d70b?w=800&q=80",
        "https://images.unsplash.com/photo-1559526324-593bc073d938?w=800&q=80",
    ],
    "#EnergieVerde": [
        "https://images.unsplash.com/photo-1509391366360-2e959784a276?w=800&q=80",
        "https://images.unsplash.com/photo-1508514177221-188b1cf16e9d?w=800&q=80",
        "https://images.unsplash.com/photo-1466611653911-95081537e5b7?w=800&q=80",
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
        "https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=800&q=80",
    ],
    "#Semiconductori": [
        "https://images.unsplash.com/photo-1618044733300-9472054094ee?w=800&q=80",
        "https://images.unsplash.com/photo-1601132359864-791a4a5d4a8c?w=800&q=80",
    ],
    "#Cybersecurity": [
        "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800&q=80",
        "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800&q=80",
        "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800&q=80",
    ],
    "#Geopolitică": [
        "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&q=80",
        "https://images.unsplash.com/photo-1523995462485-3d171b5c8fa9?w=800&q=80",
    ],
    "#Startup": [
        "https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=800&q=80",
        "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800&q=80",
        "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800&q=80",
    ],
}

FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&q=80",
    "https://images.unsplash.com/photo-1586339949916-3e9457bef6d3?w=800&q=80",
    "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=800&q=80",
    "https://images.unsplash.com/photo-1432821596592-e2c18b78144f?w=800&q=80",
    "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?w=800&q=80",
]

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


# ─── Duplicate check ──────────────────────────────────────────────────────────

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


# ─── Imagine ──────────────────────────────────────────────────────────────────

def img_key(url):
    """Extrage un identificator unic din URL-ul imaginii."""
    m = re.search(r'photo-([a-z0-9]+)', url)
    return m.group(1) if m else url[:100]

def extrage_imagine_rss(entry):
    """Nivel 1: imagine direct din feed RSS."""
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if media.get('type', '').startswith('image/'):
                return media.get('url')
    if hasattr(entry, 'enclosures'):
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image/'):
                return enc.get('href')
    if hasattr(entry, 'summary'):
        imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', entry.summary)
        if imgs:
            return imgs[0]
    return None

def genereaza_imagine_pollinations(titlu):
    """Nivel 2: generare AI Pollinations (fără API key, gratis)."""
    prompt = f"professional news photography, {titlu[:80]}, editorial style, high quality"
    seed = random.randint(10000, 99999)  # seed unic = imagine unică
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=800&height=450&nologo=true&seed={seed}"
    print(f"   🎨 Pollinations: generez (seed={seed})...")
    try:
        resp = requests.get(url, timeout=20, stream=True)
        if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
            return url
    except Exception as e:
        print(f"      ⚠️  Pollinations picat: {e}")
    return None

def obtine_imagine(entry, titlu, tag, imagini_folosite: set):
    """
    Alege imaginea cu 3 nivele de fallback + garanție anti-duplicat.
    imagini_folosite: set cu cheile imaginilor deja trimise (din DB + sesiunea curentă).
    """
    # NIVEL 1: RSS feed
    url = extrage_imagine_rss(entry)
    if url and img_key(url) not in imagini_folosite:
        print(f"   📷 Nivel 1 (RSS): {url[:70]}...")
        imagini_folosite.add(img_key(url))
        return url

    # NIVEL 2: Pollinations AI (seed random = mereu unică)
    url = genereaza_imagine_pollinations(titlu)
    if url:
        print(f"   🎨 Nivel 2 (Pollinations): OK")
        return url  # seed garantează unicitate

    # NIVEL 3: Unsplash static - alegem prima neutilizată
    pool = IMAGE_LIBRARY.get(tag, []) + IMAGE_LIBRARY.get("#Tech", []) + FALLBACK_IMAGES
    random.shuffle(pool)
    for candidate in pool:
        if img_key(candidate) not in imagini_folosite:
            print(f"   🖼️  Nivel 3 (Unsplash static): {candidate[:70]}...")
            imagini_folosite.add(img_key(candidate))
            return candidate

    # Pool epuizat (extrem de rar) - refolosim random
    fallback = random.choice(FALLBACK_IMAGES)
    print(f"   🔄 Pool epuizat, refolosim imagine.")
    return fallback


# ─── Tag ──────────────────────────────────────────────────────────────────────

def determina_tag(titlu, descriere):
    text = (titlu + ' ' + descriere).lower()
    for kw, tag in KEYWORD_TO_TAG.items():
        if kw in text:
            return tag
    return "#Tech"


# ─── DeepSeek rezumat ─────────────────────────────────────────────────────────

def genereaza_rezumat_premium(titlu, descriere, tag, limit_chars):
    if not DEEPSEEK_KEY:
        return None
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    prompt = f"""
E�ti un jurnalist de elită, cu zeci de ani de experiență în publicații de prestigiu (stil Bloomberg/Reuters). 
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
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Eroare DeepSeek: {e}")
        return None


# ─── Trimitere Telegram ───────────────────────────────────────────────────────

def trimite_pe_telegram(imagine_url, rezumat_text):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("⚠️  Token sau chat ID Telegram lipsă.")
        return False

    caption = rezumat_text[:1024]  # limita Telegram

    # Încearcă sendPhoto cu caption
    if imagine_url:
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                data={"chat_id": TG_CHAT_ID, "photo": imagine_url,
                      "caption": caption, "parse_mode": "Markdown"},
                timeout=30
            )
            result = resp.json()
            if result.get("ok"):
                print("   ✅ Foto + caption trimise!")
                return True
            print(f"   ⚠️  sendPhoto eșuat: {result.get('description')}")
        except Exception as e:
            print(f"   ⚠️  Eroare sendPhoto: {e}")

        # Fallback: foto fără caption, apoi text separat
        try:
            r1 = requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                data={"chat_id": TG_CHAT_ID, "photo": imagine_url},
                timeout=30
            )
            if r1.json().get("ok"):
                requests.post(
                    f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                    data={"chat_id": TG_CHAT_ID, "text": rezumat_text, "parse_mode": "Markdown"},
                    timeout=30
                )
                print("   ✅ Foto + text separat trimise!")
                return True
        except Exception as e:
            print(f"   ⚠️  Eroare foto separat: {e}")

    # Fallback final: doar text
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT_ID, "text": rezumat_text, "parse_mode": "Markdown"},
            timeout=30
        )
        if resp.json().get("ok"):
            print("   ⚠️  Trimis fără imagine.")
            return True
    except Exception as e:
        print(f"Eroare Telegram: {e}")
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

    # Cheile imaginilor din ultimele 50 știri → nu le repetăm
    imagini_folosite = set()
    for l in lines[-50:]:
        parts = l.split('|')
        if len(parts) >= 3 and parts[2].strip():
            imagini_folosite.add(parts[2].strip())
    print(f"🗂️  Imagini excluse (deja trimise): {len(imagini_folosite)}")

    for rss_url in config["rss_urls"]:
        try:
            print(f"\n📡 Feed: {rss_url}")
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:10]:
                if entry.link in istoric_links:
                    continue
                text = (entry.title + ' ' + entry.get('summary', '')).lower()
                if not any(kw.lower() in text for kw in config["keywords"]):
                    continue
                if verifica_duplicat_ai(entry.title, titluri_vechi):
                    print(f"   🔁 Duplicat titlu: {entry.title[:50]}")
                    continue

                print(f"\n📰 Articol: {entry.title[:65]}")
                tag = determina_tag(entry.title, entry.get('summary', ''))
                print(f"   🏷️  Tag: {tag}")

                imagine_url = obtine_imagine(entry, entry.title, tag, imagini_folosite)

                rezumat = genereaza_rezumat_premium(
                    entry.title, entry.get('summary', ''), tag, config.get("limit_chars", 800)
                )
                if not rezumat:
                    print("   ❌ Rezumat eșuat.")
                    continue

                success = trimite_pe_telegram(imagine_url, rezumat)
                if success:
                    # Salvăm: link | titlu | cheia imaginii
                    key = img_key(imagine_url)
                    with open(DB_FILE, "a") as f:
                        f.write(f"{entry.link}|{entry.title}|{key}\n")
                    print(f"   ✅ Gata: {entry.title[:50]}")
                    return
                else:
                    print("   ❌ Telegram eșuat.")

        except Exception as e:
            print(f"Eroare feed {rss_url}: {e}")

    print("\n✅ Run complet.")

if __name__ == "__main__":
    main()
