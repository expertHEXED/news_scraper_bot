import os
import threading
import random
from flask import Flask
import telebot
from telebot import types

# --- SOZLAMALAR ---
BOT_TOKEN = "8748456961:AAGKng_Y0vwE5o3L6jMwPCaa5dw0YNsi_BI"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot 24/7 faol! 🚀"

# --- FOYDALI MA'LUMOTLAR ---

HIKMATLAR = [
    "Muvaffaqiyat — bu yiqilishdan to'xtash emas, balki har safar yiqilganda qayta tura olishdir.",
    "Bugungi mehnat — ertangi rohatning poydevori.",
    "Bilim — boylikdan ustun, chunki bilim seni asraydi, boylikni esa sen asrashing kerak.",
    "Vaqt — bu biz ega bo'lgan eng qimmatbaho xazinadir, uni bexuda sarflamang.",
    "Kichik qadamlar katta natijalarga olib boradi."
]

NAMOZ_VAQTLARI = """
🕌 **Toshkent shahri uchun namoz vaqtlari (Taxminiy):**
🏙 Bomdod: 04:10
🌅 Quyosh: 05:45
☀️ Peshin: 12:40
🌇 Asr: 17:25
🌆 Shom: 19:35
🌃 Xufton: 21:10
"""

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def start(message):
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🎓 Kun hikmati", "🎲 Tasodifiy son")
    m.add("🕌 Namoz vaqtlari", "📰 Yangiliklar")
    bot.send_message(message.chat.id, f"Salom {message.from_user.first_name}! Kerakli bo'limni tanlang:", reply_markup=m)

@bot.message_handler(func=lambda msg: True)
def handle(msg):
    if msg.text == "🎓 Kun hikmati":
        hikmat = random.choice(HIKMATLAR)
        bot.send_message(msg.chat.id, f"💡 **Kun hikmati:**\n\n_{hikmat}_", parse_mode="Markdown")
    
    elif msg.text == "🎲 Tasodifiy son":
        son = random.randint(1, 100)
        bot.send_message(msg.chat.id, f"🎲 Sizga tushgan son: **{son}**", parse_mode="Markdown")
        
    elif msg.text == "🕌 Namoz vaqtlari":
        bot.send_message(msg.chat.id, NAMOZ_VAQTLARI, parse_mode="Markdown")
        
    elif msg.text == "📰 Yangiliklar":
        bot.send_message(msg.chat.id, "Yugurib borib so'nggi yangilikni axtaryapman... 🏃‍♂️")
        # Bu yerga boyagi get_news() funksiyasini qo'shib qo'yishingiz mumkin
        bot.send_message(msg.chat.id, "Tez orada Kun.uz yangiliklari bu yerda chiqadi!")

# --- RUN ---
def run_bot():
    bot.infinity_polling(timeout=20, long_polling_timeout=10)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)import os
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
        # Markaziy Bankning eng barqaror JSON linki
        url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        usd_text = ""
        eur_text = ""

        # Ma'lumotlarni aylanib chiqamiz va keraklisini "ushlab" olamiz
        for item in data:
            # Ba'zi API'larda 'Ccy', ba'zilarida 'code' bo'ladi. Ikkalasini ham tekshiramiz.
            currency_code = item.get('Ccy') or item.get('code')
            rate = item.get('Rate') or item.get('cb_price')

            if currency_code == "USD":
                usd_text = f"🇺🇸 1 USD = {rate} so'm"
            elif currency_code == "EUR":
                eur_text = f"🇪🇺 1 EUR = {rate} so'm"

        if usd_text and eur_text:
            return f"💰 **Rasmiy kurs (MB):**\n\n{usd_text}\n{eur_text}"
        else:
            return "⚠️ Valyuta topilmadi (API o'zgargan bo'lishi mumkin)."

    except Exception as e:
        return f"❌ Xato yuz berdi: {type(e).__name__}"

def get_weather():
    try:
        # Open-Meteo tekin API (Hech qanday Key kerak emas)
        url = "https://api.open-meteo.com/v1/forecast?latitude=41.26&longitude=69.21&current_weather=true"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            temp = data['current_weather']['temperature']
            return f"🌤 **Toshkentda ob-havo:**\n\nHozirgi harorat: {temp}°C"
        else:
            return "⚠️ Ob-havo xizmati vaqtincha ishlamayapti."
    except Exception as e:
        print(f"OB-HAVO XATOSI: {e}")
        return "⚠️ Ob-havo ma'lumotini yuklab bo'lmadi."

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
