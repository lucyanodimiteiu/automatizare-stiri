import feedparser
import requests
import os
import sqlite3
import google.generativeai as genai
import time

# ================= CONFIG =================
RSS_URLS = [
    "https://www.digi24.ro/rss",
    "https://www.hotnews.ro/rss"
]

DB_FILE = "stiri.db"

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FB_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_ID = os.getenv("FB_PAGE_ID")

# ============== AI CONFIG =================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
ai = genai.GenerativeModel("gemini-1.5-flash")

# ============== DATABASE ==================
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS stiri (
    link TEXT PRIMARY KEY,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# ============== FUNCTIONS =================
def exista(link):
    cursor.execute("SELECT 1 FROM stiri WHERE link=?", (link,))
    return cursor.fetchone() is not None

def salveaza(link):
    cursor.execute("INSERT INTO stiri

