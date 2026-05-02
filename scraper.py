import telebot
import requests
from bs4 import BeautifulSoup
import time
import threading
import schedule
import os
from flask import Flask
from telebot import types # Tugmalar uchun

# --- SOZLAMALAR ---
BOT_TOKEN = "8748456961:AAGKng_Y0vwE5o3L6jMwPCaa5dw0YNsi_BI"
bot = telebot.TeleBot(BOT_TOKEN)

USERS_FILE = "users.txt"
LAST_NEWS_FILE = "last_news.txt"

app = Flask(__name__)
@app.route('/')
def home():
    return "Xaker Bot 24/7 ishlamoqda! 😎"

# --- YORDAMCHI FUNKSIYALAR (Valyuta va Ob-havo) ---

def get_currency():
    """Markaziy bankdan Dollar va Evro kursini olish"""
    try:
        url = "https://nbu.uz/uz/exchange-rates/json/"
        response = requests.get(url).json()
        usd = next(item for item in response if item["code"] == "USD")
        eur = next(item for item in response if item["code"] == "EUR")
        
        text = f"💰 **Rasmiy valyuta kursi:**\n\n"
        text += f"🇺🇸 1 USD = {usd['cb_price']} so'm\n"
        text += f"🇪🇺 1 EUR = {eur['cb_price']} so'm\n"
        text += f"\n🕒 Yangilangan vaqt: {usd['date']}"
        return text
    except:
        return "⚠️ Valyuta kursini olishda xatolik yuz berdi."

def get_weather():
    """Toshkent shahri uchun ob-havo (Open-Meteo)"""
    try:
        # Toshkent koordinatalari: 41.26, 69.21
        url = "https://api.open-meteo.com/v1/forecast?latitude=41.26&longitude=69.21&current_weather=true"
        response = requests.get(url).json()
        current = response['current_weather']
        temp = current['temperature']
        wind = current['windspeed']
        
        text = f"🌤 **Toshkentda ob-havo:**\n\n"
        text += f"🌡 Harorat: {temp}°C\n"
        text += f"💨 Shamol tezligi: {wind} km/soat\n"
        text += f"\n📍 Hozirgi holat"
        return text
    except:
        return "⚠️ Ob-havo ma'lumotlarini olishda xatolik yuz berdi."

# --- ASOSIY SKREPER (Oldingi kodlar) ---

def get_latest_news():
    url = "https://kun.uz/news/list"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.text.strip()
            if '/news/20' in href and len(text) > 15:
                full_link = "https://kun.uz" + href if not href.startswith('http') else href
                art_resp = requests.get(full_link, headers=headers)
                art_soup = BeautifulSoup(art_resp.text, 'html.parser')
                img_meta = art_soup.find('meta', property='og:image')
                img_url = img_meta['content'] if img_meta else None
                return {"title": text, "link": full_link, "image": img_url}
        return None
    except:
        return None

# --- BOT KOMANDALARI VA TUGMALAR ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Foydalanuvchini saqlash (eskidek)
    if not os.path.exists(USERS_FILE): open(USERS_FILE, 'w').close()
    with open(USERS_FILE, "r+") as f:
        users = f.read().splitlines()
        if str(message.chat.id) not in users:
            f.write(f"{message.chat.id}\n")

    # Tugmalarni yaratish
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💹 Valyuta kursi")
    btn2 = types.KeyboardButton("🌤 Ob-havo (Toshkent)")
    btn3 = types.KeyboardButton("📰 So'nggi yangilik")
    markup.add(btn1, btn2)
    markup.add(btn3)

    bot.send_message(
        message.chat.id, 
        f"Salom {message.from_user.first_name}! Xaker Botga xush kelibsiz.\nPastdagi tugmalardan foydalanishingiz mumkin:", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if message.text == "💹 Valyuta kursi":
        bot.send_message(message.chat.id, get_currency(), parse_mode="Markdown")
    
    elif message.text == "🌤 Ob-havo (Toshkent)":
        bot.send_message(message.chat.id, get_weather(), parse_mode="Markdown")
        
    elif message.text == "📰 So'nggi yangilik":
        news = get_latest_news()
        if news:
            caption = f"<b>{news['title']}</b>\n\n👉 {news['link']}"
            if news['image']:
                bot.send_photo(message.chat.id, news['image'], caption=caption, parse_mode="HTML")
            else:
                bot.send_message(message.chat.id, caption, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "Hozircha yangilik topilmadi.")

# --- SERVER VA TAYMER (Oldingidek) ---
def run_server():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

def timer_thread():
    # Bu qism avvalgidek har 15 daqiqada yangilik yuborib turadi (check_and_broadcast funksiyasi kerak)
    # Joy tejash uchun uni bu yerda qoldirdim, siz o'zingizni kodingizdagi o'sha qismni saqlab qoling
    pass

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    print("Bot yangilandi va ishga tushdi! 🎧")
    bot.infinity_polling()