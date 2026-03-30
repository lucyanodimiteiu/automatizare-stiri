#!/usr/bin/env python3
"""
Script premium de rezumat stiri - Luci v4
- Prompt vizual generat LOCAL (fara API extra)
- Pollinations Flux model pentru imagini AI de calitate
- Anti-duplicat imagini + 3 nivele fallback
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
        "https://cointelegraph.com/rss",
        "https://www.digi24.ro/rss/stiri/economie",
        "http://feeds.marketwatch.com/marketwatch/topstories/",
        "https://www.reutersagency.com/feed/?best-topics=business"
    ],
    "keywords": ["economie", "finante", "bursa", "tech", "market", "fed", "bitcoin", "trump"],
    "limit_chars": 800
}

# ─── Librarie imagini statice Unsplash (fallback final) ───────────────────────
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
    "#Finante": [
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
    "#Geopolitica": [
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
    "ai": "#AI", "artificial": "#AI", "machine learning": "#AI",
    "llm": "#AI", "chatgpt": "#AI", "openai": "#AI",
    "tech": "#Tech", "tehnologie": "#Tech", "gadget": "#Tech",
    "crypto": "#Crypto", "ethereum": "#Crypto", "blockchain": "#Crypto",
    "bitcoin": "#Bitcoin",
    "economie": "#Macro", "bursa": "#Macro", "market": "#Macro",
    "fed": "#Macro", "inflatie": "#Macro",
    "finante": "#Finante", "finance": "#Finante",
    "solar": "#EnergieVerde", "renewable": "#EnergieVerde",
    "energie": "#Energie", "energy": "#Energie",
    "eolian": "#Eolian", "wind": "#Eolian",
    "auto": "#Auto", "electric vehicle": "#Auto", "tesla": "#Auto",
    "semiconductori": "#Semiconductori", "chip": "#Semiconductori", "nvidia": "#Semiconductori",
    "cybersecurity": "#Cybersecurity", "hack": "#Cybersecurity", "ransomware": "#Cybersecurity",
    "geopolitica": "#Geopolitica", "conflict": "#Geopolitica", "war": "#Geopolitica",
    "startup": "#Startup",
    "solana": "#Crypto",
    "ripple": "#Crypto",
    "xrp": "#Crypto",
    "defi": "#Crypto",
    "nft": "#Crypto",
    "altcoin": "#Crypto",
    "web3": "#Tech",
    "stablecoin": "#Crypto",
    "coinbase": "#Crypto",
    "binance": "#Crypto",
    "etf": "#Macro",
}

# ─── Dictionar de scene vizuale per concept ───────────────────────────────────
# Folosit de constructorul de prompt local - fara niciun API
SCENE_MAP = {
    # Companii / persoane notabile
    "trump": "Donald Trump speaking at a podium with American flags",
    "elon musk": "Elon Musk in a modern tech office with screens",
    "fed": "Federal Reserve building exterior in Washington DC, classical architecture",
    "nvidia": "rows of glowing GPU server racks in a data center, green light",
    "apple": "Apple headquarters glass building in Cupertino, California",
    "tesla": "Tesla electric car on a highway at sunset",
    "amazon": "Amazon warehouse with robotic arms sorting packages",
    "google": "Google campus colorful modern buildings",
    "microsoft": "Microsoft office building modern glass architecture",
    "openai": "futuristic AI research lab with holographic displays",
    # Concepte financiare
    "bitcoin": "golden bitcoin coin on a dark reflective surface, dramatic lighting",
    "crypto": "cryptocurrency trading screen with green and red charts, dark room",
    "blockchain": "abstract network of connected glowing nodes, blue light, digital",
    "bursa": "New York Stock Exchange trading floor, busy traders, screens everywhere",
    "stock market": "Wall Street stock exchange trading floor with digital displays",
    "inflation": "shopping cart with groceries, price tags, supermarket aisle",
    "recession": "empty office building, deserted financial district streets, grey sky",
    "interest rate": "bank building exterior, classical columns, financial district",
    "gold": "shiny gold bars stacked in a vault, warm yellow light",
    "dollar": "US dollar bills close up, crisp detail, green tones",
    "oil": "oil refinery at sunset with flames, industrial pipes",
    "petrol": "oil pump jack in open field at golden hour",
    # Tech
    "ai": "humanoid robot and human shaking hands in a bright futuristic lab",
    "artificial intelligence": "glowing neural network visualization in dark space, blue purple",
    "semiconductor": "extreme close up of microchip circuit board, neon light reflections",
    "chip": "silicon wafer with microchips under bright lab lighting",
    "data center": "long corridor of server racks with blue LED lights, fog effect",
    "robot": "industrial robot arm welding in a factory, sparks flying",
    "electric car": "sleek electric car charging at a station at dusk, blue glow",
    "solar": "solar panel farm in a sunny desert landscape, aerial view",
    "wind": "offshore wind turbines in the ocean at sunset, dramatic sky",
    "cybersecurity": "hooded hacker at a keyboard, multiple screens with code, dark room",
    "hack": "digital lock broken on a dark screen, red alert glow",
    # Macro / geopolitica
    "war": "diplomatic meeting room, flags, negotiation table",
    "sanctions": "cargo ships blocked at a port, cranes idle, overcast sky",
    "trade": "busy international cargo port, containers stacked high, cranes",
    "tariff": "shipping containers at a port with customs inspection",
    "china": "Shanghai skyline at night with glowing skyscrapers",
    "europe": "European Parliament building in Brussels, EU flags",
    "inflation": "empty supermarket shelves, worried shopper",
    # Energie
    "nuclear": "nuclear power plant cooling towers with steam, sunrise",
    "gas": "natural gas pipelines through a green landscape",
    "coal": "coal power plant with smoke stacks at dusk",
    # Crypto specific - stil Cointelegraph
    "solana": "glowing Solana logo SOL coin, dark background, purple neon, 3D render",
    "xrp": "XRP Ripple coin glowing blue, dark background, digital art, 3D illustration",
    "ripple": "Ripple XRP logo glowing, dark background, blue neon, futuristic",
    "defi": "decentralized finance concept, floating coins and chains, dark neon background, 3D illustration",
    "nft": "NFT digital art floating frames, colorful glow, dark background, 3D render",
    "altcoin": "multiple cryptocurrency coins floating, neon glow, dark background, 3D digital art",
    "stablecoin": "USDT USDC stable coins on dark background, green glow, digital illustration",
    "web3": "Web3 decentralized network nodes, glowing connections, dark space background, 3D render",
    "etf": "Bitcoin ETF approval concept, golden BTC coin with stock chart, dark background, 3D illustration",
    "coinbase": "Coinbase exchange logo glowing blue, dark background, 3D digital art",
    "binance": "Binance BNB golden coin glowing, dark background, neon accent, 3D render",
    "whale": "large crypto whale underwater with coins, dark ocean, neon blue glow, digital art",
    "mining": "Bitcoin mining rig with glowing GPUs in dark room, blue and orange neon light",
    "wallet": "digital crypto wallet glowing, dark background, neon coins floating, 3D illustration",
    # Default
    "economy": "aerial view of a busy city financial district at dawn",
    "business": "modern glass office building exterior, city skyline",
    "market": "financial trading floor with screens showing charts",
}

# ─── Stiluri ilustratie - inspirat din estetica Cointelegraph ────────────────
# Ilustratii 3D digitale cu elemente crypto, fundal inchis, accente neon
PHOTO_STYLES = [
    "3D digital illustration, dark background, neon glow accents, crypto themed, Cointelegraph art style, octane render, high detail",
    "isometric 3D illustration, dark navy background, glowing neon elements, futuristic crypto aesthetic, professional digital art",
    "3D render, dark gradient background, vivid neon colors, blockchain themed, stylized characters, Cointelegraph magazine cover style",
    "digital art illustration, dark background, golden and blue neon glow, crypto coins floating, cinematic composition, high quality 3D",
    "stylized 3D illustration, cyberpunk dark background, holographic elements, crypto finance themed, vivid accent colors, concept art",
]


# ─── FUNCTIA PRINCIPALA: construieste prompt vizual LOCAL, fara API ───────────

def construieste_prompt_vizual(titlu, descriere, tag):
    """
    Construieste un prompt detaliat pentru Pollinations bazat pe continutul
    articolului. Zero API calls, zero costuri extra.

    Logica:
    1. Cauta entitati cheie (companii, persoane, concepte) in text
    2. Mapeaza la scene vizuale concrete
    3. Adauga context din tag + stil fotografic random
    4. Returneaza prompt gata de trimis la Pollinations
    """
    text = (titlu + " " + descriere).lower()
    text_clean = re.sub(r'<[^>]+>', '', text)  # scoate HTML daca exista

    # Colecteaza scene relevante gasite in text
    scene_hits = []
    for keyword, scene in SCENE_MAP.items():
        if keyword in text_clean:
            scene_hits.append((keyword, scene))

    # Extrage cifre/procente importante din titlu (ex: "10%", "$500B", "2024")
    numbers = re.findall(r'\$[\d,.]+[BMK]?|\d+[\.,]\d+%?|\b\d{4}\b', titlu)
    number_context = ""
    if numbers:
        number_context = f"with visible context of {', '.join(numbers[:2])}"

    # Construieste scena principala
    if scene_hits:
        # Sorteaza dupa lungimea keywordului (mai lung = mai specific)
        scene_hits.sort(key=lambda x: len(x[0]), reverse=True)
        main_scene = scene_hits[0][1]

        # Daca avem 2+ hits, combina elementele
        if len(scene_hits) >= 2:
            secondary = scene_hits[1][1].split(",")[0]  # doar prima parte
            main_scene = main_scene + f", with {secondary} in background"
    else:
        # Fallback bazat pe tag
        tag_scenes = {
            "#AI": "humanoid robot in a modern research laboratory, glowing screens",
            "#Tech": "modern technology office with holographic displays and developers",
            "#Crypto": "cryptocurrency trading screens in a dark room, green charts",
            "#Bitcoin": "golden bitcoin symbol on dark background, dramatic spotlight",
            "#Macro": "aerial view of financial district skyscrapers at dawn",
            "#Finante": "bank vault interior with gold bars, professional lighting",
            "#EnergieVerde": "solar panel farm and wind turbines in green landscape",
            "#Energie": "power plant at sunset with dramatic sky",
            "#Auto": "modern electric car on empty road at sunset",
            "#Semiconductori": "microchip manufacturing cleanroom, workers in white suits",
            "#Cybersecurity": "network security operations center, multiple screens, dark room",
            "#Geopolitica": "world map with diplomatic meeting, flags of nations",
            "#Startup": "modern startup office with young professionals collaborating",
            "#Eolian": "wind turbines in the ocean at golden hour",
        }
        main_scene = tag_scenes.get(tag, "modern city financial district at dawn, busy streets")

    # Alege stil fotografic random pentru varietate
    style = random.choice(PHOTO_STYLES)

    # Asambleaza promptul final
    prompt_parts = [main_scene]
    if number_context:
        prompt_parts.append(number_context)
    prompt_parts.append(style)
    prompt_parts.append("no text overlays, no watermarks, high resolution, sharp details, dramatic lighting")

    final_prompt = ", ".join(prompt_parts)

    print(f"   💡 Prompt vizual: {final_prompt[:120]}...")
    return final_prompt


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
                    txt = "CONFIG:\nSurse: {}\nKeywords: {}...".format(
                        len(config["rss_urls"]), ", ".join(config["keywords"][:10]))
                    requests.post(
                        "https://api.telegram.org/bot{}/sendMessage".format(TG_TOKEN),
                        data={"chat_id": chat_id, "text": txt})
                elif text.startswith("/adauga_keyword"):
                    k = text.replace("/adauga_keyword ", "").strip().lower()
                    if k and k not in config["keywords"]:
                        config["keywords"].append(k)
                        salveaza_config(config)
                        requests.post(
                            "https://api.telegram.org/bot{}/sendMessage".format(TG_TOKEN),
                            data={"chat_id": chat_id, "text": "Adaugat: {}".format(k)})
    except:
        pass
    return config


# ─── Duplicate check ──────────────────────────────────────────────────────────

def verifica_duplicat_ai(titlu, istoric):
    if not istoric or not DEEPSEEK_KEY:
        return False
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": "Bearer {}".format(DEEPSEEK_KEY), "Content-Type": "application/json"}
    try:
        res = requests.post(url, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Titlu: {}. Istoric: {}. Daca e acelasi subiect, zi DA, altfel NU.".format(titlu, istoric)}],
            "temperature": 0.1
        }, headers=headers, timeout=10).json()
        return "DA" in res["choices"][0]["message"]["content"].upper()
    except:
        return False


# ─── Imagine - sistem cu 3 nivele ─────────────────────────────────────────────

def img_key(url):
    m = re.search(r"photo-([a-z0-9]+)", url)
    return m.group(1) if m else url[:100]

def extrage_imagine_rss(entry):
    if hasattr(entry, "media_content"):
        for media in entry.media_content:
            if media.get("type", "").startswith("image/"):
                return media.get("url")
    if hasattr(entry, "enclosures"):
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image/"):
                return enc.get("href")
    if hasattr(entry, "summary"):
        imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', entry.summary)
        if imgs:
            return imgs[0]
    return None

def genereaza_imagine_pollinations(titlu, descriere, tag):
    """Genereaza imagine AI cu prompt construit local (fara costuri extra)."""
    prompt = construieste_prompt_vizual(titlu, descriere, tag)
    seed = random.randint(10000, 99999)
    url = "https://image.pollinations.ai/prompt/{}?width=800&height=450&nologo=true&seed={}&model=flux".format(
        quote(prompt), seed)
    print("   Pollinations Flux: generez (seed={})...".format(seed))
    try:
        resp = requests.get(url, timeout=25, stream=True)
        if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
            return url
    except Exception as e:
        print("   Pollinations picat: {}".format(e))
    return None

def obtine_imagine(entry, titlu, descriere, tag, imagini_folosite):
    # NIVEL 1: RSS
    url = extrage_imagine_rss(entry)
    if url and img_key(url) not in imagini_folosite:
        print("   Nivel 1 (RSS): {}...".format(url[:60]))
        imagini_folosite.add(img_key(url))
        return url

    # NIVEL 2: Pollinations AI cu prompt local
    url = genereaza_imagine_pollinations(titlu, descriere, tag)
    if url:
        print("   Nivel 2 (Pollinations AI): OK")
        return url

    # NIVEL 3: Unsplash static, imagine neunica
    pool = IMAGE_LIBRARY.get(tag, []) + IMAGE_LIBRARY.get("#Tech", []) + FALLBACK_IMAGES
    random.shuffle(pool)
    for candidate in pool:
        if img_key(candidate) not in imagini_folosite:
            print("   Nivel 3 (Unsplash static): {}...".format(candidate[:60]))
            imagini_folosite.add(img_key(candidate))
            return candidate

    return random.choice(FALLBACK_IMAGES)


# ─── Tag ──────────────────────────────────────────────────────────────────────

def determina_tag(titlu, descriere):
    text = (titlu + " " + descriere).lower()
    for kw, tag in KEYWORD_TO_TAG.items():
        if kw in text:
            return tag
    return "#Tech"


# ─── DeepSeek rezumat ─────────────────────────────────────────────────────────

def genereaza_rezumat_premium(titlu, descriere, tag, limit_chars):
    if not DEEPSEEK_KEY:
        return None
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": "Bearer {}".format(DEEPSEEK_KEY), "Content-Type": "application/json"}
    prompt = (
        "Esti un jurnalist de elita, stil Bloomberg/Reuters. "
        "Scrie un text jurnalistic impecabil in romana, fara numerotare, fara bullet points. "
        "2-3 paragrafe scurte. Incepe cu un titlu + emoji relevant. "
        "Integreaza cifrele natural in text. Nu mentiona imaginea. Maxim 2 taguri la final.\n\n"
        "STIREA: {} - {}\nTAG: {}"
    ).format(titlu, descriere, tag)
    try:
        response = requests.post(url, json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": 1000
        }, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("Eroare DeepSeek: {}".format(e))
        return None


# ─── Trimitere Telegram ───────────────────────────────────────────────────────

def trimite_pe_telegram(imagine_url, rezumat_text):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("Token sau chat ID Telegram lipsa.")
        return False

    caption = rezumat_text[:1024]

    if imagine_url:
        try:
            resp = requests.post(
                "https://api.telegram.org/bot{}/sendPhoto".format(TG_TOKEN),
                data={"chat_id": TG_CHAT_ID, "photo": imagine_url,
                      "caption": caption, "parse_mode": "Markdown"},
                timeout=30
            )
            if resp.json().get("ok"):
                print("   Foto + caption trimise!")
                return True
            print("   sendPhoto esuat: {}".format(resp.json().get("description")))
        except Exception as e:
            print("   Eroare sendPhoto: {}".format(e))

        # Foto fara caption + text separat
        try:
            r1 = requests.post(
                "https://api.telegram.org/bot{}/sendPhoto".format(TG_TOKEN),
                data={"chat_id": TG_CHAT_ID, "photo": imagine_url},
                timeout=30
            )
            if r1.json().get("ok"):
                requests.post(
                    "https://api.telegram.org/bot{}/sendMessage".format(TG_TOKEN),
                    data={"chat_id": TG_CHAT_ID, "text": rezumat_text, "parse_mode": "Markdown"},
                    timeout=30
                )
                print("   Foto + text separat trimise!")
                return True
        except Exception as e:
            print("   Eroare foto separat: {}".format(e))

    # Fallback: doar text
    try:
        resp = requests.post(
            "https://api.telegram.org/bot{}/sendMessage".format(TG_TOKEN),
            data={"chat_id": TG_CHAT_ID, "text": rezumat_text, "parse_mode": "Markdown"},
            timeout=30
        )
        if resp.json().get("ok"):
            print("   Trimis fara imagine.")
            return True
    except Exception as e:
        print("Eroare Telegram: {}".format(e))
    return False


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    config = incarca_config()
    config = verifica_comenzi_telegram(config)

    if not os.path.exists(DB_FILE):
        open(DB_FILE, "w").close()
    with open(DB_FILE, "r") as f:
        lines = f.read().splitlines()

    istoric_links = {l.split("|")[0] for l in lines if "|" in l}
    titluri_vechi = [l.split("|")[1] for l in lines[-20:] if "|" in l]

    imagini_folosite = set()
    for l in lines[-50:]:
        parts = l.split("|")
        if len(parts) >= 3 and parts[2].strip():
            imagini_folosite.add(parts[2].strip())
    print("Imagini excluse (deja trimise): {}".format(len(imagini_folosite)))

    for rss_url in config["rss_urls"]:
        try:
            print("\nFeed: {}".format(rss_url))
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:10]:
                if entry.link in istoric_links:
                    continue
                text = (entry.title + " " + entry.get("summary", "")).lower()
                if not any(kw.lower() in text for kw in config["keywords"]):
                    continue
                if verifica_duplicat_ai(entry.title, titluri_vechi):
                    print("   Duplicat: {}".format(entry.title[:50]))
                    continue

                print("\nArticol: {}".format(entry.title[:65]))
                descriere = entry.get("summary", "")
                tag = determina_tag(entry.title, descriere)
                print("   Tag: {}".format(tag))

                imagine_url = obtine_imagine(entry, entry.title, descriere, tag, imagini_folosite)

                rezumat = genereaza_rezumat_premium(
                    entry.title, descriere, tag, config.get("limit_chars", 800))
                if not rezumat:
                    print("   Rezumat esuat.")
                    continue

                success = trimite_pe_telegram(imagine_url, rezumat)
                if success:
                    key = img_key(imagine_url)
                    with open(DB_FILE, "a") as f:
                        f.write("{}|{}|{}\n".format(entry.link, entry.title, key))
                    print("   Gata: {}".format(entry.title[:50]))
                    return
                else:
                    print("   Telegram esuat.")

        except Exception as e:
            print("Eroare feed {}: {}".format(rss_url, e))

    print("\nRun complet.")

if __name__ == "__main__":
    main()
