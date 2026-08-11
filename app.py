from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import random
import sqlite3

app = FastAPI()

# Bazani ulash va sozlash
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 500,
            is_partner INTEGER DEFAULT 0,
            demo_balance INTEGER DEFAULT 1000
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promos (
            code TEXT PRIMARY KEY,
            reward INTEGER,
            is_partner_code INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

CASES = {
    "starter": {
        "name": "Starter Case",
        "price": 10,
        "items": [
            {"name": "Common M416", "chance": 60, "val": 5},
            {"name": "Rare SCAR-L", "chance": 30, "val": 20},
            {"name": "Epic AKM", "chance": 9, "val": 50},
            {"name": "Legendary Frost M4", "chance": 1, "val": 150}
        ]
    },
    "pro": {
        "name": "Pro Case",
        "price": 30,
        "items": [
            {"name": "Rare UMP45", "chance": 50, "val": 15},
            {"name": "Epic Groza", "chance": 35, "val": 60},
            {"name": "Legendary M24", "chance": 13, "val": 200},
            {"name": "Mythic Glacier M4", "chance": 2, "val": 500}
        ]
    }
}

@app.get("/", response_class=HTMLResponse)
async def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AimDrop & Bulldrop Pro - Partner Edition</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            body { background: #0b0f19; color: #fff; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 20px; }
            header { width: 100%; max-width: 1000px; display: flex; justify-content: space-between; align-items: center; background: #131b2e; padding: 15px 25px; border-radius: 12px; border: 1px solid #1f2b45; margin-bottom: 25px; }
            .logo { font-size: 20px; font-weight: bold; color: #00ffcc; }
            .nav-menu { display: flex; gap: 10px; flex-wrap: wrap; }
            .nav-btn { background: #1f2b45; color: #fff; border: none; padding: 8px 14px; border-radius: 8px; cursor: pointer; font-weight: bold; transition: 0.2s; }
            .nav-btn:hover, .nav-btn.active { background: #00ffcc; color: #0b0f19; }
            .balance-box { background: #ffcc00; color: #000; padding: 8px 16px; border-radius: 20px; font-weight: bold; }
            
            .tab-content { display: none; width: 100%; max-width: 1000px; text-align: center; }
            .tab-content.active { display: block; }

            .grid { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-top: 20px; }
            .case-card { background: #131b2e; border: 2px solid #1f2b45; padding: 25px; border-radius: 15px; width: 280px; text-align: center; }
            .btn-open { background: #00ffcc; color: #0b0f19; border: none; padding: 12px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 15px; }
            
            .panel { background: #131b2e; border: 1px solid #1f2b45; padding: 30px; border-radius: 15px; max-width: 500px; margin: 0 auto; text-align: left; }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; margin-bottom: 5px; color: #aaa; }
            .form-group input { width: 100%; padding: 12px; background: #0b0f19; border: 1px solid #1f2b45; color: #fff; border-radius: 8px; }
            .btn-submit { background: #ffcc00; color: #0b0f19; border: none; padding: 12px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 10px; }
            .card-number { background: #0b0f19; padding: 10px; border-radius: 6px; font-family: monospace; color: #ffcc00; font-size: 18px; text-align: center; border: 1px dashed #ffcc00; }
        </style>
    </head>
    <body>

        <header>
            <div class="logo">🔥 AIMDROP PARTNER</div>
            <div class="nav-menu">
                <button class="nav-btn active" onclick="switchTab('cases', this)">Keyslar</button>
                <button class="nav-btn" onclick="switchTab('partner', this)" style="background:#ff4df2; color:#fff;">Hamkor Kabineti</button>
                <button class="nav-btn" onclick="switchTab('promo', this)">Promo Kod</button>
                <button class="nav-btn" onclick="switchTab('wallet', this)" style="background:#ffcc00; color:#000;">Hisobni To'ldirish</button>
            </div>
            <div class="balance-box">Balans: <span id="balance">500</span> UC</div>
        </header>

        <!-- CASES -->
        <div id="cases-tab" class="tab-content active">
            <h1>OMADLI KEYSLAR</h1>
            <div class="grid">
                <div class="case-card">
                    <h3>Starter Case</h3>
                    <p>Narxi: 10 UC</p>
                    <button class="btn-open" onclick="openCase('starter', 10)">OCHISH</button>
                </div>
                <div class="case-card">
                    <h3>Pro Case</h3>
                    <p>Narxi: 30 UC</p>
                    <button class="btn-open" onclick="openCase('pro', 30)">OCHISH</button>
                </div>
            </div>
            <div id="result-modal" style="margin-top:20px; font-size:20px; color:#00ffcc;"></div>
        </div>

        <!-- PARTNER CABINET -->
        <div id="partner-tab" class="tab-content">
            <div class="panel" style="text-align: center;">
                <h2>🤝 HAMKOR KABINETI</h2>
                <p style="color: #aaa; margin-bottom: 15px;">Hamkorlar uchun maxsus test sinovlari uchun demo balans:</p>
                <h3 style="color: #ff4df2; font-size: 28px; margin-bottom: 20px;"><span id="demo-balance">1000</span> Demo UC</h3>
                <p style="font-size: 14px; color: #00ffcc;">Hamkor promokodlari orqali foydalanuvchilarga avtomatik 20% bonus taqdim etiladi!</p>
            </div>
        </div>

        <!-- PROMO -->
        <div id="promo-tab" class="tab-content">
            <div class="panel">
                <h2>PROMO KOD</h2>
                <div class="form-group">
                    <label>Promokodni kiriting (Hamkor kodlari 20% bonus beradi):</label>
                    <input type="text" id="promo-code" placeholder="Masalan: PARTNER20">
                </div>
                <button class="btn-submit" onclick="activatePromo()">TASDIQLASH</button>
                <p id="promo-msg" style="margin-top: 15px; text-align: center;"></p>
            </div>
        </div>

        <!-- WALLET -->
        <div id="wallet-tab" class="tab-content">
            <div class="panel">
                <h2>HISOBNI TO'LDIRISH</h2>
                <div class="form-group">
                    <label>Karta raqami:</label>
                    <div class="card-number">5614 6865 0763 1458</div>
                </div>
                <div class="form-group">
                    <label>Summa:</label>
                    <input type="number" id="pay-amount" placeholder="Summani kiriting">
                </div>
                <button class="btn-submit" onclick="alert('So\'rov yuborildi!')">TO'LDIRISH</button>
            </div>
        </div>

        <script>
            let userBalance = 500;
            let demoBalance = 1000;

            function switchTab(tabName, btn) {
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
                document.getElementById(tabName + '-tab').classList.add('active');
                btn.classList.add('active');
            }

            async function openCase(caseId, price) {
                if (userBalance < price) { alert("Balans yetarli emas!"); return; }
                const response = await fetch(`/open/${caseId}`, { method: 'POST' });
                const resData = await response.json();
                if(resData.item) {
                    userBalance = userBalance - price + resData.price;
                    document.getElementById('balance').innerText = userBalance;
                    document.getElementById('result-modal').innerText = `🎉 Yutdingiz: ${resData.item} (${resData.price} UC)`;
                }
            }

            function activatePromo() {
                let code = document.getElementById('promo-code').value.trim();
                let msg = document.getElementById('promo-msg');
                if (code.toUpperCase().includes("PARTNER") || code.toUpperCase() === "20%") {
                    let bonus = 120; // 20% qo'shilgan holat
                    userBalance += bonus;
                    document.getElementById('balance').innerText = userBalance;
                    msg.style.color = "#ff4df2";
                    msg.innerText = "🎉 Hamkor promokodi tasdiqlandi! +20% bonus qo'shildi.";
                } else {
                    msg.style.color = "#ff4d4d";
                    msg.innerText = "❌ Noto'g'ri promokod!";
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/open/{case_id}")
async def open_case(case_id: str):
    case = CASES.get(case_id)
    items = case["items"]
    result = random.choices(items, weights=[i['chance'] for i in items], k=1)[0]
    return {"item": result["name"], "price": result["val"]}
