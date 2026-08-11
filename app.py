from fastapi import FastAPI, Request, Form  # <--- Form shu yerga qo'shildi
from fastapi.responses import HTMLResponse
import random
import sqlite3

app = FastAPI()
# Qolgan kodlar o'z holicha qoladi...

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            balance REAL DEFAULT 11.31,
            is_partner INTEGER DEFAULT 0,
            partner_code TEXT,
            partner_earned REAL DEFAULT 0.0
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
    cursor.execute("INSERT OR IGNORE INTO promos (code, reward, is_partner, max_uses) VALUES ('RAVOX', 20.0, 1, 999999)")
    cursor.execute("INSERT OR IGNORE INTO promos (code, reward, is_partner, max_uses) VALUES ('ULUOFD', 15.0, 0, 5)")
    conn.commit()
    conn.close()

init_db()

CASES = {
    "oasis": {
        "name": "Розовый оазис", 
        "price": 24.03, 
        "items": [
            {"name": "Kukri Ares", "val": 148.8, "img": "🔪"},
            {"name": "AWM BOOM", "val": 781.9, "img": "🎯"},
            {"name": "AKR Dragon", "val": 45.0, "img": "🔫"},
            {"name": "USP Ghosts", "val": 12.5, "img": "🔫"},
            {"name": "M4 Catalyst", "val": 19.5, "img": "⚔️"}
        ]
    }
}

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bulldrop - Official Site</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
            body { background: #0b0f19; color: #fff; min-height: 100vh; display: flex; flex-direction: column; }
            
            /* Header */
            header { display: flex; justify-content: space-between; align-items: center; background: #131b2e; padding: 15px 30px; border-bottom: 1px solid #1f2b45; }
            .logo { font-size: 24px; font-weight: bold; color: #ff3366; display: flex; align-items: center; gap: 5px; }
            .nav-menu { display: flex; gap: 20px; }
            .nav-btn { background: transparent; color: #8b9bb4; border: none; cursor: pointer; font-weight: 600; font-size: 15px; transition: 0.2s; }
            .nav-btn:hover, .nav-btn.active { color: #fff; }
            .balance-box { background: #1a233a; border: 1px solid #2a3a5a; padding: 8px 16px; border-radius: 20px; font-weight: bold; color: #ffcc00; display: flex; align-items: center; gap: 8px; }
            .balance-box button { background: #ff3366; color: #fff; border: none; width: 22px; height: 22px; border-radius: 50%; cursor: pointer; font-weight: bold; }

            /* Main Layout */
            .container { max-width: 1200px; margin: 0 auto; width: 100%; padding: 30px 20px; flex: 1; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }

            /* Case Card */
            .cases-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; }
            .case-card { background: #131b2e; border: 1px solid #1f2b45; border-radius: 16px; padding: 25px; text-align: center; cursor: pointer; transition: 0.3s; }
            .case-card:hover { border-color: #ff3366; transform: translateY(-4px); }
            .case-img { font-size: 64px; margin: 15px 0; }
            .btn-open { background: #ff3366; color: #fff; border: none; padding: 12px; width: 100%; border-radius: 10px; font-weight: bold; margin-top: 15px; cursor: pointer; transition: 0.2s; }
            .btn-open:hover { background: #e02855; }

            /* Roulette Animation Window */
            .roulette-container { display: none; background: #131b2e; border: 1px solid #1f2b45; border-radius: 16px; padding: 40px; text-align: center; max-width: 700px; margin: 40px auto; position: relative; }
            .roulette-track-window { width: 100%; overflow: hidden; position: relative; height: 140px; background: #0b0f19; border-radius: 12px; border: 1px solid #2a3a5a; margin-bottom: 25px; }
            .roulette-pointer { position: absolute; top: 0; bottom: 0; left: 50%; width: 4px; background: #ff3366; transform: translateX(-50%); z-index: 10; }
            .roulette-track { display: flex; position: absolute; left: 0; top: 10px; transition: transform 4s cubic-bezier(0.08, 0.82, 0.17, 1); }
            .roulette-item { min-width: 120px; height: 120px; background: #1a233a; border: 1px solid #2a3a5a; border-radius: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0 8px; font-weight: bold; }
            
            /* Panel / Forms */
            .panel { background: #131b2e; border: 1px solid #1f2b45; padding: 30px; border-radius: 16px; max-width: 450px; margin: 0 auto; text-align: center; }
            .form-group { margin-bottom: 15px; text-align: left; }
            .form-group label { display: block; margin-bottom: 8px; color: #8b9bb4; font-size: 14px; }
            .form-group input { width: 100%; padding: 12px; background: #0b0f19; border: 1px solid #1f2b45; color: #fff; border-radius: 10px; font-size: 15px; }
            .btn-submit { background: #ff3366; color: #fff; border: none; padding: 12px; width: 100%; border-radius: 10px; font-weight: bold; cursor: pointer; }
        </style>
    </head>
    <body>

        <header>
            <div class="logo">⚡ BULLDROP</div>
            <div class="nav-menu">
                <button class="nav-btn active" onclick="switchTab('cases', this)">Keyslar</button>
                <button class="nav-btn" onclick="switchTab('promo', this)">Promokod</button>
            </div>
            <div class="balance-box">
                <span id="balance">11.31</span> 🪙
                <button onclick="switchTab('promo', document.querySelectorAll('.nav-btn')[1])">+</button>
            </div>
        </header>

        <div class="container">
            
            <!-- CASES TAB -->
            <div id="cases-tab" class="tab-content active">
                <h2 style="margin-bottom: 20px;">Ommabop Keyslar</h2>
                <div class="cases-grid">
                    <div class="case-card" onclick="startRoulette('oasis', 24.03)">
                        <div class="case-img">🦩</div>
                        <h3>Розовый оазис</h3>
                        <p style="color:#ffcc00; margin: 10px 0; font-weight: bold;">24.03 🪙</p>
                        <button class="btn-open">Ochish</button>
                    </div>
                </div>
            </div>

            <!-- ROULETTE ANIMATION TAB -->
            <div id="roulette-tab" class="tab-content">
                <div class="roulette-container" id="roulette-box" style="display: block;">
                    <h2>Keys Ochilmoqda...</h2>
                    <div class="roulette-track-window">
                        <div class="roulette-pointer"></div>
                        <div class="roulette-track" id="track"></div>
                    </div>
                    <div id="win-result" style="font-size: 20px; font-weight: bold; color: #00ffcc; margin-bottom: 20px; min-height: 30px;"></div>
                    <button class="btn-submit" onclick="backToCases()" id="back-btn" style="display:none;">Orqaga qaytish</button>
                </div>
            </div>

            <!-- PROMO TAB -->
            <div id="promo-tab" class="tab-content">
                <div class="panel">
                    <h2>Aktivatsiya Promokoda</h2>
                    <p style="color: #8b9bb4; font-size: 13px; margin: 10px 0 20px 0;">Promokodni kiriting va sovg'aga ega bo'ling!</p>
                    <div class="form-group">
                        <input type="text" id="promo-input" placeholder="Masalan: RAVOX / ULUOFD">
                    </div>
                    <button class="btn-submit" onclick="activatePromo()">Aktivirovat</button>
                    <p id="promo-msg" style="margin-top: 15px; font-weight: 500;"></p>
                </div>
            </div>

        </div>

        <script>
            let balance = 11.31;

            function switchTab(tabName, btn) {
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
                document.getElementById(tabName + '-tab').classList.add('active');
                if(btn) btn.classList.add('active');
            }

            async function activatePromo() {
                let code = document.getElementById('promo-input').value.trim();
                let msg = document.getElementById('promo-msg');
                let res = await fetch('/activate_promo', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: 'code=' + code + '&user_id=1'
                });
                let data = await res.json();
                if(data.success) {
                    balance += data.reward;
                    document.getElementById('balance').innerText = balance.toFixed(2);
                    msg.style.color = "#00ffcc";
                    msg.innerText = "✅ " + data.msg;
                } else {
                    msg.style.color = "#ff3366";
                    msg.innerText = "❌ " + data.msg;
                }
            }

            async function startRoulette(caseId, price) {
                if(balance < price) { alert("Balans yetarli emas! Hisobni to'ldiring."); return; }
                
                // Balansdan yechish
                balance -= price;
                document.getElementById('balance').innerText = balance.toFixed(2);
                
                switchTab('roulette', null);
                document.getElementById('win-result').innerText = "";
                document.getElementById('back-btn').style.display = "none";

                let res = await fetch('/open/' + caseId, {method: 'POST'});
                let data = await res.json();

                let track = document.getElementById('track');
                track.style.transition = 'none';
                track.style.transform = 'translateX(0px)';
                
                // Ruletka elementlarini generatsiya qilish (soxta elementlar + yutuq o'rtada)
                let itemsHtml = '';
                let winningIndex = 35; // O'rtadagi aniq indeks
                for(let i = 0; i < 50; i++) {
                    let item = (i === winningIndex) ? data.win_item : data.random_items[i % data.random_items.length];
                    itemsHtml += `<div class="roulette-item"><span>${item.img}</span><span style="font-size:12px; margin-top:5px;">${item.val} 🪙</span></div>`;
                }
                track.innerHTML = itemsHtml;

                // Animatsiyani ishga tushirish
                setTimeout(() => {
                    track.style.transition = 'transform 4s cubic-bezier(0.08, 0.82, 0.17, 1)';
                    // Har bir element eni 136px (120px + 16px margins), markazga keltirish uchun offset
                    let targetOffset = (winningIndex * 136) - 250; 
                    track.style.transform = `translateX(-${targetOffset}px)`;
                }, 50);

                // Natijani ko'rsatish
                setTimeout(() => {
                    balance += data.win_item.val;
                    document.getElementById('balance').innerText = balance.toFixed(2);
                    document.getElementById('win-result').innerHTML = `🎉 Tabriklaymiz! Yutdingiz: ${data.win_item.name} (${data.win_item.val} 🪙)`;
                    document.getElementById('back-btn').style.display = "block";
                }, 4100);
            }

            function backToCases() {
                switchTab('cases', document.querySelectorAll('.nav-btn')[0]);
            }
        </script>
    </body>
    </html>
    """)

@app.post("/activate_promo")
async def activate_promo(code: str = Form(...), user_id: int = Form(1)):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT reward, is_partner, max_uses, used_count FROM promos WHERE code = ?", (code.upper(),))
    promo = cursor.fetchone()

    if not promo:
        conn.close()
        return {"success": False, "msg": "Promokod topilmadi!"}

    reward, is_partner, max_uses, used_count = promo

    if not is_partner and used_count >= max_uses:
        conn.close()
        return {"success": False, "msg": "Промокод закончился"}

    if not is_partner:
        cursor.execute("UPDATE promos SET used_count = used_count + 1 WHERE code = ?", (code.upper(),))
    else:
        cursor.execute("UPDATE users SET partner_earned = partner_earned + ? WHERE partner_code = ?", (reward, code.upper()))

    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
    conn.commit()
    conn.close()
    return {"success": True, "reward": reward, "msg": f"Muvaffaqiyatli faollashtirildi! +{reward} 🪙 qo'shildi."}

@app.post("/open/{case_id}")
async def open_case(case_id: str):
    case = CASES[case_id]
    win_item = random.choice(case["items"])
    random_items = [random.choice(case["items"]) for _ in range(10)]
    return {"win_item": win_item, "random_items": random_items}
