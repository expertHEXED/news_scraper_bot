import telebot
import requests
from bs4 import BeautifulSoup
import time
import threading
import schedule
import os

# --- SIZNING SOZLAMALARINGIZ ---
BOT_TOKEN = "8748456961:AAGKng_Y0vwE5o3L6jMwPCaa5dw0YNsi_BI"
bot = telebot.TeleBot(BOT_TOKEN)

# Fayllar nomi
USERS_FILE = "users.txt"
LAST_NEWS_FILE = "last_news.txt"

# --- 1. XOTIRA FUNKSIYALARI ---
def add_user(chat_id):
    """Yangi foydalanuvchini bazaga (users.txt) qo'shish"""
    users = get_all_users()
    if str(chat_id) not in users:
        with open(USERS_FILE, "a") as file:
            file.write(f"{chat_id}\n")

def get_all_users():
    """Barcha foydalanuvchilar ID sini o'qib olish"""
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as file:
        return file.read().splitlines()

def get_last_sent_link():
    """Oxirgi yuborilgan yangilik ssilkasini o'qish"""
    if not os.path.exists(LAST_NEWS_FILE):
        return ""
    with open(LAST_NEWS_FILE, "r") as file:
        return file.read().strip()

def save_last_link(link):
    """Oxirgi yuborilgan yangilik ssilkasini saqlab qo'yish"""
    with open(LAST_NEWS_FILE, "w") as file:
        file.write(link)

# --- 2. YANGILIK QIDIRISH FUNKSIYASI ---
def get_latest_news():
    url = "https://kun.uz/news/list"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.text.strip()
            
            # Haqiqiy yangilikni ushlash
            if '/news/20' in href and len(text) > 15:
                full_link = "https://kun.uz" + href if not href.startswith('http') else href
                
                # Rasm qidirish
                art_resp = requests.get(full_link, headers=headers)
                art_soup = BeautifulSoup(art_resp.text, 'html.parser')
                img_meta = art_soup.find('meta', property='og:image')
                image_url = img_meta['content'] if img_meta else None
                
                return {"title": text, "link": full_link, "image": image_url}
        return None
    except Exception as e:
        print(f"Web Scraping xatoligi: {e}")
        return None

# --- 3. AVTOMATIK TARQATISH FUNKSIYASI ---
def check_and_broadcast():
    """Har safar ishga tushib, yangilik bormi tekshiradi va hammaga tarqatadi"""
    news = get_latest_news()
    if not news:
        return

    last_link = get_last_sent_link()
    
    # Agar bu yangilikni oldin yubormagan bo'lsak, demak u YANGI!
    if news['link'] != last_link:
        print(f"Yangi xabar topildi! Tarqatish boshlandi... ({news['title']})")
        users = get_all_users()
        caption = f"<b>{news['title']}</b>\n\n👉 Batafsil: {news['link']}"
        
        for user_id in users:
            try:
                if news['image']:
                    bot.send_photo(user_id, news['image'], caption=caption, parse_mode="HTML")
                else:
                    bot.send_message(user_id, caption, parse_mode="HTML")
            except Exception as e:
                print(f"{user_id} ga yuborishda xatolik (balki botni bloklagan): {e}")
                
        # Hammaga yuborib bo'lgach, bu yangilikni "eski" deb saqlab qo'yamiz
        save_last_link(news['link'])
    else:
        print("Hozircha yangi xabarlar yo'q...")

# --- 4. ORQA FONDA ISHLOVCHI TIMER (TAQSIMOT) ---
def timer_thread():
    # Har 15 daqiqada check_and_broadcast funksiyasini ishga tushiradi
    schedule.every(15).minutes.do(check_and_broadcast)
    while True:
        schedule.run_pending()
        time.sleep(1)

# --- 5. BOTNING ODAMLAR BILAN GAPLASHISH QISMI ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user(message.chat.id) # Odamni xotiraga yozamiz
    bot.reply_to(message, "Salom! Siz Kun.uz yangiliklar botiga obuna bo'ldingiz ✅\n\nSaytda yangi xabar chiqishi bilan men sizga avtomat ravishda yuborib turaman!")
    
    # Start bosgan odam xursand bo'lishi uchun o'sha zaxoti bitta eng so'nggi yangilikni yuboramiz
    bot.send_message(message.chat.id, "<i>Hozirgi eng so'nggi xabarni qidiryapman... ⏳</i>", parse_mode="HTML")
    check_and_broadcast()

if __name__ == "__main__":
    # Avtomatik tekshiruvchini orqa fonda alohida ishga tushiramiz
    threading.Thread(target=timer_thread, daemon=True).start()
    
    print("Bot muvaffaqiyatli ishga tushdi! Eshitish rejimida... 🎧")
    # Botni o'chib qolmasdan doimiy ishlab turishga majbur qilamiz
    bot.infinity_polling()