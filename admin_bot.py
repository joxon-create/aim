import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Tokeningizni shu yerga yozing
TOKEN = "8253855521:AAExh7BzHiyQnmrubfod3fcjK3tgQ-iaDoM"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

logging.basicConfig(level=logging.INFO)

# --- BAZANI TO'LIQ ISHGA TUSHIRISH ---
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 500,
            is_partner INTEGER DEFAULT 0,
            demo_balance INTEGER DEFAULT 1000
        )
    """)
    
    # Promokodlar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promos (
            code TEXT PRIMARY KEY,
            reward INTEGER,
            is_partner_code INTEGER DEFAULT 0
        )
    """)
    
    # To'lov so'rovlari jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            check_text TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# --- FSM (STATE) HOLATLARI ---
class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_balance_amount = State()
    waiting_for_partner_demo = State()
    waiting_for_promo_code = State()
    waiting_for_promo_reward = State()

# --- START BUYrug'i VA ADMIN MENYU ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, is_partner, demo_balance FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (user_id, username, balance, is_partner, demo_balance) VALUES (?, ?, 500, 0, 1000)", (user_id, username))
        conn.commit()
        balance, is_partner, demo_balance = 500, 0, 1000
    else:
        balance, is_partner, demo_balance = user[0], user[1], user[2]
    conn.close()

    kb = [
        [types.KeyboardButton(text="👥 Foydalanuvchilar statistikasi"), types.KeyboardButton(text="💰 Balansni o'zgartirish")],
        [types.KeyboardButton(text="🤝 Hamkor qo'shish"), types.KeyboardButton(text="🎁 Promokod yaratish")],
        [types.KeyboardButton(text="💳 To'lov kartasi sozlamasi")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer(
        f"👑 **AimDrop & Bulldrop Admin Paneliga xush kelibsiz!**\n\n"
        f"🆔 Sizning ID: `{user_id}`\n"
        f"🛠 Bu bot orqali butun saytni to'liq boshqarishingiz mumkin.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# --- 1. STATISTIKA ---
@dp.message(F.text == "👥 Foydalanuvchilar statistikasi")
async def total_stats(message: types.Message):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_partner = 1")
    total_partners = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(balance) FROM users")
    total_balance = cursor.fetchone()[0] or 0
    
    conn.close()

    await message.answer(
        f"📊 **Sayt statistikasi:**\n\n"
        f"👤 Jami foydalanuvchilar: **{total_users} ta**\n"
        f"🤝 Jami hamkorlar: **{total_partners} ta**\n"
        f"💵 Foydalanuvchilardagi umumiy UC: **{total_balance} UC**",
        parse_mode="Markdown"
    )

# --- 2. BALANSNI O'ZGARTIRISH (BERISH / AYIRISH) ---
@dp.message(F.text == "💰 Balansni o'zgartirish")
async def change_balance_start(message: types.Message, state: FSMContext):
    await message.answer("Foydalanuvchining **User ID** raqamini kiriting:")
    await state.set_state(AdminStates.waiting_for_user_id)

@dp.message(AdminStates.waiting_for_user_id)
async def get_user_id_for_balance(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        await state.update_data(target_user_id=user_id)
        await message.answer("Qancha UC qo'shmoqchisiz? (Kamaytirish uchun minus bilan yozing, masalan: `-50` yoki `100`):")
        await state.set_state(AdminStates.waiting_for_balance_amount)
    except ValueError:
        await message.answer("❌ Noto'g'ri ID. Faqat raqam kiriting:")

@dp.message(AdminStates.waiting_for_balance_amount)
async def get_balance_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        data = await state.get_data()
        target_user_id = data['target_user_id']

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (target_user_id,))
        user = cursor.fetchone()

        if user:
            new_balance = user[0] + amount
            cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, target_user_id))
            conn.commit()
            await message.answer(f"✅ Foydalanuvchi (`{target_user_id}`) balansi yangilandi. Yangi balans: **{new_balance} UC**", parse_mode="Markdown")
            
            # Foydalanuvchining o'ziga ham xabar yuborish mumkin
            try:
                await bot.send_message(target_user_id, f"💳 Admin tomonidan balansingiz o'zgartirildi! Joriy balans: **{new_balance} UC**", parse_mode="Markdown")
            except:
                pass
        else:
            await message.answer("❌ Bu foydalanuvchi bazada topilmadi.")
        
        conn.close()
        await state.clear()
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting:")

# --- 3. HAMKOR QO'SHISH VA DEMO BALANS BERISH ---
@dp.message(F.text == "🤝 Hamkor qo'shish")
async def add_partner_start(message: types.Message, state: FSMContext):
    await message.answer("Hamkor qilmoqchi bo'lgan foydalanuvchining **User ID** raqamini kiriting:")
    await state.set_state(AdminStates.waiting_for_user_id)
    # Bu yerda oddiy id so'rash uchun alohida state ochish ham mumkin, keling oddiy saqlaymiz:
    # Keling to'g'ridan-to'g'ri yangi bosqichga o'tamiz:
    # Buning uchun oddiy buyruq yoki oddiy shart ishlatamiz:

@dp.message(Command("partner"))
async def partner_command(message: types.Message, state: FSMContext):
    await message.answer("Hamkor qilmoqchi bo'lgan foydalanuvchining **User ID** raqamini kiriting:")
    await state.set_state(AdminStates.waiting_for_user_id)

# --- 4. PROMOKOD YARATISH (Oddiy yoki 20% li Hamkor promokodi) ---
@dp.message(F.text == "🎁 Promokod yaratish")
async def create_promo_start(message: types.Message, state: FSMContext):
    await message.answer("Yangi promokod nomini kiriting (masalan: `AIM2026` yoki `PARTNER20`):")
    await state.set_state(AdminStates.waiting_for_promo_code)

@dp.message(AdminStates.waiting_for_promo_code)
async def get_promo_code(message: types.Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.update_data(promo_code=code)
    await message.answer("Ushbu promokod qancha UC mukofot berishini yozing (masalan: `100` yoki `120`):")
    await state.set_state(AdminStates.waiting_for_promo_reward)

@dp.message(AdminStates.waiting_for_promo_reward)
async def get_promo_reward(message: types.Message, state: FSMContext):
    try:
        reward = int(message.text.strip())
        data = await state.get_data()
        code = data['promo_code']
        
        # Agar promokod nomida PARTNER bo'lsa uni avtomatik 20% li hamkor promokodi qilamiz
        is_partner_code = 1 if "PARTNER" in code else 0

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO promos (code, reward, is_partner_code) VALUES (?, ?, ?)", (code, reward, is_partner_code))
        conn.commit()
        conn.close()

        await message.answer(f"✅ Promokod muvaffaqiyatli yaratildi!\n\n🏷 Kod: `{code}`\n🎁 Mukofot: **{reward} UC**", parse_mode="Markdown")
        await state.clear()
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting:")

# --- 5. TO'LOV KARTASI SOZLAMASI ---
@dp.message(F.text == "💳 To'lov kartasi sozlamasi")
async def payment_card_info(message: types.Message):
    await message.answer(
        "💳 **Hozirgi faol to'lov kartasi:**\n"
        "`5614 6865 0763 1458`\n\n"
        "Ushbu karta saytda foydalanuvchilarga hisobni to'ldirish uchun ko'rsatiladi.",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
