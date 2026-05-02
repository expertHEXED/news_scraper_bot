import os
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask
import telebot
from telebot import types

# --- SOZLAMALAR ---
BOT_TOKEN = "8748456961:AAGKng_Y0vwE5o3L6jMwPCaa5dw0YNsi_BI"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running..."

# --- FUNKSIYALAR ---

def get_currency():
    try:
        url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
        res = requests.get(url, timeout=10).json()
        usd = next(x for x in res if x["code"] == "USD")
        eur = next(x for x in res if x["code"] == "EUR")
        return f"💰 **Kurs (MB):**\n🇺🇸 1 USD = {usd['Rate']} so'm\n🇪🇺 1 EUR = {eur['Rate']} so'm"
    except:
        return "⚠️ Kursni olishda xatolik."

def get_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=41.26&longitude=69.21&current_weather=true"
        res = requests.get(url, timeout=10).json()
        temp = res['current_weather']['temperature']
        return f"🌤 **Toshkent:** {temp}°C"
    except:
        return "⚠️ Ob-havoda xatolik."

def get_news():
    try:
        url = "https://kun.uz/news/list"
        res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a'):
            href = a.get('href', '')
            if '/news/20' in href and len(a.text.strip()) > 15:
                link = "https://kun.uz" + href if not href.startswith('http') else href
                return f"📰 **Yangilik:**\n{a.text.strip()}\n\n🔗 {link}"
        return "Yangilik topilmadi."
    except:
        return "⚠️ Saytga ulanishda xato."

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def start(message):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("💹 Valyuta kursi", "🌤 Ob-havo")
    m.add("📰 So'nggi yangilik")
    bot.send_message(message.chat.id, "Tanlang:", reply_markup=m)

@bot.message_handler(func=lambda msg: True)
def handle(msg):
    if msg.text == "💹 Valyuta kursi":
        bot.send_message(msg.chat.id, get_currency(), parse_mode="Markdown")
    elif msg.text == "🌤 Ob-havo":
        bot.send_message(msg.chat.id, get_weather(), parse_mode="Markdown")
    elif msg.text == "📰 So'nggi yangilik":
        bot.send_message(msg.chat.id, get_news(), parse_mode="Markdown", disable_web_page_preview=False)

# --- RUN ---

def run_bot():
    bot.infinity_polling(timeout=20, long_polling_timeout=10)

# Botni alohida oqimda yurgizish
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)