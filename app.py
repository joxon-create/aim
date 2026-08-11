import random
import sqlite3
import re
import threading
import asyncio
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

app = FastAPI()

ADMIN_CARD = "5614686507631458"
CARD_HOLDER = "AZIZA BOYTEMIROVA"

BOT_TOKEN = "8882251329:AAFNqlxx7bYPVs2bMdfYB80Qol1PWzEUk-Y"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            aimcoin REAL DEFAULT 100.0,
            total_donated REAL DEFAULT 0.0,
            pubg_id TEXT,
            is_partner INTEGER DEFAULT 0,
            partner_code TEXT,
            partner_earned REAL DEFAULT 0.0
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
        CREATE TABLE IF NOT EXISTS promos (
            code TEXT PRIMARY KEY,
            reward REAL,
            max_uses INTEGER DEFAULT 10,
            used_count INTEGER DEFAULT 0,
            is_partner INTEGER DEFAULT 0
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, aimcoin) VALUES (1, 'default_user', 100.0)")
    conn.commit()
    conn.close()

init_db()

@dp.message(F.text)
async def catch_card_sms(message: types.Message):
    text = message.text or ""
    if "UZS" in text or "so'm" in text:
        clean_text = text.replace(',', '').replace(' ', '')
        numbers = re.findall(r'\d+', clean_text)
        if numbers:
            sum_amount = float(numbers[0])
            uc_amount = (sum_amount / 14000) * 60
            aim_add = (uc_amount / 60) * 100
            
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET aimcoin = aimcoin + ?, total_donated = total_donated + ? WHERE user_id = 1", (aim_add, uc_amount))
            conn.commit()
            conn.close()
            
            await message.reply(f"✅ To'lov qabul qilindi!\nSumma: {sum_amount} so'm\nHisobga qo'shildi: {uc_amount:.1f} UC")

def run_telegram_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(dp.start_polling(bot))

@app.on_event("startup")
def startup_event():
    t = threading.Thread(target=run_telegram_bot, daemon=True)
    t.start()

PUBG_ITEMS_POOL = [
    {"name": "M416 'Lednik'", "val": 18000, "img": "❄️", "chance": 0.000001},
    {"name": "M416 'Glacier'", "val": 2800, "img": "🧊", "chance": 0.00005},
    {"name": "AWM 'The Fool'", "val": 2500, "img": "🤡", "chance": 0.0001},
    {"name": "Groza 'Jungle'", "val": 1800, "img": "🐍", "chance": 0.0005},
    {"name": "PP-19 Bizon", "val": 1200, "img": "🔫", "chance": 0.001},
    {"name": "Vector 'Blood'", "val": 900, "img": "🩸", "chance": 0.005},
    {"name": "Kar98k 'Sting'", "val": 750, "img": "🎯", "chance": 0.01},
    {"name": "UMP45 'EMP'", "val": 600, "img": "⚡", "chance": 0.05},
    {"name": "SCAR-L 'Toreador'", "val": 500, "img": "🔥", "chance": 0.1},
    {"name": "Pan 'BFC'", "val": 450, "img": "🍳", "chance": 0.2},
    {"name": "Helmet Lv.3", "val": 350, "img": "🪖", "chance": 0.5},
    {"name": "Backpack Lv.3", "val": 300, "img": "🎒", "chance": 0.8},
    {"name": "M16A4 'Neon'", "val": 250, "img": "🔋", "chance": 1.0},
    {"name": "Mini14 'Silver'", "val": 220, "img": "🛡️", "chance": 1.5},
    {"name": "SKS 'Metal'", "val": 200, "img": "⚙️", "chance": 2.0},
    {"name": "Thompson 'Classic'", "val": 180, "img": "📻", "chance": 2.5},
    {"name": "P92 'Gold'", "val": 150, "img": "🟡", "chance": 3.0},
    {"name": "Parachute 'Phoenix'", "val": 130, "img": "🪂", "chance": 4.0},
    {"name": "Grenade 'Finish'", "val": 110, "img": "💣", "chance": 5.0},
    {"name": "Smoke 'Red'", "val": 90, "img": "🌫️", "chance": 6.0},
    {"name": "Energy Drink", "val": 75, "img": "🥤", "chance": 8.0},
    {"name": "Painkiller", "val": 60, "img": "💊", "chance": 10.0},
    {"name": "First Aid", "val": 50, "img": "🩹", "chance": 12.0},
    {"name": "Cloth Mask", "val": 40, "img": "😷", "chance": 14.0},
    {"name": "Combat Pants", "val": 30, "img": "👖", "chance": 16.0},
    {"name": "Sneakers", "val": 25, "img": "👟", "chance": 18.0},
    {"name": "Glasses", "val": 20, "img": "🕶️", "chance": 20.0},
    {"name": "Cap 'PUBG'", "val": 15, "img": "🧢", "chance": 22.0},
    {"name": "T-Shirt", "val": 10, "img": "👕", "chance": 25.0},
    {"name": "Silver Fragment", "val": 5, "img": "🪙", "chance": 30.0},
]

CASES = {}
case_names = [
    "Soldier Crate", "Premium Crate", "Classic Crate", "Custom Crate", "Royal Pass Box",
    "Mythic Forge", "Cyber Punk", "Desert Storm", "Neon City", "Arctic Wolf",
    "Golden Dragon", "Shadow Ninja", "Titanium Box", "Blood Moon", "Pharaoh Vault",
    "Ocean Treasure", "Galaxy Drop", "Inferno Case", "Thunder Strike", "Rosovy Oazis"
]

for i, name in enumerate(case_names):
    price = 10 if i == 0 else (300 if i == 19 else round(10 + (290 / 18) * i, 1))
    items = []
    for item in PUBG_ITEMS_POOL:
        copied = item.copy()
        if i == 19 and copied["name"] == "M416 'Lednik'":
            copied["val"] = price * 30
        else:
            copied["val"] = round(price * random.uniform(0.2, 2.0), 1)
        items.append(copied)
    while len(items) < 30:
        items.append(random.choice(PUBG_ITEMS_POOL))
    CASES[f"case_{i+1}"] = {"name": name, "price": price, "items": items}

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BullDrop - PUBG UC</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: #0b0f19; color: #fff; min-height: 100vh; display: flex; flex-direction: column; }}
            header {{ display: flex; justify-content: space-between; align-items: center; background: #131b2e; padding: 12px 20px; border-bottom: 1px solid #1f2b45; }}
            .logo {{ font-size: 22px; font-weight: bold; color: #ff3366; }}
            .header-right {{ display: flex; align-items: center; gap: 10px; }}
            .lang-select {{ background: #1a233a; color: #fff; border: 1px solid #2a3a5a; padding: 5px 10px; border-radius: 12px; cursor: pointer; font-size: 13px; }}
            .balance-container {{ background: #1a233a; border: 1px solid #2a3a5a; padding: 6px 14px; border-radius: 20px; font-weight: bold; color: #ffcc00; font-size: 14px; }}
            .container {{ max-width: 1200px; margin: 0 auto; width: 100%; padding: 20px; flex: 1; padding-bottom: 90px; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .cases-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; }}
            .case-card {{ background: #131b2e; border: 1px solid #1f2b45; border-radius: 14px; padding: 15px; text-align: center; cursor: pointer; transition: 0.2s; }}
            .case-card:hover {{ border-color: #ff3366; transform: translateY(-3px); }}
            .case-img {{ font-size: 40px; margin: 10px 0; }}
            .btn-open {{ background: #ff3366; color: #fff; border: none; padding: 8px; width: 100%; border-radius: 8px; font-weight: bold; margin-top: 10px; cursor: pointer; }}
            
            .roulette-container {{ background: #131b2e; border: 1px solid #1f2b45; border-radius: 14px; padding: 20px; text-align: center; max-width: 650px; margin: 20px auto; }}
            .roulette-track-window {{ width: 100%; overflow: hidden; position: relative; height: 130px; background: #0b0f19; border-radius: 10px; border: 1px solid #2a3a5a; margin-bottom: 20px; }}
            .roulette-pointer {{ position: absolute; top: 0; bottom: 0; left: 50%; width: 3px; background: #ff3366; transform: translateX(-50%); z-index: 10; }}
            .roulette-track {{ display: flex; position: absolute; left: 0; top: 8px; transition: transform 4s cubic-bezier(0.08, 0.82, 0.17, 1); }}
            .roulette-item {{ min-width: 110px; height: 110px; background: #1a233a; border: 1px solid #2a3a5a; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0 6px; font-weight: bold; }}

            .panel {{ background: #131b2e; border: 1px solid #1f2b45; padding: 25px; border-radius: 14px; max-width: 450px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 15px; }}
            .form-group label {{ display: block; margin-bottom: 6px; color: #8b9bb4; font-size: 13px; }}
            .form-group input {{ width: 100%; padding: 11px; background: #0b0f19; border: 1px solid #1f2b45; color: #fff; border-radius: 8px; font-size: 14px; }}
            .btn-submit {{ background: #ff3366; color: #fff; border: none; padding: 11px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; }}

            .bottom-nav {{ position: fixed; bottom: 0; left: 0; width: 100%; background: #131b2e; border-top: 1px solid #1f2b45; display: flex; justify-content: space-around; padding: 10px 0; z-index: 100; }}
            .nav-item {{ background: transparent; border: none; color: #8b9bb4; cursor: pointer; font-size: 12px; display: flex; flex-direction: column; align-items: center; gap: 3px; font-weight: 600; }}
            .nav-item.active {{ color: #ff3366; }}
            .nav-item span.icon {{ font-size: 20px; }}
        </style>
    </head>
    <body>
        <header>
            <div class="logo">⚡ BULLDROP</div>
            <div class="header-right">
                <select class="lang-select" id="lang-switcher" onchange="changeLanguage(this.value)">
                    <option value="uz">UZ</option>
                    <option value="ru">RU</option>
                </select>
                <div class="balance-container">
                    <span id="balance">100.00</span> Aim (<span id="uc-balance">60</span> UC)
                </div>
            </div>
        </header>

        <div class="container">
            <div id="cases-tab" class="tab-content active">
                <h3 style="margin-bottom: 15px;" id="t-cases-title">PUBG Кейслар</h3>
                <div class="cases-grid" id="cases-grid"></div>
            </div>

            <div id="roulette-tab" class="tab-content">
                <div class="roulette-container">
                    <h3 style="margin-bottom: 15px;" id="case-title-run">Keys ochilmoqda...</h3>
                    <div class="roulette-track-window">
                        <div class="roulette-pointer"></div>
                        <div class="roulette-track" id="track"></div>
                    </div>
                    <div id="win-result" style="font-size: 18px; font-weight: bold; color: #00ffcc; margin-bottom: 15px; min-height: 25px;"></div>
                    <button class="btn-submit" onclick="switchTab('cases', document.querySelectorAll('.bottom-nav button')[0])" id="back-btn" style="display:none; max-width: 180px; margin: 0 auto;">Keylarga qaytish</button>
                </div>
            </div>

            <div id="wallet-tab" class="tab-content">
                <div class="panel">
                    <h3 style="margin-bottom: 15px;" id="t-wallet-title">Balansni to'ldirish (60 UC = 14,000 so'm)</h3>
                    <div class="form-group">
                        <label id="t-uc-label">UC miqdori (Minimal 60 UC):</label>
                        <input type="number" id="uc-topup" value="60" oninput="calcSum()">
                    </div>
                    <p style="color: #ffcc00; margin-bottom: 15px; font-size: 14px;"><span id="t-sum-text">To'lov summasi:</span> <span id="sum-calc">14000</span> so'm</p>
                    <div style="background: #0b0f19; padding: 12px; border-radius: 8px; border: 1px solid #2a3a5a; margin-bottom: 15px; font-size: 13px;">
                        <p style="color: #8b9bb4; margin-bottom: 5px;">Uzcard raqamiga o'tkazing:</p>
                        <p style="color: #00ffcc; font-weight: bold; font-size: 15px;">{ADMIN_CARD}</p>
                        <p style="color: #8b9bb4; font-size: 11px; margin-top: 3px;">Egasi: {CARD_HOLDER}</p>
                    </div>
                    <button class="btn-submit" onclick="createPayment()" id="t-pay-btn">To'lov qildim</button>
                    <p id="wallet-msg" style="margin-top: 12px; font-size: 13px; text-align: center;"></p>
                </div>
            </div>

            <div id="promo-tab" class="tab-content">
                <div class="panel">
                    <h3 style="margin-bottom: 15px;" id="t-promo-title">Promokod aktivatsiya</h3>
                    <div class="form-group">
                        <input type="text" id="promo-code-input" placeholder="Promokodni kiriting...">
                    </div>
                    <button class="btn-submit" onclick="activatePromo()" id="t-promo-btn">Faollashtirish</button>
                    <p id="promo-msg" style="margin-top: 12px; font-size: 13px; text-align: center;"></p>
                </div>
            </div>

            <div id="withdraw-tab" class="tab-content">
                <div class="panel">
                    <h3 style="margin-bottom: 15px;" id="t-withdraw-title">UC Yechib olish (Chiqarib olish)</h3>
                    <p style="color: #ff3366; font-size: 12px; margin-bottom: 12px;" id="t-withdraw-rule">⚠️ Eslatma: Chiqarish uchun eng kami saytda 60 UC donate qilgan bo'lishi shart!</p>
                    <div class="form-group">
                        <label id="t-pubg-label">Aniq PUBG ID yozing:</label>
                        <input type="text" id="pubg-id-input" placeholder="Masalan: 5123456789">
                    </div>
                    <div class="form-group">
                        <label id="t-withdraw-amt-label">Yechib olinadigan UC:</label>
                        <input type="number" id="uc-withdraw-amount" value="60">
                    </div>
                    <button class="btn-submit" onclick="requestUCWithdraw()" id="t-withdraw-btn">UC Yechish so'rovi</button>
                    <p id="withdraw-msg" style="margin-top: 12px; font-size: 13px; text-align: center;"></p>
                </div>
            </div>
        </div>

        <nav class="bottom-nav">
            <button class="nav-item active" onclick="switchTab('cases', this)"><span class="icon">📦</span> <span id="nav-cases">Кейсы</span></button>
            <button class="nav-item" onclick="switchTab('wallet', this)"><span class="icon">💳</span> <span id="nav-wallet">To'ldirish</span></button>
            <button class="nav-item" onclick="switchTab('promo', this)"><span class="icon">🎁</span> <span id="nav-promo">Promo</span></button>
            <button class="nav-item" onclick="switchTab('withdraw', this)"><span class="icon">💸</span> <span id="nav-withdraw">Chiqarish</span></button>
        </nav>

        <script>
            let balanceAim = 100.0;
            let currentLang = 'uz';

            const translations = {{
                uz: {{
                    casesTitle: "PUBG Кейслар (20 ta)",
                    openBtn: "Ochish",
                    walletTitle: "Balansni to'ldirish (60 UC = 14,000 so'm)",
                    ucLabel: "UC miqdori (Minimal 60 UC):",
                    sumText: "To'lov summasi:",
                    payBtn: "To'lov qildim (Webhook)",
                    promoTitle: "Promokod aktivatsiya",
                    promoPlaceholder: "Promokodni kiriting...",
                    promoBtn: "Faollashtirish",
                    withdrawTitle: "UC Yechib olish (Chiqarish)",
                    withdrawRule: "⚠️ Eslatma: Chiqarish uchun eng kami saytda 60 UC donate qilgan bo'lishi shart!",
                    pubgLabel: "Aniq PUBG ID yozing:",
                    withdrawAmtLabel: "Yechib olinadigan UC:",
                    withdrawBtn: "UC Yechish so'rovi",
                    navCases: "Кейслар",
                    navWallet: "To'ldirish",
                    navPromo: "Promo",
                    navWithdraw: "Chiqarish"
                }},
                ru: {{
                    casesTitle: "Кейсы PUBG (20 шт)",
                    openBtn: "Открыть",
                    walletTitle: "Пополнить баланс (60 UC = 14,000 сум)",
                    ucLabel: "Количество UC (Мин. 60 UC):",
                    sumText: "Сумма к оплате:",
                    payBtn: "Я оплатил (Webhook)",
                    promoTitle: "Активация промокода",
                    promoPlaceholder: "Введите промокод...",
                    promoBtn: "Активировать",
                    withdrawTitle: "Вывод UC",
                    withdrawRule: "⚠️ Внимание: Для вывода необходимо пополнить баланс минимум на 60 UC!",
                    pubgLabel: "Введите ваш PUBG ID:",
                    withdrawAmtLabel: "Количество UC для вывода:",
                    withdrawBtn: "Запросить вывод UC",
                    navCases: "Кейсы",
                    navWallet: "Пополнить",
                    navPromo: "Промо",
                    navWithdraw: "Вывод"
                }}
            }};

            function changeLanguage(lang) {{
                currentLang = lang;
                let t = translations[lang];
                document.getElementById('t-cases-title').innerText = t.casesTitle;
                document.getElementById('t-wallet-title').innerText = t.walletTitle;
                document.getElementById('t-uc-label').innerText = t.ucLabel;
                document.getElementById('t-sum-text').innerText = t.sumText;
                document.getElementById('t-pay-btn').innerText = t.payBtn;
                document.getElementById('t-promo-title').innerText = t.promoTitle;
                document.getElementById('promo-code-input').placeholder = t.promoPlaceholder;
                document.getElementById('t-promo-btn').innerText = t.promoBtn;
                document.getElementById('t-withdraw-title').innerText = t.withdrawTitle;
                document.getElementById('t-withdraw-rule').innerText = t.withdrawRule;
                document.getElementById('t-pubg-label').innerText = t.pubgLabel;
                document.getElementById('t-withdraw-amt-label').innerText = t.withdrawAmtLabel;
                document.getElementById('t-withdraw-btn').innerText = t.withdrawBtn;
                document.getElementById('nav-cases').innerText = t.navCases;
                document.getElementById('nav-wallet').innerText = t.navWallet;
                document.getElementById('nav-promo').innerText = t.navPromo;
                document.getElementById('nav-withdraw').innerText = t.navWithdraw;
                loadCases();
            }}

            function updateUI() {{
                document.getElementById('balance').innerText = balanceAim.toFixed(2);
                document.getElementById('uc-balance').innerText = Math.floor((balanceAim / 100) * 60);
            }}

            function switchTab(tabName, btn) {{
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                document.getElementById(tabName + '-tab').classList.add('active');
                if(btn) btn.classList.add('active');
            }}

            function calcSum() {{
                let uc = parseFloat(document.getElementById('uc-topup').value) || 0;
                let sum = (uc / 60) * 14000;
                document.getElementById('sum-calc').innerText = Math.round(sum);
            }}

            async function loadCases() {{
                let res = await fetch('/get_cases');
                let cases = await res.json();
                let html = '';
                let t = translations[currentLang];
                for(let id in cases) {{
                    let c = cases[id];
                    let aimPrice = (c.price / 60) * 100;
                    html += `
                        <div class="case-card" onclick="startRoulette('${{id}}', ${{aimPrice}}, '${{c.name}}')">
                            <div class="case-img">📦</div>
                            <h4 style="font-size: 13px;">${{c.name}}</h4>
                            <p style="color:#ffcc00; margin: 8px 0; font-weight: bold;">${{c.price}} UC</p>
                            <button class="btn-open">${{t.openBtn}}</button>
                        </div>
                    `;
                }}
                document.getElementById('cases-grid').innerHTML = html;
            }}
            loadCases();

            async function createPayment() {{
                let uc = parseFloat(document.getElementById('uc-topup').value) || 0;
                if(uc < 60) {{ alert("Minimal to'ldirish 60 UC!"); return; }}
                let res = await fetch('/topup_webhook', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                    body: `uc=${{uc}}&user_id=1`
                }});
                let data = await res.json();
                if(data.success) {{
                    balanceAim = data.new_aim;
                    updateUI();
                    document.getElementById('wallet-msg').style.color = "#00ffcc";
                    document.getElementById('wallet-msg').innerText = "✅ " + data.msg;
                }}
            }}

            async function activatePromo() {{
                let code = document.getElementById('promo-code-input').value.trim();
                let msg = document.getElementById('promo-msg');
                let res = await fetch('/activate_promo', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                    body: `code=${{code}}&user_id=1`
                }});
                let data = await res.json();
                if(data.success) {{
                    balanceAim += data.reward_aim;
                    updateUI();
                    msg.style.color = "#00ffcc";
                    msg.innerText = "✅ " + data.msg;
                }} else {{
                    msg.style.color = "#ff3366";
                    msg.innerText = "❌ " + data.msg;
                }}
            }}

            async function requestUCWithdraw() {{
                let pubgId = document.getElementById('pubg-id-input').value.trim();
                let ucAmt = parseFloat(document.getElementById('uc-withdraw-amount').value) || 0;
                let msg = document.getElementById('withdraw-msg');

                let res = await fetch('/withdraw_uc', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                    body: `pubg_id=${{pubgId}}&uc=${{ucAmt}}&user_id=1`
                }});
                let data = await res.json();
                if(data.success) {{
                    msg.style.color = "#00ffcc";
                    msg.innerText = "✅ " + data.msg;
                }} else {{
                    msg.style.color = "#ff3366";
                    msg.innerText = "❌ " + data.msg;
                }}
            }}

            async function startRoulette(caseId, priceAim, caseName) {{
                if(balanceAim < priceAim) {{ alert("AimCoin yetarli emas!"); return; }}
                balanceAim -= priceAim;
                updateUI();

                switchTab('roulette', null);
                document.getElementById('case-title-run').innerText = caseName + " ochilmoqda...";
                document.getElementById('win-result').innerText = "";
                document.getElementById('back-btn').style.display = "none";

                let res = await fetch('/open/' + caseId, {{method: 'POST'}});
                let data = await res.json();

                let track = document.getElementById('track');
                track.style.transition = 'none';
                track.style.transform = 'translateX(0px)';

                let itemsHtml = '';
                let winningIndex = 35;
                for(let i = 0; i < 50; i++) {{
                    let item = (i === winningIndex) ? data.win_item : data.random_items[i % data.random_items.length];
                    itemsHtml += `<div class="roulette-item"><span>${{item.img}}</span><span style="font-size:11px; margin-top:4px;">${{item.val}} UC</span></div>`;
                }}
                track.innerHTML = itemsHtml;

                setTimeout(() => {{
                    track.style.transition = 'transform 4s cubic-bezier(0.08, 0.82, 0.17, 1)';
                    let targetOffset = (winningIndex * 122) - 250;
                    track.style.transform = `translateX(-${{targetOffset}px)`;
                }, 50);

                setTimeout(() => {{
                    let wonAim = (data.win_item.val / 60) * 100;
                    balanceAim += wonAim;
                    updateUI();
                    document.getElementById('win-result').innerHTML = `🎉 Yutib oldingiz: ${{data.win_item.name}} (${{data.win_item.val}} UC)`;
                    document.getElementById('back-btn').style.display = "block";
                }, 4100);
            }}
        </script>
    </body>
    </html>
    """)

@app.get("/get_cases")
async def get_cases():
    return CASES

@app.post("/topup_webhook")
async def topup_webhook(uc: float = Form(...), user_id: int = Form(1)):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    aim_add = (uc / 60) * 100
    cursor.execute("UPDATE users SET aimcoin = aimcoin + ?, total_donated = total_donated + ? WHERE user_id = ?", (aim_add, uc, user_id))
    cursor.execute("SELECT aimcoin FROM users WHERE user_id = ?", (user_id,))
    new_aim = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return {"success": True, "new_aim": new_aim, "msg": f"To'lov tasdiqlandi! +{uc} UC qo'shildi."}

@app.post("/activate_promo")
async def activate_promo(code: str = Form(...), user_id: int = Form(1)):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT reward, max_uses, used_count FROM promos WHERE code = ?", (code.upper(),))
    promo = cursor.fetchone()

    if not promo:
        conn.close()
        return {"success": False, "msg": "Promokod topilmadi!"}

    reward, max_uses, used_count = promo
    if used_count >= max_uses:
        conn.close()
        return {"success": False, "msg": "Promokod muddati tugagan!"}

    reward_aim = (reward / 60) * 100
    cursor.execute("UPDATE promos SET used_count = used_count + 1 WHERE code = ?", (code.upper(),))
    cursor.execute("UPDATE users SET aimcoin = aimcoin + ? WHERE user_id = ?", (reward_aim, user_id))
    conn.commit()
    conn.close()
    return {"success": True, "reward_aim": reward_aim, "msg": f"+{reward} UC berildi!"}

@app.post("/withdraw_uc")
async def withdraw_uc(pubg_id: str = Form(...), uc: float = Form(...), user_id: int = Form(1)):
    if not pubg_id:
        return {"success": False, "msg": "PUBG ID kiriting!"}
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT total_donated, aimcoin FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return {"success": False, "msg": "Foydalanuvchi topilmadi!"}
    
    total_donated, aimcoin = user
    
    # Minimal 60 UC donate qilgan bo'lishi shart tekshiruvi
    if total_donated < 60:
        conn.close()
        return {"success": False, "msg": "Chiqarish uchun eng kami saytda 60 UC donate qilgan bo'lishi shart!"}
    
    aim_required = (uc / 60) * 100
    if aimcoin < aim_required:
        conn.close()
        return {"success": False, "msg": "Hisobda yetarli AimCoin yo'q!"}

    cursor.execute("UPDATE users SET aimcoin = aimcoin - ? WHERE user_id = ?", (aim_required, user_id))
    cursor.execute("INSERT INTO uc_requests (user_id, pubg_id, uc_amount) VALUES (?, ?, ?)", (user_id, pubg_id, uc))
    conn.commit()
    conn.close()
    return {"success": True, "msg": "UC yechish so'rovi adminga yuborildi!"}

@app.post("/open/{case_id}")
async def open_case(case_id: str):
    case = CASES[case_id]
    items = case["items"]
    chances = [item["chance"] for item in items]
    win_item = random.choices(items, weights=chances, k=1)[0]
    random_items = [random.choice(items) for _ in range(10)]
    return {"win_item": win_item, "random_items": random_items}
