import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from database import get_connection, is_admin

TOKEN = "8253855521:AAEVWGNmNMCaPS7kzrwtqKn1UTUtVLfH9jo" # Bot tokeningiz
SUPER_ADMIN_ID = 8692517241
CARD_NUMBER = "5614686507631458"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class PartnerState(StatesGroup):
    waiting_for_site_id = State()

@dp.message(Command("start", "admin"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        admin_menu = (
            "👑 **Admin Panel (Aimdrop):**\n\n"
            "📋 **Buyruqlar:**\n"
            "/stats - Statistika\n"
            "/ucrequests - PUBG UC so'rovlari\n"
            "/promolist - Promo-kodlar ro'yxati\n"
            "/addpromo <kod> <summa> <limit> - Promo yaratish\n"
            "/delpromo <kod> - Promoni o'chirish\n"
            "/partners - Hamkorlar\n"
            "/addbalance <tg_id> <summa> - Balans qo'shish\n"
        )
        if user_id == SUPER_ADMIN_ID:
            admin_menu += (
                "\n⭐ **Super Admin:**\n"
                "/addadmin <tg_id> - Admin qo'shish\n"
                "/deladmin <tg_id> - Adminni o'chirish\n"
                "/adminlist - Adminlar ro'yxati"
            )
        await message.answer(admin_menu)
    else:
        await message.answer(
            f"👋 **Aimdrop Botiga xush kelibsiz!**\n\n"
            f"💳 **Balansni to'ldirish uchun Karta:**\n`{CARD_NUMBER}`\n"
            "Pulni tashlab, chek yoki skrinni adminga yuboring.\n\n"
            "Hamkor bo'lish uchun:\n"
            "/be_partner - Saytdagi ID raqamni yuborish"
        )

@dp.message(Command("partners"))
async def cmd_partners(message: types.Message):
    if not is_admin(message.from_user.id): return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE is_partner = 1")
    partners = cursor.fetchall()
    text = "🤝 **Hamkorlar ro'yxati:**\n\n"
    for p in partners:
        cursor.execute("SELECT code FROM promo_codes WHERE partner_id = ?", (p['id'],))
        promo = cursor.fetchone()
        text += f"👤 @{p['username']} | Demo: `{p['demo_balance']}` | Kod: `{promo['code'] if promo else 'Yoq'}`\n"
    conn.close()
    await message.answer(text)

@dp.message(Command("ucrequests"))
async def cmd_ucrequests(message: types.Message):
    if not is_admin(message.from_user.id): return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ucr.*, u.username, u.telegram_id FROM uc_requests ucr JOIN users u ON ucr.user_id = u.id WHERE ucr.status = 'pending'")
    reqs = cursor.fetchall()
    conn.close()
    if not reqs:
        await message.answer("📭 Yangi PUBG UC so'rovlari yo'q.")
        return
    text = "🎮 **PUBG UC So'rovlari:**\n\n"
    for r in reqs:
        text += f"🆔 ID: `{r['id']}` | @{r['username']} | PUBG ID: `{r['pubg_id']}` | `{r['uc_amount']} UC`\nTasdiqlash uchun: `/ucdone {r['id']}`\n\n"
    await message.answer(text)

@dp.message(Command("ucdone"))
async def cmd_ucdone(message: types.Message):
    if not is_admin(message.from_user.id): return
    parts = message.text.split()
    if len(parts) < 2: return
    req_id = int(parts[1])
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ucr.*, u.telegram_id FROM uc_requests ucr JOIN users u ON ucr.user_id = u.id WHERE ucr.id = ?", (req_id,))
    req = cursor.fetchone()
    if req:
        cursor.execute("UPDATE uc_requests SET status = 'completed' WHERE id = ?", (req_id,))
        conn.commit()
        await message.answer(f"✅ #{req_id}-sonli UC bajarildi.")
        try:
            await bot.send_message(req['telegram_id'], f"🎉 Sizning `{req['uc_amount']} UC` buyurtmangiz PUBG ID ({req['pubg_id']}) ga tashlab berildi!")
        except:
            pass
    conn.close()

@dp.message(Command("addbalance"))
async def cmd_addbalance(message: types.Message):
    if not is_admin(message.from_user.id): return
    parts = message.text.split()
    if len(parts) < 3: return
    tg_id, amount = int(parts[1]), float(parts[2])
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE telegram_id = ?", (amount, tg_id))
    conn.commit()
    conn.close()
    await message.answer(f"✅ Balansga qo'shildi: `{tg_id}` -> `{amount} so'm`")

@dp.message(Command("addpromo"))
async def cmd_addpromo(message: types.Message):
    if not is_admin(message.from_user.id): return
    parts = message.text.split()
    if len(parts) < 4: return
    code, amount, max_uses = parts[1].upper(), float(parts[2]), int(parts[3])
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO promo_codes (code, reward_amount, max_uses) VALUES (?, ?, ?)", (code, amount, max_uses))
        conn.commit()
        await message.answer(f"✅ Promo yaratildi: `{code}`")
    except Exception as e:
        await message.answer(f"Xatolik: {e}")
    finally:
        conn.close()

@dp.message(Command("promolist"))
async def cmd_promolist(message: types.Message):
    if not is_admin(message.from_user.id): return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM promo_codes")
    promos = cursor.fetchall()
    conn.close()
    text = "🎟 **Promo-kodlar:**\n"
    for p in promos:
        text += f"🔹 `{p['code']}` - {p['reward_amount']} so'm ({p['used_count']}/{p['max_uses']})\n"
    await message.answer(text)

@dp.message(Command("delpromo"))
async def cmd_delpromo(message: types.Message):
    if not is_admin(message.from_user.id): return
    parts = message.text.split()
    if len(parts) < 2: return
    code = parts[1].upper()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM promo_codes WHERE code = ?", (code,))
    conn.commit()
    conn.close()
    await message.answer(f"✅ O'chirildi: `{code}`")

@dp.message(Command("addadmin"))
async def cmd_addadmin(message: types.Message):
    if message.from_user.id != SUPER_ADMIN_ID: return
    parts = message.text.split()
    if len(parts) < 2: return
    new_id = int(parts[1])
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (telegram_id, username, added_by) VALUES (?, ?, ?)", (new_id, f"Admin_{new_id}", message.from_user.id))
    conn.commit()
    conn.close()
    await message.answer(f"✅ Admin qo'shildi: `{new_id}`")

@dp.message(Command("deladmin"))
async def cmd_deladmin(message: types.Message):
    if message.from_user.id != SUPER_ADMIN_ID: return
    parts = message.text.split()
    if len(parts) < 2: return
    target_id = int(parts[1])
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admins WHERE telegram_id = ?", (target_id,))
    conn.commit()
    conn.close()
    await message.answer(f"✅ Admin o'chirildi: `{target_id}`")

@dp.message(Command("adminlist"))
async def cmd_adminlist(message: types.Message):
    if message.from_user.id != SUPER_ADMIN_ID: return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins")
    admins = cursor.fetchall()
    conn.close()
    text = f"⭐ Super Admin: `{SUPER_ADMIN_ID}`\n"
    for a in admins:
        text += f"🔹 Admin: `{a['telegram_id']}`\n"
    await message.answer(text)

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if not is_admin(message.from_user.id): return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM uc_requests WHERE status = 'pending'")
    uc_reqs = cursor.fetchone()[0]
    conn.close()
    await message.answer(f"📊 Jami foydalanuvchilar: {users}\n⚡ Kutilayotgan UC so'rovlari: {uc_reqs}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
