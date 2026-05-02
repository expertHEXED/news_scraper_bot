import telebot
import requests
from bs4 import BeautifulSoup
import time
import threading
import schedule
import os
from flask import Flask # YAngi kutubxona

# --- SIZNING SOZLAMALARINGIZ ---
BOT_TOKEN = "8748456961:AAGKng_Y0vwE5o3L6jMwPCaa5dw0YNsi_BI"
bot = telebot.TeleBot(BOT_TOKEN)

USERS_FILE = "users.txt"
LAST_NEWS_FILE = "last_news.txt"

# --- RENDER UCHUN ALDAMCHI SERVER (YANGI QISM) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Xaker Bot 24/7 ishlamoqda! 😎"

def run_server():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# --- XOTIRA FUNKSIYALARI ---
def add_user(chat_id):
    users = get_all_users()
    if str(chat_id) not in users:
        with open(USERS_FILE, "a") as file:
            file.write(f"{chat_id}\n")

def get_all_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as file:
        return file.read().splitlines()

def get_last_sent_link():
    if not os.path.exists(LAST_NEWS_FILE):
        return ""
    with open(LAST_NEWS_FILE, "r") as file:
        return file.read().strip()

def save_last_link(link):
    with open(LAST_NEWS_FILE, "w") as file:
        file.write(link)

# --- YANGILIK QIDIRISH ---
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
                image_url = img_meta['content'] if img_meta else None
                return {"title": text, "link": full_link, "image": image_url}
        return None
    except Exception as e:
        print(f"Xatolik: {e}")
        return None

# --- TARQATISH ---
def check_and_broadcast():
    news = get_latest_news()
    if not news:
        return
    last_link = get_last_sent_link()
    if news['link'] != last_link:
        print("Yangi xabar topildi! Tarqatyapman...")
        users = get_all_users()
        caption = f"<b>{news['title']}</b>\n\n👉 Batafsil: {news['link']}"
        for user_id in users:
            try:
                if news['image']:
                    bot.send_photo(user_id, news['image'], caption=caption, parse_mode="HTML")
                else:
                    bot.send_message(user_id, caption, parse_mode="HTML")
            except Exception as e:
                pass
        save_last_link(news['link'])

def timer_thread():
    schedule.every(15).minutes.do(check_and_broadcast)
    while True:
        schedule.run_pending()
        time.sleep(1)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user(message.chat.id)
    bot.reply_to(message, "Salom! Siz Kun.uz yangiliklar botiga obuna bo'ldingiz ✅")
    bot.send_message(message.chat.id, "<i>Eng so'nggi xabarni qidiryapman... ⏳</i>", parse_mode="HTML")
    check_and_broadcast()

if __name__ == "__main__":
    # Avtomatik tarqatuvchini ishga tushiramiz
    threading.Thread(target=timer_thread, daemon=True).start()
    # Aldamchi serverni ishga tushiramiz
    threading.Thread(target=run_server, daemon=True).start()
    
    print("Bot ishga tushdi! 🎧")
    bot.infinity_polling()