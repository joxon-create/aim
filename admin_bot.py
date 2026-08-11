import logging
import sqlite3
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8882251329:AAFNqlxx7bYPVs2bMdfYB80Qol1PWzEUk-Y"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

logging.basicConfig(level=logging.INFO)

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            balance REAL DEFAULT 0.01,
            is_partner INTEGER DEFAULT 0,
            partner_code TEXT,
            partner_earned REAL DEFAULT 0.0,
            aimcoin REAL DEFAULT 100.0,
            total_donated REAL DEFAULT 0.0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promos (
            code TEXT PRIMARY KEY,
            reward REAL,
            is_partner INTEGER DEFAULT 0,
            max_uses INTEGER DEFAULT 10,
            used_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

class PromoState(StatesGroup):
    waiting_for_code = State()
    waiting_for_reward = State()
    waiting_for_limit = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text="🎁 Promokod yaratish"), types.KeyboardButton(text="🤝 Hamkorlar statistikasi")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("⚡ **Bulldrop Admin Paneliga xush kelibsiz!**", reply_markup=keyboard, parse_mode="Markdown")

# --- HAMKORLAR STATISTIKASI (Qancha pul kelgani ko'rinib turadi) ---
@dp.message(F.text == "🤝 Hamkorlar statistikasi")
async def partner_stats(message: types.Message):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, partner_code, partner_earned FROM users WHERE is_partner = 1")
    partners = cursor.fetchall()
    conn.close()

    if not partners:
        await message.answer("❌ Hozircha hamkorlar mavjud emas.")
        return

    text = "📊 **Hamkorlar 20% promokod statistikasi:**\n\n"
    for p in partners:
        text += f"👤 Username: @{p[0] or 'Nomaʼlum'}\n🏷 Kod: `{p[1]}`\n💰 Kelgan foyda: **{p[2]} 🪙**\n-------------------\n"
    
    await message.answer(text, parse_mode="Markdown")

# --- PROMOKOD YARATISH (LIMIT VA 20% HAMKOR BILAN) ---
@dp.message(F.text == "🎁 Promokod yaratish")
async def create_promo(message: types.Message, state: FSMContext):
    await message.answer("Yangi promokod nomini kiriting (Agar hamkor uchun bo'lsa, xohlagancha ishlatiladi):")
    await state.set_state(PromoState.waiting_for_code)

@dp.message(PromoState.waiting_for_code)
async def get_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text.strip().upper())
    await message.answer("Promokod qancha mukofot berishini yozing (masalan: `20`):")
    await state.set_state(PromoState.waiting_for_reward)

@dp.message(PromoState.waiting_for_reward)
async def get_reward(message: types.Message, state: FSMContext):
    try:
        reward = float(message.text.strip())
        await state.update_data(reward=reward)
        await message.answer("Bu oddiy keys promokodimi yoki 20% li hamkor promokodimi?\n1 - Oddiy (Limitli)\n2 - 20% Hamkor (Cheksiz)")
        await state.set_state(PromoState.waiting_for_limit)
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting:")

@dp.message(PromoState.waiting_for_limit)
async def get_limit(message: types.Message, state: FSMContext):
    choice = message.text.strip()
    data = await state.get_data()
    code = data['code']
    reward = data['reward']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if choice == "2":
        cursor.execute("INSERT OR REPLACE INTO promos (code, reward, is_partner, max_uses) VALUES (?, ?, 1, 999999)", (code, reward))
        cursor.execute("UPDATE users SET is_partner = 1, partner_code = ? WHERE user_id = ?", (code, message.from_user.id))
        conn.commit()
        conn.close()
        await message.answer(f"✅ **20% Hamkor promokodi yaratildi!**\n🏷 Kod: `{code}`", parse_mode="Markdown")
    else:
        cursor.execute("INSERT OR REPLACE INTO promos (code, reward, is_partner, max_uses) VALUES (?, ?, 0, 10)", (code, reward))
        conn.commit()
        conn.close()
        await message.answer(f"✅ **Oddiy keys promokodi yaratildi!** (Limit: 10 ta)\n🏷 Kod: `{code}`", parse_mode="Markdown")

    await state.clear()

# --- CARD XABARBOT SMS'LARINI AVTOMAT O'QISH VA BALANSNI TO'LDIRISH ---
@dp.message(F.text)
async def catch_card_sms(message: types.Message):
    text = message.text or ""
    
    # Xabarda UZS yoki so'm borligini va to'lov kelganini tekshiramiz
    if "UZS" in text or "so'm" in text:
        clean_text = text.replace(',', '').replace(' ', '')
        numbers = re.findall(r'\d+', clean_text)
        
        if numbers:
            sum_amount = float(numbers[0])
            uc_amount = (sum_amount / 14000) * 60
            aim_add = (uc_amount / 60) * 100
            
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            # user_id = 1 ni bazada yangilaymiz (yoki kerakli foydalanuvchi)
            cursor.execute("UPDATE users SET aimcoin = aimcoin + ?, total_donated = total_donated + ? WHERE user_id = 1", (aim_add, uc_amount))
            conn.commit()
            conn.close()
            
            await message.reply(f"✅ **To'lov muvaffaqiyatli topildi!**\n\nSumma: {sum_amount} so'm\nHisobga qo'shildi: {uc_amount:.1f} UC ({aim_add} AimCoin)")

if __name__ == "__main__":
    import asyncio
    print("Admin bot ishga tushdi...")
    asyncio.run(dp.start_polling(bot))
