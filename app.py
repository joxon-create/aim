import random
import sqlite3
import asyncio
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

app = FastAPI()

# --- SOZLAMALAR ---
BOT_TOKEN = "8253855521:AAF4l7kWU_hKgMysrmHFJjsV2wDVZKtUgRs"
SUPER_ADMIN_ID = 8692517241

# Eski adminlar huquqlari saqlangan holda qo'shimcha adminlar ID lari
ADMINS = [SUPER_ADMIN_ID, 123456789] 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- BAZANI YARATISH ---
def get_db_connection():
    conn = sqlite3.connect("aimdrop.db", timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            aimcoin REAL DEFAULT 100.0,
            total_donated REAL DEFAULT 0.0,
            partner_earned REAL DEFAULT 0.0,
            uid TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promos (
            code TEXT PRIMARY KEY,
            reward REAL,
            max_uses INTEGER DEFAULT 10,
            used_count INTEGER DEFAULT 0,
            owner_id INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS demo_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            status TEXT DEFAULT 'pending'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            promo TEXT,
            receipt_info TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            val REAL,
            img TEXT
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO admins (admin_id) VALUES (?)", (SUPER_ADMIN_ID,))
    conn.commit()
    conn.close()

init_db()

def is_admin(user_id: int) -> bool:
    if user_id in ADMINS:
        return True
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE admin_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

# --- TELEGRAM BOT ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, aimcoin) VALUES (?, ?, 100.0)", (user_id, username))
    conn.commit()
    conn.close()

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Aim Balans So'rash"), KeyboardButton(text="📊 Mening Aim Statistikam")],
            [KeyboardButton(text="💳 Balansni to'ldirish")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"🔥 **BULLDROP v2.0** rasmiy botiga xush kelibsiz!\n"
        f"Sizning Telegram ID raqamingiz: `{user_id}`\n\n"
        f"Pastdagi tugmalar orqali Aim balans so'rashingiz va Web App orqali eksklyuziv keyslar ochishingiz mumkin.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.message(F.text == "🎬 Aim Balans So'rash")
async def ask_demo_start(message: types.Message):
    await message.answer("Iltimos, demo sifatida olmoqchi bo'lgan Aim miqdorini yuboring (masalan: `500`):", parse_mode="Markdown")

@dp.message(F.text == "💳 Balansni to'ldirish")
async def deposit_start_bot(message: types.Message):
    await message.answer(
        "💳 **Balansni to'ldirish uchun Web App'ga o'ting!**\n\n"
        "U yerda karta raqamiga o'tkazma qilib, 20% promokodlarni qo'llashingiz va chek ma'lumotlari bilan 'To'lov qildim' tugmasini bosishingiz mumkin.",
        parse_mode="Markdown"
    )

@dp.message(F.text.regexp(r'^\d+(\.\d+)?$'))
async def process_demo_amount(message: types.Message):
    user_id = message.from_user.id
    amount = float(message.text)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO demo_requests (user_id, amount) VALUES (?, ?)", (user_id, amount))
    req_id = cursor.lastrowid
    conn.commit()
    conn.close()

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_demo_{req_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_demo_{req_id}")
        ]
    ])
    try:
        for adm in ADMINS:
            await bot.send_message(
                adm,
                f"🎬 **Yangi Aim So'rovi!**\n\n"
                f"👤 Foydalanuvchi ID: `{user_id}`\n"
                f"💎 Miqdor: {amount} Aim\n"
                f"🆔 So'rov ID: #{req_id}",
                reply_markup=markup,
                parse_mode="Markdown"
            )
    except Exception:
        pass

    await message.answer(f"✅ Aim so'rovingiz ({amount} Aim) adminga yuborildi! Tez orada ko'rib chiqiladi.")

@dp.message(F.text == "📊 Mening Aim Statistikam")
async def my_stats(message: types.Message):
    user_id = message.from_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT aimcoin, partner_earned FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        aim = user["aimcoin"]
        uc = (aim / 100) * 60
        earned = user["partner_earned"]
        await message.answer(f"📊 **AimProfilingiz:**\n\n💎 AimCoin: {aim:.2f} Aim\n💰 UC Ekvivalenti: {uc:.1f} UC\n🤝 Hamkorlikdan topilgan: {earned} Aim")

@dp.callback_query(F.data.startswith("approve_demo_"))
async def approve_demo(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    req_id = int(callback.data.split("_")[2])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, amount, status FROM demo_requests WHERE id = ?", (req_id,))
    req = cursor.fetchone()
    if not req or req["status"] != "pending":
        conn.close()
        return
    user_id, amount = req["user_id"], req["amount"]
    cursor.execute("UPDATE users SET aimcoin = aimcoin + ? WHERE user_id = ?", (amount, user_id))
    cursor.execute("UPDATE demo_requests SET status = 'approved' WHERE id = ?", (req_id,))
    conn.commit()
    conn.close()
    await callback.message.edit_text(f"✅ Aim so'rov (#{req_id}) tasdiqlandi! +{amount} Aim qo'shildi.")
    await bot.send_message(user_id, f"🎉 Tabriklaymiz! Admin aim so'rovingizni tasdiqladi: +{amount} Aim qo'shildi.")

@dp.callback_query(F.data.startswith("reject_demo_"))
async def reject_demo(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    req_id = int(callback.data.split("_")[2])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE demo_requests SET status = 'rejected' WHERE id = ?", (req_id,))
    conn.commit()
    conn.close()
    await callback.message.edit_text(f"❌ Aim so'rov (#{req_id}) rad etildi.")

# --- WEB APP ORQALI TO'LOV CALLBACK'LARI ---
@dp.callback_query(F.data.startswith("accept_payment_"))
async def accept_payment(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda bu huquq yo'q!", show_alert=True)
        return
    payment_id = int(callback.data.split("_")[2])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, amount, promo, status FROM payments WHERE id = ?", (payment_id,))
    pay = cursor.fetchone()
    if not pay or pay["status"] != "pending":
        conn.close()
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan yoki topilmadi.", show_alert=True)
        return
    
    user_id, uc_amount, promo = pay["user_id"], pay["amount"], pay["promo"]
    final_uc = uc_amount
    
    if promo:
        cursor.execute("SELECT owner_id FROM promos WHERE code = ?", (promo.upper(),))
        p_data = cursor.fetchone()
        final_uc = uc_amount * 1.20
        if p_data and p_data["owner_id"] and p_data["owner_id"] != user_id:
            owner_id = p_data["owner_id"]
            partner_bonus = (uc_amount / 60) * 100 * 0.20
            cursor.execute("UPDATE users SET partner_earned = partner_earned + ? WHERE user_id = ?", (partner_bonus, owner_id))

    aim_add = (final_uc / 60) * 100
    cursor.execute("UPDATE users SET aimcoin = aimcoin + ?, total_donated = total_donated + ? WHERE user_id = ?", (aim_add, uc_amount, user_id))
    cursor.execute("UPDATE payments SET status = 'accepted' WHERE id = ?", (payment_id,))
    conn.commit()
    conn.close()

    await callback.message.edit_text(f"✅ To'lov (#{payment_id}) tasdiqlandi va foydalanuvchi balansiga Aim qo'shildi.")
    try:
        await bot.send_message(user_id, f"✅ **To'lovingiz admin tomonidan tasdiqlandi!** Balansingizga muvaffaqiyatli Aim qo'shildi.")
    except Exception:
        pass

@dp.callback_query(F.data.startswith("reject_payment_"))
async def reject_payment(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda bu huquq yo'q!", show_alert=True)
        return
    payment_id = int(callback.data.split("_")[2])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE payments SET status = 'rejected' WHERE id = ?", (payment_id,))
    conn.commit()
    
    cursor.execute("SELECT user_id FROM payments WHERE id = ?", (payment_id,))
    p_data = cursor.fetchone()
    conn.close()
    if p_data:
        try:
            await bot.send_message(p_data["user_id"], f"❌ **To'lovingiz rad etildi.** Ma'lumotlarni tekshirib qaytadan urinib ko'ring.")
        except Exception:
            pass
            
    await callback.message.edit_text(f"❌ To'lov (#{payment_id}) rad etildi.")

# --- FASTAPI STARTUP ---
@app.on_event("startup")
async def startup_event():
    async def run_telegram_bot():
        try:
            await dp.start_polling(bot, skip_updates=True)
        except Exception as e:
            print(f"Bot polling xatosi: {e}")
            
    asyncio.create_task(run_telegram_bot())

# --- BULLDROP CASES & ITEMS ---
BULLDROP_ITEMS_POOL = [
    {"name": "Bulldrop M416 'Glacier'", "val": 2800, "img": "https://cdn-icons-png.flaticon.com/512/3076/3076137.png", "chance": 0.05},
    {"name": "Bulldrop AWM 'The Fool'", "val": 2500, "img": "https://cdn-icons-png.flaticon.com/512/1069/1069158.png", "chance": 0.1},
    {"name": "Bulldrop Pan 'BFC'", "val": 450, "img": "https://cdn-icons-png.flaticon.com/512/1046/1046857.png", "chance": 2.0},
    {"name": "Bull Helmet Lv.3", "val": 350, "img": "https://cdn-icons-png.flaticon.com/512/807/807281.png", "chance": 5.0},
    {"name": "Bull Silver Fragment", "val": 15, "img": "https://cdn-icons-png.flaticon.com/512/217/217853.png", "chance": 92.85},
]

CASES = {}
for i in range(1, 21):
    price_uc = 10 if i == 1 else round(10 + (290 / 19) * (i - 1), 1)
    price_aim = (price_uc / 60) * 100
    items = [dict(item, val=round(price_aim * random.uniform(0.3, 2.5), 1)) for item in BULLDROP_ITEMS_POOL]
    CASES[f"case_{i}"] = {
        "name": f"Bulldrop Case #{i}",
        "price_uc": price_uc,
        "price_aim": round(price_aim, 2),
        "img": "https://cdn-icons-png.flaticon.com/512/3313/3313498.png",
        "items": items
    }

# --- FASTAPI WEB APP (ULTRA CREATIVE & MODERN UI) ---
@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=""""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BULLDROP - Cyber Gaming Ecosystem</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg-main: #06070b;
                --bg-card: rgba(19, 23, 34, 0.75);
                --bg-card-hover: rgba(26, 31, 46, 0.9);
                --accent-purple: #8b5cf6;
                --accent-pink: #ec4899;
                --accent-gradient: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
                --accent-gold: #fbbf24;
                --text-main: #ffffff;
                --text-muted: #94a3b8;
                --border-color: rgba(255, 255, 255, 0.08);
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; -webkit-tap-highlight-color: transparent; }
            body { background: var(--bg-main); color: var(--text-main); min-height: 100vh; display: flex; flex-direction: column; overflow-x: hidden; background-image: radial-gradient(circle at 50% -20%, #3b0764 0%, transparent 60%); }
            
            header { display: flex; justify-content: space-between; align-items: center; background: rgba(6, 7, 11, 0.85); backdrop-filter: blur(25px); padding: 14px 20px; border-bottom: 1px solid var(--border-color); position: sticky; top: 0; z-index: 1000; }
            .logo { font-size: 22px; font-weight: 800; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 0.8px; text-shadow: 0 0 30px rgba(139,92,246,0.4); }
            .balance-container { background: rgba(139, 92, 246, 0.12); border: 1px solid rgba(139, 92, 246, 0.35); padding: 8px 16px; border-radius: 40px; font-weight: 700; color: #c4b5fd; font-size: 13px; box-shadow: 0 0 25px rgba(139, 92, 246, 0.2); display: flex; align-items: center; gap: 6px; }

            .container { max-width: 1200px; margin: 0 auto; width: 100%; padding: 20px; flex: 1; padding-bottom: 110px; }
            .tab-content { display: none; animation: fadeIn 0.35s cubic-bezier(0.16, 1, 0.3, 1); }
            .tab-content.active { display: block; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

            .section-title { font-size: 20px; font-weight: 800; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; color: #f8fafc; }
            .cases-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(155px, 1fr)); gap: 16px; }
            .case-card { background: var(--bg-card); backdrop-filter: blur(15px); border: 1px solid var(--border-color); border-radius: 22px; padding: 18px 12px; text-align: center; cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 10px 30px rgba(0,0,0,0.5); position: relative; overflow: hidden; }
            .case-card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px; background: var(--accent-gradient); opacity: 0; transition: 0.3s; }
            .case-card:hover { transform: translateY(-6px); background: var(--bg-card-hover); border-color: rgba(139, 92, 246, 0.5); box-shadow: 0 20px 40px rgba(139, 92, 246, 0.2); }
            .case-card:hover::before { opacity: 1; }
            .case-img { width: 75px; height: 75px; object-fit: contain; margin: 10px auto; filter: drop-shadow(0 12px 15px rgba(0,0,0,0.7)); transition: 0.3s; }
            .case-card:hover .case-img { transform: scale(1.1); }
            .btn-open { background: var(--accent-gradient); color: #fff; border: none; padding: 10px; width: 100%; border-radius: 12px; font-weight: 700; margin-top: 12px; cursor: pointer; box-shadow: 0 4px 15px rgba(139, 92, 246, 0.35); font-size: 12px; transition: 0.2s; }
            .btn-open:active { transform: scale(0.96); }

            .case-view { background: var(--bg-card); backdrop-filter: blur(25px); border: 1px solid var(--border-color); border-radius: 26px; padding: 25px; text-align: center; max-width: 600px; margin: 0 auto; box-shadow: 0 30px 60px rgba(0,0,0,0.8); }
            .multi-select { display: flex; justify-content: center; gap: 8px; margin: 15px 0; flex-wrap: wrap; }
            .count-btn { background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); color: var(--text-muted); padding: 8px 14px; border-radius: 10px; font-weight: 700; cursor: pointer; font-size: 12px; transition: 0.2s; }
            .count-btn.active { background: var(--accent-purple); color: #fff; border-color: var(--accent-purple); box-shadow: 0 0 15px rgba(139, 92, 246, 0.5); }

            .roulettes-container { display: flex; flex-direction: column; gap: 10px; max-height: 380px; overflow-y: auto; margin: 15px 0; padding-right: 4px; }
            .roulette-track-window { width: 100%; overflow: hidden; position: relative; height: 110px; background: #030406; border-radius: 14px; border: 1px solid var(--border-color); flex-shrink: 0; }
            .roulette-pointer { position: absolute; top: 0; bottom: 0; left: 50%; width: 3px; background: var(--accent-pink); transform: translateX(-50%); z-index: 10; box-shadow: 0 0 15px var(--accent-pink); }
            .roulette-track { display: flex; position: absolute; left: 0; top: 6px; transition: transform 4s cubic-bezier(0.08, 0.82, 0.17, 1); }
            .roulette-item { min-width: 98px; height: 96px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0 5px; font-size: 11px; padding: 4px; }
            .roulette-item img { width: 45px; height: 45px; object-fit: contain; margin-bottom: 4px; }

            .win-actions-container { display: flex; gap: 10px; margin-top: 15px; justify-content: center; }
            .btn-win-sell { background: #ef4444; color: #fff; border: none; padding: 10px 16px; border-radius: 10px; font-weight: 700; font-size: 12px; cursor: pointer; flex: 1; box-shadow: 0 4px 15px rgba(239, 68, 68, 0.35); }
            .btn-win-keep { background: #10b981; color: #fff; border: none; padding: 10px 16px; border-radius: 10px; font-weight: 700; font-size: 12px; cursor: pointer; flex: 1; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.35); }

            .inventory-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(135px, 1fr)); gap: 12px; margin-top: 15px; max-height: 450px; overflow-y: auto; padding-right: 4px; }
            .inv-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 16px; padding: 12px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: space-between; }
            .inv-card img { width: 55px; height: 55px; object-fit: contain; margin-bottom: 6px; }
            .inv-actions { display: flex; gap: 6px; width: 100%; margin-top: 10px; }
            .btn-inv-sell { background: #ef4444; color: #fff; border: none; padding: 6px; border-radius: 8px; font-size: 10px; font-weight: bold; cursor: pointer; flex: 1; }
            .btn-inv-keep { background: rgba(255,255,255,0.05); color: var(--text-muted); border: 1px solid var(--border-color); padding: 6px; border-radius: 8px; font-size: 10px; font-weight: bold; cursor: pointer; flex: 1; }

            .game-panel { background: var(--bg-card); backdrop-filter: blur(25px); border: 1px solid var(--border-color); border-radius: 26px; padding: 22px; max-width: 500px; margin: 0 auto; text-align: center; box-shadow: 0 30px 60px rgba(0,0,0,0.7); }
            .games-menu { display: flex; justify-content: center; gap: 8px; margin-bottom: 20px; }
            .game-tab-btn { background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); color: var(--text-muted); padding: 8px 14px; border-radius: 10px; font-weight: 700; cursor: pointer; font-size: 12px; flex: 1; }
            .game-tab-btn.active { background: var(--accent-purple); color: #fff; border-color: var(--accent-purple); }

            .mines-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 15px 0; }
            .mine-cell { aspect-ratio: 1; background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 10px; font-size: 18px; cursor: pointer; transition: 0.2s; display: flex; align-items: center; justify-content: center; }
            .mine-cell:hover { background: rgba(255,255,255,0.07); }

            .tower-grid { display: flex; flex-direction: column-reverse; gap: 6px; margin: 15px 0; }
            .tower-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
            .tower-cell { background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); height: 42px; border-radius: 10px; cursor: pointer; font-weight: bold; color: #fff; }

            .crash-screen { height: 180px; background: #030406; border-radius: 14px; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 1px solid var(--border-color); margin: 15px 0; position: relative; overflow: hidden; }
            .crash-multiplier { font-size: 38px; font-weight: 900; color: #10b981; text-shadow: 0 0 25px rgba(16, 185, 129, 0.4); }

            .panel { background: var(--bg-card); backdrop-filter: blur(25px); border: 1px solid var(--border-color); padding: 24px; border-radius: 26px; max-width: 440px; margin: 0 auto; box-shadow: 0 30px 60px rgba(0,0,0,0.7); }
            .form-group { margin-bottom: 16px; text-align: left; }
            .form-group label { display: block; margin-bottom: 6px; color: var(--text-muted); font-size: 12px; font-weight: 700; }
            .form-group input { width: 100%; padding: 14px; background: #030406; border: 1px solid var(--border-color); color: #fff; border-radius: 12px; font-size: 14px; text-align: center; outline: none; transition: 0.2s; }
            .form-group input:focus { border-color: var(--accent-purple); box-shadow: 0 0 12px rgba(139, 92, 246, 0.25); }
            
            .card-box { background: linear-gradient(135deg, #1e1b4b 0%, #311042 100%); border: 1px solid rgba(139,92,246,0.3); border-radius: 16px; padding: 16px; margin-bottom: 16px; text-align: center; position: relative; box-shadow: 0 10px 25px rgba(0,0,0,0.4); }
            .card-number { font-size: 16px; font-weight: 800; letter-spacing: 1.5px; color: #e2e8f0; margin: 6px 0; }
            .btn-copy { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; padding: 6px 12px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer; transition: 0.2s; }
            .btn-copy:active { background: var(--accent-purple); }

            .btn-submit { background: var(--accent-gradient); color: #fff; border: none; padding: 14px; width: 100%; border-radius: 12px; font-weight: 800; cursor: pointer; box-shadow: 0 6px 20px rgba(139, 92, 246, 0.35); font-size: 14px; transition: 0.2s; }
            .btn-submit:active { transform: scale(0.98); }

            .bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(6, 7, 11, 0.85); backdrop-filter: blur(25px); border-top: 1px solid var(--border-color); display: flex; justify-content: space-around; padding: 10px 0; z-index: 1000; }
            .nav-item { background: transparent; border: none; color: var(--text-muted); cursor: pointer; font-size: 11px; display: flex; flex-direction: column; align-items: center; gap: 4px; font-weight: 700; transition: 0.2s; }
            .nav-item.active { color: #c4b5fd; text-shadow: 0 0 15px rgba(139, 92, 246, 0.5); }
            .nav-item span.icon { font-size: 20px; }
        </style>
    </head>
    <body>
        <header>
            <div class="logo">BULLDROP</div>
            <div class="balance-container">💎 <span id="balance">100.00</span> Aim (<span id="uc-balance">60</span> UC)</div>
        </header>

        <div class="container">
            <!-- Cases Tab -->
            <div id="cases-tab" class="tab-content active">
                <div class="section-title">📦 Bulldog Premium Keyslari</div>
                <div class="cases-grid" id="cases-grid"></div>
            </div>

            <!-- Case Detail View -->
            <div id="case-detail-tab" class="tab-content">
                <div class="case-view">
                    <img id="detail-img" src="" style="width: 85px; height: 85px; object-fit: contain; margin-bottom: 8px;">
                    <h2 id="detail-name" style="margin-bottom: 4px; font-size: 19px; font-weight: 800;">Bulldrop Case</h2>
                    <p style="color: #c4b5fd; font-weight: 700; font-size: 15px;" id="detail-price-text">10 UC (16.67 Aim)</p>
                    
                    <p style="font-size: 12px; color: var(--text-muted); margin-top: 14px;">Ochish sonini tanlang:</p>
                    <div class="multi-select">
                        <button class="count-btn active" onclick="setCount(1, this)">1 ta</button>
                        <button class="count-btn" onclick="setCount(2, this)">2 ta</button>
                        <button class="count-btn" onclick="setCount(3, this)">3 ta</button>
                        <button class="count-btn" onclick="setCount(4, this)">4 ta</button>
                        <button class="count-btn" onclick="setCount(5, this)">5 ta</button>
                        <button class="count-btn" onclick="setCount(10, this)">10 ta</button>
                    </div>

                    <p style="font-size: 13px; margin-bottom: 12px;">Umumiy qiymat: <span id="total-open-price" style="color: #c4b5fd; font-weight: bold;">10</span> UC (<span id="total-open-aim" style="color: #10b981; font-weight: bold;">16.67</span> Aim)</p>
                    
                    <div id="roulette-section" style="display: none;">
                        <div class="roulettes-container" id="roulettes-container-box"></div>
                    </div>

                    <div id="win-result-container" style="display: none; margin-top: 12px;">
                        <div id="win-result-text" style="font-size: 13px; font-weight: bold; color: #10b981; margin-bottom: 8px;"></div>
                        <div class="win-actions-container" id="win-actions-box"></div>
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-top: 15px;">
                        <button class="btn-submit" onclick="openSelectedCase()" id="action-btn">Hozir Ochish</button>
                        <button class="count-btn" onclick="switchTab('cases', document.querySelectorAll('.bottom-nav button')[0])" style="flex:1; display:flex; align-items:center; justify-content:center;">Orqaga</button>
                    </div>
                </div>
            </div>

            <!-- Inventory Tab -->
            <div id="inventory-tab" class="tab-content">
                <div class="section-title">🎒 Mening Inventarim</div>
                <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">Yutuqlaringizni shu yerdan sotishingiz yoki saqlashingiz mumkin.</p>
                <div class="inventory-grid" id="inventory-grid"></div>
            </div>

            <!-- Mini Games Tab -->
            <div id="games-tab" class="tab-content">
                <div class="game-panel">
                    <div class="games-menu">
                        <button class="game-tab-btn active" onclick="switchGame('mines', this)">Mines</button>
                        <button class="game-tab-btn" onclick="switchGame('tower', this)">Tower</button>
                        <button class="game-tab-btn" onclick="switchGame('crash', this)">Crash</button>
                    </div>

                    <div id="game-mines" class="sub-game">
                        <h3 style="margin-bottom: 12px; font-size: 16px;">Bulldrop Mines</h3>
                        <div class="form-group"><label>Tikish (Aim):</label><input type="number" id="mines-bet" value="10"></div>
                        <div class="mines-grid" id="mines-board"></div>
                        <button class="btn-submit" onclick="startMines()">O'yinni Boshlash</button>
                    </div>

                    <div id="game-tower" class="sub-game" style="display: none;">
                        <h3 style="margin-bottom: 12px; font-size: 16px;">Bulldrop Tower</h3>
                        <div class="form-group"><label>Tikish (Aim):</label><input type="number" id="tower-bet" value="10"></div>
                        <div class="tower-grid" id="tower-board"></div>
                        <button class="btn-submit" onclick="startTower()">Qurishni Boshlash</button>
                    </div>

                    <div id="game-crash" class="sub-game" style="display: none;">
                        <h3 style="margin-bottom: 12px; font-size: 16px;">Bulldrop Crash</h3>
                        <div class="form-group"><label>Tikish (Aim):</label><input type="number" id="crash-bet" value="10"></div>
                        <div class="crash-screen">
                            <div class="crash-multiplier" id="crash-mult">1.00x</div>
                        </div>
                        <button class="btn-submit" onclick="startCrash()" id="crash-btn">Uchishni Boshlash</button>
                    </div>
                </div>
            </div>

            <!-- Wallet Tab (Qulaylashtirilgan to'lov tizimi) -->
            <div id="wallet-tab" class="tab-content">
                <div class="panel" id="wallet-step-1">
                    <h3 style="margin-bottom: 14px; font-size: 18px;">💳 Balansni To'ldirish</h3>
                    <div class="card-box">
                        <div style="font-size: 11px; color: #a5b4fc; font-weight: 700;">RASMIY KARTA (UZCARD / HUMO)</div>
                        <div class="card-number" id="card-num-text">9860 1234 5678 9012</div>
                        <button class="btn-copy" onclick="copyCard()">📋 Karta Raqamini Nusxalash</button>
                    </div>
                    <div class="form-group"><label>UC Miqdori:</label><input type="number" id="uc-topup" value="60" oninput="calcSum()"></div>
                    <div class="form-group"><label>🎁 Hamkor Promokodi (+20% Bonus):</label><input type="text" id="wallet-promo-input" placeholder="PROMOKOD"></div>
                    <div class="form-group"><label>📝 Chek Raqami yoki Izoh (ixtiyoriy):</label><input type="text" id="wallet-receipt" placeholder="Masalan: 123456 yoki vaqti"></div>
                    <p style="color: #c4b5fd; margin-bottom: 16px; font-size: 14px; font-weight: 700;">To'lash kerak: <span id="sum-calc">14000</span> so'm</p>
                    <button class="btn-submit" onclick="requestPayment()">✅ To'lov Qildim (Adminga yuborish)</button>
                </div>
                <div class="panel" id="wallet-step-2" style="display: none; text-align: center;">
                    <h3 style="margin-bottom: 12px; font-size: 18px; color: #10b981;">⏳ To'lov so'rovi yuborildi</h3>
                    <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">Adminlar to'lovingizni tekshirib tasdiqlashlarini kuting. Tasdiqlangach balansingizga avtomatik qo'shiladi.</p>
                    <button class="btn-submit" onclick="resetWalletForm()">Bosh sahifaga qaytish</button>
                </div>
            </div>

            <!-- Promo Tab -->
            <div id="promo-tab" class="tab-content">
                <div class="panel" style="margin-bottom: 20px;">
                    <h3 style="margin-bottom: 14px; font-size: 18px;">🎁 Promokod Faollashtirish</h3>
                    <div class="form-group"><input type="text" id="promo-code-input" placeholder="PROMOKODNI KIRITING"></div>
                    <button class="btn-submit" onclick="activatePromo()">Faollashtirish</button>
                    <p id="promo-msg" style="margin-top: 12px; font-size: 13px; text-align: center; font-weight: 700;"></p>
                </div>
                <div class="panel">
                    <h3 style="margin-bottom: 10px; font-size: 18px;">🤝 Hamkorlik Dasturi</h3>
                    <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">Sizning promokodingiz orqali tushgan daromad:</p>
                    <p style="font-size: 16px; color: #10b981; font-weight: bold; margin-bottom: 14px;"><span id="partner-earned">0</span> Aim</p>
                    <button class="btn-submit" onclick="loadPartnerStats()">Statistikani Yangilash</button>
                </div>
            </div>
        </div>

        <nav class="bottom-nav">
            <button class="nav-item active" onclick="switchTab('cases', this)"><span class="icon">📦</span> <span>Keyslar</span></button>
            <button class="nav-item" onclick="switchTab('inventory', this)"><span class="icon">🎒</span> <span>Inventar</span></button>
            <button class="nav-item" onclick="switchTab('games', this)"><span class="icon">🎮</span> <span>O'yinlar</span></button>
            <button class="nav-item" onclick="switchTab('wallet', this)"><span class="icon">💳</span> <span>To'ldirish</span></button>
            <button class="nav-item" onclick="switchTab('promo', this)"><span class="icon">🎁</span> <span>Hamkor</span></button>
        </nav>

        <script>
            const tg = window.Telegram.WebApp;
            tg.expand();
            const userId = tg.initDataUnsafe?.user?.id || 12345678;

            let balanceAim = 100.0;
            let currentCaseId = null;
            let currentCasePriceUc = 0;
            let currentCasePriceAim = 0;
            let selectedCount = 1;

            function updateUI() {
                document.getElementById('balance').innerText = balanceAim.toFixed(2);
                document.getElementById('uc-balance').innerText = Math.floor((balanceAim / 100) * 60);
            }

            function switchTab(tabName, btn) {
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                document.getElementById(tabName + '-tab').classList.add('active');
                if(btn) btn.classList.add('active');
                if(tabName === 'inventory') loadInventory();
            }

            function copyCard() {
                let cardText = document.getElementById('card-num-text').innerText.replace(/\s+/g, '');
                navigator.clipboard.writeText(cardText);
                alert("Karta raqami nusxalandi!");
            }

            async function loadCases() {
                let res = await fetch('/get_cases');
                let cases = await res.json();
                let html = '';
                for(let id in cases) {
                    let c = cases[id];
                    html += `
                        <div class="case-card" onclick="selectCase('${id}', ${c.price_uc}, ${c.price_aim}, '${c.name}', '${c.img}')">
                            <img src="${c.img}" class="case-img">
                            <h4 style="font-size: 13px; font-weight: 700; margin-top:4px;">${c.name}</h4>
                            <p style="color:#c4b5fd; margin: 6px 0; font-weight: 800; font-size: 13px;">${c.price_uc} UC</p>
                            <button class="btn-open">Ochish</button>
                        </div>
                    `;
                }
                document.getElementById('cases-grid').innerHTML = html;
            }
            loadCases();

            function selectCase(id, priceUc, priceAim, name, img) {
                currentCaseId = id;
                currentCasePriceUc = priceUc;
                currentCasePriceAim = priceAim;
                selectedCount = 1;
                document.querySelectorAll('.count-btn').forEach((b, idx) => b.classList.toggle('active', idx === 0));
                document.getElementById('detail-name').innerText = name;
                document.getElementById('detail-img').src = img;
                document.getElementById('detail-price-text').innerText = `${priceUc} UC (${priceAim} Aim)`;
                document.getElementById('win-result-container').style.display = 'none';
                document.getElementById('roulette-section').style.display = 'none';
                updateOpenCost();
                switchTab('case-detail', null);
            }

            function setCount(count, btn) {
                selectedCount = count;
                document.querySelectorAll('.multi-select .count-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                updateOpenCost();
            }

            function updateOpenCost() {
                let totalUc = currentCasePriceUc * selectedCount;
                let totalAim = currentCasePriceAim * selectedCount;
                document.getElementById('total-open-price').innerText = totalUc.toFixed(1);
                document.getElementById('total-open-aim').innerText = totalAim.toFixed(2);
            }

            async function openSelectedCase() {
                let totalAim = currentCasePriceAim * selectedCount;
                if(balanceAim < totalAim) { alert("AimCoin yetarli emas!"); return; }
                balanceAim -= totalAim;
                updateUI();

                let containerBox = document.getElementById('roulettes-container-box');
                containerBox.innerHTML = '';
                document.getElementById('roulette-section').style.display = 'block';
                document.getElementById('win-result-container').style.display = 'none';

                let res = await fetch(`/open/${currentCaseId}?user_id=${userId}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `count=${selectedCount}`
                });
                let data = await res.json();

                let tracks = [];
                for(let i = 0; i < selectedCount; i++) {
                    let winObj = data.results[i].win_item;
                    let randArr = data.results[i].random_items;
                    
                    let winWindow = document.createElement('div');
                    winWindow.className = 'roulette-track-window';
                    winWindow.innerHTML = `
                        <div class="roulette-pointer"></div>
                        <div class="roulette-track" id="track-${i}"></div>
                    `;
                    containerBox.appendChild(winWindow);

                    let track = document.getElementById(`track-${i}`);
                    let itemsHtml = '';
                    for(let j = 0; j < 40; j++) {
                        let item = (j === 30) ? winObj : randArr[j % randArr.length];
                        itemsHtml += `<div class="roulette-item"><img src="${item.img}"><span>${item.val} Aim</span></div>`;
                    }
                    track.innerHTML = itemsHtml;
                    tracks.push(track);
                }

                setTimeout(() => {
                    tracks.forEach(track => {
                        track.style.transition = 'transform 4s cubic-bezier(0.08, 0.82, 0.17, 1)';
                        track.style.transform = `translateX(-${(30 * 108) - 160}px)`;
                    });
                }, 50);

                setTimeout(() => {
                    let winTextHtml = `🎉 Siz yutib oldingiz: `;
                    let actionsHtml = '';
                    
                    data.results.forEach((resItem, idx) => {
                        let item = resItem.win_item;
                        let invId = resItem.inventory_id;
                        winTextHtml += `<br><b>${item.name}</b> (${item.val} Aim)`;
                        actionsHtml += `
                            <div style="display:flex; gap:6px; flex:1; flex-direction:column;">
                                <span style="font-size:10px; color:var(--text-muted); text-align:center;">#${idx+1} Buyum</span>
                                <div style="display:flex; gap:4px;">
                                    <button class="btn-win-sell" onclick="sellWonItem(${invId}, this)">Sotish (${item.val} Aim)</button>
                                    <button class="btn-win-keep" onclick="keepWonItem(this)">Saqlash</button>
                                </div>
                            </div>
                        `;
                    });

                    document.getElementById('win-result-text').innerHTML = winTextHtml;
                    document.getElementById('win-actions-box').innerHTML = actionsHtml;
                    document.getElementById('win-result-container').style.display = 'block';
                }, 4100);
            }

            async function sellWonItem(inventoryId, btnElement) {
                let res = await fetch('/sell_item', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `item_id=${inventoryId}&user_id=${userId}`
                });
                let data = await res.json();
                if(data.success) {
                    balanceAim = data.new_aim;
                    updateUI();
                    btnElement.parentElement.innerHTML = `<span style="color:#ef4444; font-size:11px; font-weight:bold; text-align:center; width:100%;">Sotildi! (+${data.sold_val} Aim)</span>`;
                } else {
                    alert(data.msg);
                }
            }

            function keepWonItem(btnElement) {
                btnElement.parentElement.innerHTML = `<span style="color:#10b981; font-size:11px; font-weight:bold; text-align:center; width:100%;">Saqlangan (Inventarda)</span>`;
            }

            async function loadInventory() {
                let res = await fetch(`/get_inventory/${userId}`);
                let items = await res.json();
                let grid = document.getElementById('inventory-grid');
                if(items.length === 0) {
                    grid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: var(--text-muted); font-size: 13px;">Inventaringiz bo'sh.</p>`;
                    return;
                }
                let html = '';
                items.forEach(item => {
                    html += `
                        <div class="inv-card" id="inv-item-${item.id}">
                            <img src="${item.img}">
                            <div style="font-size: 11px; font-weight: bold; margin-bottom: 2px;">${item.name}</div>
                            <div style="font-size: 10px; color: #c4b5fd; font-weight: bold;">${item.val} Aim</div>
                            <div class="inv-actions">
                                <button class="btn-inv-sell" onclick="sellInventoryItem(${item.id})">Sotish</button>
                                <button class="btn-inv-keep" onclick="alert('Buyum allaqachon inventaringizda saqlangan!')">Saqlangan</button>
                            </div>
                        </div>
                    `;
                });
                grid.innerHTML = html;
            }

            async function sellInventoryItem(itemId) {
                let res = await fetch('/sell_item', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `item_id=${itemId}&user_id=${userId}`
                });
                let data = await res.json();
                if(data.success) {
                    balanceAim = data.new_aim;
                    updateUI();
                    let el = document.getElementById(`inv-item-${itemId}`);
                    if(el) el.remove();
                } else {
                    alert(data.msg);
                }
            }

            function switchGame(game, btn) {
                document.querySelectorAll('.sub-game').forEach(el => el.style.display = 'none');
                document.querySelectorAll('.game-tab-btn').forEach(b => b.classList.remove('active'));
                document.getElementById('game-' + game).style.display = 'block';
                btn.classList.add('active');
            }

            let minesBoard = document.getElementById('mines-board');
            for(let i=0; i<25; i++) {
                let cell = document.createElement('button');
                cell.className = 'mine-cell';
                cell.innerText = '💎';
                minesBoard.appendChild(cell);
            }
            function startMines() {
                let bet = parseFloat(document.getElementById('mines-bet').value) || 10;
                if(balanceAim < bet) { alert("Aim yetarli emas!"); return; }
                balanceAim -= bet; updateUI();
                document.querySelectorAll('.mine-cell').forEach(c => {
                    c.innerText = '💎';
                    c.onclick = () => {
                        let win = bet * 1.5;
                        balanceAim += win; updateUI();
                        alert(`Tabriklaymiz! +${win.toFixed(1)} Aim yutdingiz!`);
                    };
                });
            }

            let towerBoard = document.getElementById('tower-board');
            for(let i=0; i<4; i++) {
                let row = document.createElement('div');
                row.className = 'tower-row';
                for(let j=0; j<3; j++) {
                    let btn = document.createElement('button');
                    btn.className = 'tower-cell';
                    btn.innerText = '•';
                    row.appendChild(btn);
                }
                towerBoard.appendChild(row);
            }
            function startTower() {
                let bet = parseFloat(document.getElementById('tower-bet').value) || 10;
                if(balanceAim < bet) { alert("Aim yetarli emas!"); return; }
                balanceAim -= bet; updateUI();
                alert("Tower o'yini boshlandi!");
            }

            function startCrash() {
                let bet = parseFloat(document.getElementById('crash-bet').value) || 10;
                if(balanceAim < bet) { alert("Aim yetarli emas!"); return; }
                balanceAim -= bet; updateUI();
                let mult = 1.0;
                let multElem = document.getElementById('crash-mult');
                let timer = setInterval(() => {
                    mult += 0.05;
                    multElem.innerText = mult.toFixed(2) + 'x';
                    if(Math.random() < 0.05) {
                        clearInterval(timer);
                        multElem.innerText = "CRASHED (" + mult.toFixed(2) + "x)";
                    }
                }, 100);
            }

            function calcSum() {
                let uc = parseFloat(document.getElementById('uc-topup').value) || 0;
                document.getElementById('sum-calc').innerText = Math.round((uc / 60) * 14000);
            }

            async function requestPayment() {
                let uc = parseFloat(document.getElementById('uc-topup').value) || 60;
                let promo = document.getElementById('wallet-promo-input').value.trim();
                let receipt = document.getElementById('wallet-receipt').value.trim();
                let res = await fetch('/topup_webhook', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `uc=${uc}&user_id=${userId}&promo=${encodeURIComponent(promo)}&receipt=${encodeURIComponent(receipt)}`
                });
                let data = await res.json();
                if(data.success) {
                    document.getElementById('wallet-step-1').style.display = 'none';
                    document.getElementById('wallet-step-2').style.display = 'block';
                } else {
                    alert(data.msg);
                }
            }

            function resetWalletForm() {
                document.getElementById('wallet-step-2').style.display = 'none';
                document.getElementById('wallet-step-1').style.display = 'block';
                switchTab('cases', document.querySelectorAll('.bottom-nav button')[0]);
            }

            async function activatePromo() {
                let code = document.getElementById('promo-code-input').value.trim();
                let msg = document.getElementById('promo-msg');
                let res = await fetch('/activate_promo', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `code=${code}&user_id=${userId}`
                });
                let data = await res.json();
                msg.style.color = data.success ? "#10b981" : "#ef4444";
                msg.innerText = data.msg;
                if(data.success) { balanceAim += data.reward_aim; updateUI(); }
            }
            async function loadPartnerStats() {
                let res = await fetch(`/partner_stats/${userId}`);
                let data = await res.json();
                document.getElementById('partner-earned').innerText = data.earned;
            }
        </script>
    </body>
    </html>
    """)

@app.get("/get_cases")
async def get_cases():
    return CASES

@app.post("/open/{case_id}")
async def open_case(case_id: str, user_id: int, count: int = Form(1)):
    case = CASES[case_id]
    items = case["items"]
    chances = [item["chance"] for item in items]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    results = []
    for _ in range(count):
        win_item = random.choices(items, weights=chances, k=1)[0]
        random_items = [random.choice(items) for _ in range(15)]
        
        cursor.execute("INSERT INTO inventory (user_id, name, val, img) VALUES (?, ?, ?, ?)", 
                       (user_id, win_item["name"], win_item["val"], win_item["img"]))
        inventory_id = cursor.lastrowid
        
        results.append({
            "win_item": win_item, 
            "random_items": random_items,
            "inventory_id": inventory_id
        })
    conn.commit()
    conn.close()
    
    return {"results": results}

@app.get("/get_inventory/{user_id}")
async def get_inventory(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, val, img FROM inventory WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/sell_item")
async def sell_item(item_id: int = Form(...), user_id: int = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT val FROM inventory WHERE id = ? AND user_id = ?", (item_id, user_id))
    item = cursor.fetchone()
    if not item:
        conn.close()
        return {"success": False, "msg": "Buyum topilmadi yoki allaqachon sotilgan!"}
    
    aim_val = item["val"]
    cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    cursor.execute("UPDATE users SET aimcoin = aimcoin + ? WHERE user_id = ?", (aim_val, user_id))
    cursor.execute("SELECT aimcoin FROM users WHERE user_id = ?", (user_id,))
    new_aim = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return {"success": True, "new_aim": new_aim, "sold_val": aim_val}

@app.post("/topup_webhook")
async def topup_webhook(uc: float = Form(...), user_id: int = Form(...), promo: str = Form(""), receipt: str = Form("")):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Dublikat to'lovlarni bloklash (aynan shu miqdorda pending to'lov mavjudligini tekshirish)
    cursor.execute("SELECT id FROM payments WHERE amount = ? AND status = 'pending'", (uc,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "msg": "⚠️ Bu miqdordagi to'lov hozirda boshqa foydalanuvchi tomonidan amalga oshirilmoqda. Biroz farqli summa kiriting!"}

    if promo:
        cursor.execute("SELECT max_uses, used_count FROM promos WHERE code = ?", (promo.upper(),))
        p_data = cursor.fetchone()
        if not p_data:
            conn.close()
            return {"success": False, "msg": "Bunday promokod topilmadi!"}
        if p_data["used_count"] >= p_data["max_uses"]:
            conn.close()
            return {"success": False, "msg": "Promokod muddati tugagan!"}

    cursor.execute("INSERT INTO payments (user_id, amount, promo, receipt_info, status) VALUES (?, ?, ?, ?, 'pending')", (user_id, uc, promo, receipt))
    payment_id = cursor.lastrowid
    
    cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
    usr = cursor.fetchone()
    username = usr["username"] if usr and usr["username"] else str(user_id)
    conn.commit()
    conn.close()

    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_payment_{payment_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_payment_{payment_id}")
        ]
    ])

    for adm in ADMINS:
        try:
            await bot.send_message(
                adm,
                f"🔔 **Yangi to'lov so'rovi!**\n\n"
                f"👤 Foydalanuvchi: @{username} (`{user_id}`)\n"
                f"💰 Summa: {uc} UC\n"
                f"🎁 Promokod: {promo if promo else 'Yoq'}\n"
                f"📝 Chek/Izoh: {receipt if receipt else 'Kiritilmagan'}\n"
                f"🆔 To'lov ID: #{payment_id}",
                reply_markup=admin_markup,
                parse_mode="Markdown"
            )
        except Exception:
            pass

    return {"success": True, "msg": "To'lov so'rovi adminga yuborildi!"}

@app.post("/activate_promo")
async def activate_promo(code: str = Form(...), user_id: int = Form(...)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT reward, max_uses, used_count, owner_id FROM promos WHERE code = ?", (code.upper(),))
        promo = cursor.fetchone()
        if not promo: return {"success": False, "msg": "Promokod topilmadi!"}
        reward, max_uses, used_count, owner_id = promo
        if used_count >= max_uses: return {"success": False, "msg": "Promokod muddati tugagan!"}
        
        reward_aim = (reward / 60) * 100
        cursor.execute("UPDATE promos SET used_count = used_count + 1 WHERE code = ?", (code.upper(),))
        cursor.execute("UPDATE users SET aimcoin = aimcoin + ? WHERE user_id = ?", (reward_aim, user_id))
        
        if owner_id and owner_id != user_id:
            partner_bonus = reward_aim * 0.20
            cursor.execute("UPDATE users SET partner_earned = partner_earned + ? WHERE user_id = ?", (partner_bonus, owner_id))
        conn.commit()
    finally:
        conn.close()
    return {"success": True, "reward_aim": reward_aim, "msg": f"+{reward_aim:.1f} Aim berildi!"}

@app.get("/partner_stats/{user_id}")
async def partner_stats(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT partner_earned FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return {"earned": res["partner_earned"] if res else 0.0}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=10000)
