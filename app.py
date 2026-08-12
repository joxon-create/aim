import random
import sqlite3
import threading
import asyncio
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

app = FastAPI()

# --- SOZLAMALAR ---
BOT_TOKEN = "8253855521:AAExh7BzHiyQnmrubfod3fcjK3tgQ-iaDoM"
SUPER_ADMIN_ID = 8692517241  # Katta admin ID raqami

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
            pubg_id TEXT,
            partner_code TEXT,
            partner_earned REAL DEFAULT 0.0,
            referred_count INTEGER DEFAULT 0
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
            owner_id INTEGER DEFAULT 0,
            earned_from_promo REAL DEFAULT 0.0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uc_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            pubg_id TEXT,
            uc_amount REAL,
            status TEXT DEFAULT 'pending'
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
    cursor.execute("INSERT OR IGNORE INTO admins (admin_id) VALUES (?)", (SUPER_ADMIN_ID,))
    conn.commit()
    conn.close()

init_db()

def is_admin(user_id: int) -> bool:
    if user_id == SUPER_ADMIN_ID:
        return True
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE admin_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

# --- TELEGRAM BOT QISMI (ADMIN VA USER) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, aimcoin) VALUES (?, ?, 100.0)", (user_id, username))
    conn.commit()
    conn.close()

    admin_text = ""
    if is_admin(user_id):
        admin_text = "\n\n🛠 **Admin Buyruqlari:**\n/addpromo [kod] [uc] [limit] - Promokod qo'shish\n/addadmin [user_id] - Admin qo'shish\n/stats - Statistika"

    await message.answer(
        f"🔥 **BULLDROP / AIMDROP** rasmiy botiga xush kelibsiz!\n"
        f"Sizning Telegram ID raqamingiz: `{user_id}`{admin_text}",
        parse_mode="Markdown"
    )

@dp.message(Command("addpromo"))
async def cmd_addpromo(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    args = message.text.split()
    if len(args) < 4:
        await message.answer("⚠️ Format: `/addpromo [KOD] [UC] [LIMIT]`", parse_mode="Markdown")
        return
    code, reward, limit = args[1].upper(), float(args[2]), int(args[3])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO promos (code, reward, max_uses, used_count) VALUES (?, ?, ?, 0)", (code, reward, limit))
    conn.commit()
    conn.close()
    await message.answer(f"✅ Promokod yaratildi: `{code}` ({reward} UC)", parse_mode="Markdown")

@dp.message(Command("addadmin"))
async def cmd_addadmin(message: types.Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        await message.answer("❌ Faqat Katta Admin qo'shishi mumkin!")
        return
    args = message.text.split()
    if len(args) < 2:
        return
    new_admin = int(args[1])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (admin_id) VALUES (?)", (new_admin,))
    conn.commit()
    conn.close()
    await message.answer(f"✅ {new_admin} admin qilindi.")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    u_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM demo_requests WHERE status='pending'")
    d_count = cursor.fetchone()[0]
    conn.close()
    await message.answer(f"📊 **Statistika:**\n👥 Foydalanuvchilar: {u_count}\n⏳ Kutilayotgan demo so'rovlar: {d_count}")

# Demo balansni tasdiqlash handlerlari
@dp.callback_query(F.data.startswith("approve_demo_"))
async def approve_demo(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    req_id = int(callback.data.split("_")[2])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, amount, status FROM demo_requests WHERE id = ?", (req_id,))
    req = cursor.fetchone()
    if not req or req["status"] != "pending":
        await callback.answer("So'rov allaqachon bajarilgan!", show_alert=True)
        conn.close()
        return
    
    user_id, amount = req["user_id"], req["amount"]
    aim_add = (amount / 60) * 100
    cursor.execute("UPDATE users SET aimcoin = aimcoin + ? WHERE user_id = ?", (aim_add, user_id))
    cursor.execute("UPDATE demo_requests SET status = 'approved' WHERE id = ?", (req_id,))
    conn.commit()
    conn.close()

    await callback.message.edit_text(f"✅ Demo so'rov (#{req_id}) tasdiqlandi! Foydalanuvchiga {amount} UC ({aim_add} Aim) qo'shildi.")
    await bot.send_message(user_id, f"🎉 Tabriklaymiz! Admin sizning demo balans so'rovingizni tasdiqladi: +{amount} UC qo'shildi.")

@dp.callback_query(F.data.startswith("reject_demo_"))
async def reject_demo(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    req_id = int(callback.data.split("_")[2])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE demo_requests SET status = 'rejected' WHERE id = ?", (req_id,))
    conn.commit()
    conn.close()
    await callback.message.edit_text(f"❌ Demo so'rov (#{req_id}) rad etildi.")

def run_telegram_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(dp.start_polling(bot))

@app.on_event("startup")
def startup_event():
    t = threading.Thread(target=run_telegram_bot, daemon=True)
    t.start()

# --- PUBG ITEMS VA CASES POOL ---
PUBG_ITEMS_POOL = [
    {"name": "M416 'Lednik'", "val": 18000, "img": "https://cdn-icons-png.flaticon.com/512/3076/3076137.png", "chance": 0.000001},
    {"name": "M416 'Glacier'", "val": 2800, "img": "https://cdn-icons-png.flaticon.com/512/3076/3076137.png", "chance": 0.00005},
    {"name": "AWM 'The Fool'", "val": 2500, "img": "https://cdn-icons-png.flaticon.com/512/1069/1069158.png", "chance": 0.0001},
    {"name": "Pan 'BFC'", "val": 450, "img": "https://cdn-icons-png.flaticon.com/512/1046/1046857.png", "chance": 0.2},
    {"name": "Helmet Lv.3", "val": 350, "img": "https://cdn-icons-png.flaticon.com/512/807/807281.png", "chance": 0.5},
    {"name": "Silver Fragment", "val": 5, "img": "https://cdn-icons-png.flaticon.com/512/217/217853.png", "chance": 30.0},
]

CASE_IMAGES = ["https://cdn-icons-png.flaticon.com/512/3313/3313498.png"] * 20
CASES = {}
case_names = [f"Case #{i+1}" for i in range(20)]
for i, name in enumerate(case_names):
    price = 10 if i == 0 else (300 if i == 19 else round(10 + (290 / 18) * i, 1))
    items = [dict(item, val=round(price * random.uniform(0.2, 2.0), 1)) for item in PUBG_ITEMS_POOL]
    while len(items) < 20: items.append(random.choice(PUBG_ITEMS_POOL))
    CASES[f"case_{i+1}"] = {"name": name, "price": price, "img": CASE_IMAGES[i], "items": items}

# --- WEB APP FRONTEND & BACKEND ---
@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bulldrop / AimDrop</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            body { background: #0b0f19; color: #fff; min-height: 100vh; display: flex; flex-direction: column; }
            header { display: flex; justify-content: space-between; align-items: center; background: #131b2e; padding: 12px 20px; border-bottom: 1px solid #1f2b45; }
            .logo { font-size: 20px; font-weight: bold; color: #f39c12; }
            .balance-container { background: #1a233a; border: 1px solid #f39c12; padding: 5px 12px; border-radius: 20px; font-weight: bold; color: #f39c12; font-size: 13px; }
            .container { max-width: 1200px; margin: 0 auto; width: 100%; padding: 15px; flex: 1; padding-bottom: 90px; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            .cases-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
            .case-card { background: #131b2e; border: 1px solid #1f2b45; border-radius: 12px; padding: 12px; text-align: center; cursor: pointer; }
            .case-img { width: 70px; height: 70px; object-fit: contain; margin: 8px auto; display: block; }
            .btn-open { background: linear-gradient(135deg, #f39c12, #d35400); color: #fff; border: none; padding: 7px; width: 100%; border-radius: 6px; font-weight: bold; margin-top: 8px; cursor: pointer; }
            
            .roulette-container { background: #131b2e; border: 1px solid #1f2b45; border-radius: 12px; padding: 15px; text-align: center; max-width: 600px; margin: 15px auto; }
            .roulette-track-window { width: 100%; overflow: hidden; position: relative; height: 120px; background: #0b0f19; border-radius: 8px; border: 1px solid #2a3a5a; margin-bottom: 15px; }
            .roulette-pointer { position: absolute; top: 0; bottom: 0; left: 50%; width: 3px; background: #f39c12; transform: translateX(-50%); z-index: 10; }
            .roulette-track { display: flex; position: absolute; left: 0; top: 6px; transition: transform 4s cubic-bezier(0.08, 0.82, 0.17, 1); }
            .roulette-item { min-width: 100px; height: 105px; background: #1a233a; border: 1px solid #2a3a5a; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0 5px; font-size: 11px; padding: 4px; }
            .roulette-item img { width: 45px; height: 45px; object-fit: contain; margin-bottom: 4px; }

            .panel { background: #131b2e; border: 1px solid #1f2b45; padding: 20px; border-radius: 12px; max-width: 420px; margin: 0 auto; }
            .form-group { margin-bottom: 12px; }
            .form-group label { display: block; margin-bottom: 5px; color: #8b9bb4; font-size: 12px; }
            .form-group input { width: 100%; padding: 10px; background: #0b0f19; border: 1px solid #1f2b45; color: #fff; border-radius: 6px; font-size: 14px; text-align: center; }
            .btn-submit { background: linear-gradient(135deg, #f39c12, #d35400); color: #fff; border: none; padding: 10px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; }

            .bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: #131b2e; border-top: 1px solid #1f2b45; display: flex; justify-content: space-around; padding: 8px 0; z-index: 100; }
            .nav-item { background: transparent; border: none; color: #8b9bb4; cursor: pointer; font-size: 11px; display: flex; flex-direction: column; align-items: center; gap: 2px; font-weight: 600; }
            .nav-item.active { color: #f39c12; }
            .nav-item span.icon { font-size: 18px; }
        </style>
    </head>
    <body>
        <header>
            <div class="logo">🔥 BULLDROP</div>
            <div class="balance-container"><span id="balance">100.00</span> Aim (<span id="uc-balance">60</span> UC)</div>
        </header>

        <div class="container">
            <!-- Cases Tab -->
            <div id="cases-tab" class="tab-content active">
                <h3 style="margin-bottom: 12px;">PUBG Кейслар</h3>
                <div class="cases-grid" id="cases-grid"></div>
            </div>

            <!-- Roulette Tab -->
            <div id="roulette-tab" class="tab-content">
                <div class="roulette-container">
                    <h3 style="margin-bottom: 12px;" id="case-title-run">Keys ochilmoqda...</h3>
                    <div class="roulette-track-window">
                        <div class="roulette-pointer"></div>
                        <div class="roulette-track" id="track"></div>
                    </div>
                    <div id="win-result" style="font-size: 16px; font-weight: bold; color: #00ffcc; margin-bottom: 12px; min-height: 20px;"></div>
                    <button class="btn-submit" onclick="switchTab('cases', document.querySelectorAll('.bottom-nav button')[0])" id="back-btn" style="display:none; max-width: 180px; margin: 0 auto;">Orqaga</button>
                </div>
            </div>

            <!-- Wallet Tab -->
            <div id="wallet-tab" class="tab-content">
                <div class="panel" id="wallet-step-1">
                    <h3 style="margin-bottom: 12px;">Balansni to'ldirish</h3>
                    <div class="form-group"><label>Karta raqami:</label><input type="text" id="card-input" placeholder="8600 0000 0000 0000"></div>
                    <div class="form-group"><label>UC miqdori:</label><input type="number" id="uc-topup" value="60" oninput="calcSum()"></div>
                    <p style="color: #f39c12; margin-bottom: 12px; font-size: 13px;">Summa: <span id="sum-calc">14000</span> so'm</p>
                    <button class="btn-submit" onclick="requestSMS()">SMS kodni olish</button>
                </div>
                <div class="panel" id="wallet-step-2" style="display: none;">
                    <h3>SMS Tasdiqlash</h3>
                    <div class="form-group" style="margin-top: 10px;"><input type="text" id="sms-code-input" placeholder="• • • •" maxlength="4"></div>
                    <button class="btn-submit" onclick="confirmPayment()">Tasdiqlash</button>
                </div>
            </div>

            <!-- Promo & Partner Tab -->
            <div id="promo-tab" class="tab-content">
                <div class="panel" style="margin-bottom: 15px;">
                    <h3 style="margin-bottom: 10px;">Promokod kiritish</h3>
                    <div class="form-group"><input type="text" id="promo-code-input" placeholder="PROMOKOD"></div>
                    <button class="btn-submit" onclick="activatePromo()">Faollashtirish</button>
                    <p id="promo-msg" style="margin-top: 8px; font-size: 12px; text-align: center;"></p>
                </div>
                <div class="panel">
                    <h3 style="margin-bottom: 10px;">Hamkorlik (20% Bonus)</h3>
                    <p style="font-size: 12px; color: #8b9bb4; margin-bottom: 10px;">Sizning promokodingiz orqali kelganlardan tushgan foyda statistikasi:</p>
                    <p style="font-size: 14px; color: #00ffcc; font-weight: bold; margin-bottom: 10px;">Ishlab topilgan: <span id="partner-earned">0</span> UC</p>
                    <button class="btn-submit" onclick="loadPartnerStats()">Statistikani yangilash</button>
                </div>
            </div>

            <!-- Demo Balance Tab -->
            <div id="demo-tab" class="tab-content">
                <div class="panel">
                    <h3 style="margin-bottom: 10px;">Video uchun Demo Balans</h3>
                    <p style="font-size: 12px; color: #8b9bb4; margin-bottom: 12px;">Video olish uchun Telegram ID orqali adminga demo balans so'rovini yuboring.</p>
                    <div class="form-group"><label>Demo UC miqdori:</label><input type="number" id="demo-amount" value="500"></div>
                    <button class="btn-submit" onclick="requestDemo()">So'rov yuborish</button>
                    <p id="demo-msg" style="margin-top: 10px; font-size: 12px; text-align: center;"></p>
                </div>
            </div>
        </div>

        <nav class="bottom-nav">
            <button class="nav-item active" onclick="switchTab('cases', this)"><span class="icon">📦</span> <span>Keyslar</span></button>
            <button class="nav-item" onclick="switchTab('wallet', this)"><span class="icon">💳</span> <span>To'ldirish</span></button>
            <button class="nav-item" onclick="switchTab('promo', this)"><span class="icon">🎁</span> <span>Promo/Hamkor</span></button>
            <button class="nav-item" onclick="switchTab('demo', this)"><span class="icon">🎬</span> <span>Demo Balans</span></button>
        </nav>

        <script>
            const tg = window.Telegram.WebApp;
            tg.expand();
            const userId = tg.initDataUnsafe?.user?.id || 12345678;

            let balanceAim = 100.0;

            function updateUI() {
                document.getElementById('balance').innerText = balanceAim.toFixed(2);
                document.getElementById('uc-balance').innerText = Math.floor((balanceAim / 100) * 60);
            }

            function switchTab(tabName, btn) {
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                document.getElementById(tabName + '-tab').classList.add('active');
                if(btn) btn.classList.add('active');
            }

            function calcSum() {
                let uc = parseFloat(document.getElementById('uc-topup').value) || 0;
                document.getElementById('sum-calc').innerText = Math.round((uc / 60) * 14000);
            }

            async function loadCases() {
                let res = await fetch('/get_cases');
                let cases = await res.json();
                let html = '';
                for(let id in cases) {
                    let c = cases[id];
                    let aimPrice = (c.price / 60) * 100;
                    html += `
                        <div class="case-card" onclick="startRoulette('${id}', ${aimPrice}, '${c.name}')">
                            <img src="${c.img}" class="case-img">
                            <h4 style="font-size: 12px;">${c.name}</h4>
                            <p style="color:#f39c12; margin: 6px 0; font-weight: bold;">${c.price} UC</p>
                            <button class="btn-open">Ochish</button>
                        </div>
                    `;
                }
                document.getElementById('cases-grid').innerHTML = html;
            }
            loadCases();

            function requestSMS() {
                document.getElementById('wallet-step-1').style.display = 'none';
                document.getElementById('wallet-step-2').style.display = 'block';
            }

            async function confirmPayment() {
                let uc = parseFloat(document.getElementById('uc-topup').value) || 60;
                let res = await fetch('/topup_webhook', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `uc=${uc}&user_id=${userId}`
                });
                let data = await res.json();
                if(data.success) {
                    balanceAim = data.new_aim;
                    updateUI();
                    alert("To'lov muvaffaqiyatli amalga oshirildi!");
                    document.getElementById('wallet-step-2').style.display = 'none';
                    document.getElementById('wallet-step-1').style.display = 'block';
                    switchTab('cases', document.querySelectorAll('.bottom-nav button')[0]);
                }
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
                msg.style.color = data.success ? "#00ffcc" : "#ff3366";
                msg.innerText = data.msg;
                if(data.success) { balanceAim += data.reward_aim; updateUI(); }
            }

            async function loadPartnerStats() {
                let res = await fetch(`/partner_stats/${userId}`);
                let data = await res.json();
                document.getElementById('partner-earned').innerText = data.earned;
            }

            async function requestDemo() {
                let amount = parseFloat(document.getElementById('demo-amount').value) || 100;
                let msg = document.getElementById('demo-msg');
                let res = await fetch('/request_demo', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `user_id=${userId}&amount=${amount}`
                });
                let data = await res.json();
                msg.style.color = data.success ? "#00ffcc" : "#ff3366";
                msg.innerText = data.msg;
            }

            async function startRoulette(caseId, priceAim, caseName) {
                if(balanceAim < priceAim) { alert("AimCoin yetarli emas!"); return; }
                balanceAim -= priceAim;
                updateUI();

                switchTab('roulette', null);
                document.getElementById('case-title-run').innerText = caseName + " ochilmoqda...";
                document.getElementById('win-result').innerText = "";
                document.getElementById('back-btn').style.display = "none";

                let res = await fetch('/open/' + caseId, {method: 'POST'});
                let data = await res.json();

                let track = document.getElementById('track');
                track.style.transition = 'none';
                track.style.transform = 'translateX(0px)';

                let itemsHtml = '';
                let winningIndex = 35;
                for(let i = 0; i < 50; i++) {
                    let item = (i === winningIndex) ? data.win_item : data.random_items[i % data.random_items.length];
                    itemsHtml += `<div class="roulette-item"><img src="${item.img}"><span>${item.val} UC</span></div>`;
                }
                track.innerHTML = itemsHtml;

                setTimeout(() => {
                    track.style.transition = 'transform 4s cubic-bezier(0.08, 0.82, 0.17, 1)';
                    let targetOffset = (winningIndex * 110) - 220;
                    track.style.transform = `translateX(-${targetOffset}px)`;
                }, 50);

                setTimeout(() => {
                    let wonAim = (data.win_item.val / 60) * 100;
                    balanceAim += wonAim;
                    updateUI();
                    document.getElementById('win-result').innerHTML = `🎉 Yutib oldingiz: ${data.win_item.name} (${data.win_item.val} UC)`;
                    document.getElementById('back-btn').style.display = "block";
                }, 4100);
            }
        </script>
    </body>
    </html>
    """)

@app.get("/get_cases")
async def get_cases():
    return CASES

@app.post("/topup_webhook")
async def topup_webhook(uc: float = Form(...), user_id: int = Form(...)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        aim_add = (uc / 60) * 100
        cursor.execute("UPDATE users SET aimcoin = aimcoin + ?, total_donated = total_donated + ? WHERE user_id = ?", (aim_add, uc, user_id))
        cursor.execute("SELECT aimcoin FROM users WHERE user_id = ?", (user_id,))
        new_aim = cursor.fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    return {"success": True, "new_aim": new_aim}

@app.post("/activate_promo")
async def activate_promo(code: str = Form(...), user_id: int = Form(...)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT reward, max_uses, used_count, owner_id FROM promos WHERE code = ?", (code.upper(),))
        promo = cursor.fetchone()
        if not promo:
            return {"success": False, "msg": "Promokod topilmadi!"}
        
        reward, max_uses, used_count, owner_id = promo
        if used_count >= max_uses:
            return {"success": False, "msg": "Promokod muddati tugagan!"}

        reward_aim = (reward / 60) * 100
        cursor.execute("UPDATE promos SET used_count = used_count + 1 WHERE code = ?", (code.upper(),))
        cursor.execute("UPDATE users SET aimcoin = aimcoin + ? WHERE user_id = ?", (reward_aim, user_id))
        
        # Hamkor uchun 20% bonus hisoboti
        if owner_id and owner_id != user_id:
            partner_bonus = reward * 0.20
            cursor.execute("UPDATE users SET partner_earned = partner_earned + ? WHERE user_id = ?", (partner_bonus, owner_id))
            
        conn.commit()
    finally:
        conn.close()
    return {"success": True, "reward_aim": reward_aim, "msg": f"+{reward} UC berildi!"}

@app.get("/partner_stats/{user_id}")
async def partner_stats(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT partner_earned FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    earned = res["partner_earned"] if res else 0.0
    return {"earned": earned}

@app.post("/request_demo")
async def request_demo(user_id: int = Form(...), amount: float = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO demo_requests (user_id, amount) VALUES (?, ?)", (user_id, amount))
    req_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Admin botga xabar yuborish
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_demo_{req_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_demo_{req_id}")
        ]
    ])
    try:
        await bot.send_message(
            SUPER_ADMIN_ID,
            f"🎬 **Yangi Demo Balans So'rovi!**\n\n"
            f"👤 Foydalanuvchi ID: `{user_id}`\n"
            f"💰 So'ralayotgan summa: {amount} UC\n"
            f"🆔 So'rov raqami: #{req_id}",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    except Exception:
        pass

    return {"success": True, "msg": "Demo balans so'rovi adminga yuborildi! Tez orada ko'rib chiqiladi."}

@app.post("/open/{case_id}")
async def open_case(case_id: str):
    case = CASES[case_id]
    items = case["items"]
    chances = [item["chance"] for item in items]
    win_item = random.choices(items, weights=chances, k=1)[0]
    random_items = [random.choice(items) for _ in range(10)]
    return {"win_item": win_item, "random_items": random_items}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=10000)
