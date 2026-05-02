import telebot
import requests
from bs4 import BeautifulSoup
import time
import threading
import schedule
import os
from flask import Flask
from telebot import types

# --- SOZLAMALAR ---
BOT_TOKEN = "8748456961:AAGKng_Y0vwE5o3L6jMwPCaa5dw0YNsi_BI"
bot = telebot.TeleBot(BOT_TOKEN)

USERS_FILE = "users.txt"
LAST_NEWS_FILE = "last_news.txt"

app = Flask(__name__)

@app.route('/')
def home():
    return "Xaker Bot 24/7 ishlamoqda! 😎"

# --- YORDAMCHI FUNKSIYALAR ---

def get_currency():
    try:
        url = "https://nbu.uz/uz/exchange-rates/json/"
        response = requests.get(url).json()
        usd = next(item for item in response if item["code"] == "USD")
        eur = next(item for item in response if item["code"] == "EUR")
        return f"💰 **Rasmiy kurs:**\n🇺🇸 1 USD = {usd['cb_price']} so'm\n🇪🇺 1 EUR = {eur['cb_price']} so'm"
    except:
        return "⚠️ Kursni olishda xatolik."

def get_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=41.26&longitude=69.21&current_weather=true"
        res = requests.get(url).json()
        temp = res['current_weather']['temperature']
        return f"🌤 **Toshkent:** {temp}°C"
    except:
        return "⚠️ Ob-havoda xatolik."

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
                return {"title": text, "link": full_link}
        return None
    except: return None

# --- BOT KOMANDALARI ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Foydalanuvchini saqlash
    if not os.path.exists(USERS_FILE): open(USERS_FILE, 'w').close()
    with open(USERS_FILE, "a+") as f:
        f.seek(0)
        users = f.read().splitlines()
        if str(message.chat.id) not in users:
            f.write(f"{message.chat.id}\n")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💹 Valyuta kursi", "🌤 Ob-havo (Toshkent)")
    markup.add("📰 So'nggi yangilik")

    bot.send_message(message.chat.id, "Xush kelibsiz! Tugmalardan birini tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if message.text == "💹 Valyuta kursi":
        bot.send_message(message.chat.id, get_currency(), parse_mode="Markdown")
    elif message.text == "🌤 Ob-havo (Toshkent)":
        bot.send_message(message.chat.id, get_weather(), parse_mode="Markdown")
    elif message.text == "📰 So'nggi yangilik":
        news = get_latest_news()
        if news:
            bot.send_message(message.chat.id, f"<b>{news['title']}</b>\n\n{news['link']}", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "Yangilik topilmadi.")

# --- RENDERDA BOTNI ISHLATISH SIRI ---

def start_bot():
    print("Bot polling boshlandi...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

# Botni alohida oqimda (thread) ishga tushiramiz
# Bu qism 'gunicorn' kodni o'qishi bilan darhol ishga tushadi
threading.Thread(target=start_bot, daemon=True).start()

if __name__ == "__main__":
    # Bu faqat lokalda ishlatish uchun
    app.run(host="0.0.0.0", port=5000)
