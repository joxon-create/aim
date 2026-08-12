import telebot
from telebot import types
import sqlite3

TOKEN = "TOKENINGizni_SHU_YERGA_YOZING"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 123456789 # O'z Telegram ID ingizni yozing

def db_conn():
    return sqlite3.connect('pubg_ecosystem.db', check_same_thread=False)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (str(user_id),))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute("INSERT INTO users (telegram_id, username, balance) VALUES (?, ?, ?)", (str(user_id), username, 0.0))
        conn.commit()
    conn.close()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🎮 O'yinga o'tish"), types.KeyboardButton("💼 Inventar va Balans"))
    markup.add(types.KeyboardButton("🎁 Promo-kod ishlatish"), types.KeyboardButton("🤝 Hamkorlik (Partner)"))
    
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("👑 Admin Panel"))
        
    bot.send_message(message.chat.id, "Xush kelibsiz! PUBG Case va Ecosystem botiga marhamat.", reply_markup=markup)

@bot.message_handler(text=["👑 Admin Panel"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Promo-kod qo'shish", callback_data="add_promo"))
    markup.add(types.InlineKeyboardButton("📊 Statistika", callback_data="stats"))
    bot.send_message(message.chat.id, "Admin paneliga xush kelibsiz:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_promo")
def callback_add_promo(call):
    msg = bot.send_message(call.message.chat.id, "Yangi promo-kod va bonusni quyidagi formatda yuboring:\n`KOD BONUS IS_FREE_CASE(0 yoki 1)`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_promo_step)

def save_promo_step(message):
    try:
        parts = message.text.split()
        code = parts[0]
        bonus = float(parts[1])
        is_free = int(parts[2])
        
        conn = db_conn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO promo_codes (code, bonus, is_free_case) VALUES (?, ?, ?)", (code, bonus, is_free))
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, "✅ Promo-kod muvaffaqiyatli qo'shildi!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xatolik yuz berdi: {e}")

if __name__ == '__main__':
    bot.polling(none_stop=True)
