import asyncio
import edge_tts
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

# Configurare
OUTPUT_FILE = "tiktok_news.mp4"
VOICE = "ro-RO-AlinaNeural"  # Voce feminina (sau ro-RO-EmilNeural pentru masculina)
BG_COLOR = (20, 20, 20)      # Gri inchis
TEXT_COLOR = (255, 255, 255) # Alb
FONT_SIZE = 50

async def genereaza_audio(text, output_audio):
    """Genereaza fisier audio din text folosind Edge TTS"""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_audio)
    print(f"🔊 Audio generat: {output_audio}")

def genereaza_imagine(titlu, continut, output_img):
    """Creeaza o imagine statica cu text pentru video (9:16 format TikTok)"""
    W, H = 1080, 1920
    img = Image.new('RGB', (W, H), color=BG_COLOR)
    d = ImageDraw.Draw(img)

    # Incarca un font (default sau Arial daca exista)
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    # Formateaza textul
    margin = 100
    offset = 400
    
    # Titlu
    lines = textwrap.wrap(titlu, width=25)
    for line in lines:
        d.text((margin, offset), line, font=font_title, fill=(255, 215, 0)) # Auriu
        offset += 80
    
    offset += 50 # Spatiu
    
    # Continut
    lines = textwrap.wrap(continut, width=40)
    for line in lines:
        d.text((margin, offset), line, font=font_body, fill=TEXT_COLOR)
        offset += 50
    
    # Footer
    d.text((margin, H - 200), "#StiriAI #Tech #Inovatie", font=font_body, fill=(0, 200, 255))

    img.save(output_img)
    print(f"🖼️ Imagine generata: {output_img}")

def monteaza_video(audio_path, image_path, output_video):
    """Combina imaginea si sunetul intr-un MP4"""
    # Incarca audio pentru a sti durata
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration + 0.5 # Putina pauza la final

    # Incarca imaginea si seteaza durata
    image_clip = ImageClip(image_path).set_duration(duration)
    
    # Combina
    video = image_clip.set_audio(audio_clip)
    video.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac")
    print(f"🎬 Video final: {output_video}")

async def main():
    # 1. Date de intrare (Simulam o stire)
    titlu = "BREAKING: Noul Model AI de la Google sparge topurile!"
    stire = "Gemini 1.5 Pro tocmai a fost lansat si depaseste GPT-4 in majoritatea testelor. Are o fereastra de context de 1 milion de tokeni! Asta inseamna ca poate citi carti intregi intr-o secunda."

    # 2. Generare
    await genereaza_audio(f"{titlu}. {stire}", "temp_audio.mp3")
    genereaza_imagine(titlu, stire, "temp_img.png")
    monteaza_video("temp_audio.mp3", "temp_img.png", OUTPUT_FILE)

    # 3. Curatenie
    os.remove("temp_audio.mp3")
    os.remove("temp_img.png")
    print("✅ Gata! Verifica fisierul tiktok_news.mp4")

if __name__ == "__main__":
    asyncio.run(main())
