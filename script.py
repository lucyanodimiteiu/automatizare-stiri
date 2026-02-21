import feedparser, requests, os, json, time

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_FILE = "stiri_trimise.txt"
CONFIG_FILE = "config_bot.json"

# Secretul tău din GitHub se numește EXACT: DEEPSEEKAPIKEY
DEEPSEEK_KEY = os.getenv("DEEPSEEKAPIKEY")


def incarca_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"rss_urls": [], "keywords": [], "limit_chars": 900}


def trimite_tg(destinatar_id, text, img=None):
    try:
        if img:
            requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                data={
                    "chat_id": destinatar_id,
                    "photo": img,
                    "caption": text,
                    "parse_mode": "Markdown"
                },
                timeout=15
            )
        else:
            requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                data={
                    "chat_id": destinatar_id,
                    "text": text,
                    "parse_mode": "Markdown"
                },
                timeout=15
            )
    except:
        pass


def rezuma_cu_deepseek(prompt):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "Ești un asistent care rezumă știri în română, clar, concis și cu emoji."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    r = requests.post(url, headers=headers, json=data, timeout=20)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def main():
    config = incarca_config()

    if not os.path.exists(DB_FILE):
        open(DB_FILE, "w").close()

    with open(DB_FILE, "r") as f:
        istoric = f.read()

    for url in config["rss_urls"]:
        try:
            feed = feedparser.parse(url)

            for entry in feed.entries[:5]:
                if entry.link not in istoric:

                    full_text = (entry.title + " " + entry.get('summary', '')).lower()

                    if any(k in full_text for k in config["keywords"]):

                        prompt = f"""
                        Analizează știrea asta: "{entry.title} - {entry.get('summary', '')}"
                        1. Fă un rezumat scurt în română (max 3 idei principale, cu emoji).
                        2. Identifică sentimentul pieței (Pozitiv 🟢 / Neutru 🟡 / Negativ 🔴).
                        3. Extrage 2-3 hashtag-uri relevante (#Bitcoin, #AI, etc).

                        Format dorit:
                        *Titlu (Bold)*
                        Rezumat...
                        Hashtags...
                        Sentiment: 🟢/🔴
                        Link original: {entry.link}
                        """

                        try:
                            raspuns = rezuma_cu_deepseek(prompt)

                            img = None
                            if 'media_content' in entry:
                                img = entry.media_content[0]['url']

                            trimite_tg(TG_CHAT_ID, raspuns, img)

                            with open(DB_FILE, "a") as f:
                                f.write(f"{entry.link}\n")

                        except Exception as e:
                            print("Eroare DeepSeek:", e)

                        time.sleep(2)

        except Exception as e:
            print(f"Eroare la procesarea {url}: {e}")


if __name__ == "__main__":
    main()
