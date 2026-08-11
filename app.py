from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import random
import sqlite3

app = FastAPI()

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            balance REAL DEFAULT 0.02,
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
    cursor.execute("INSERT OR IGNORE INTO promos (code, reward, is_partner, max_uses) VALUES ('RAVOX', 0.20, 1, 999999)")
    cursor.execute("INSERT OR IGNORE INTO promos (code, reward, is_partner, max_uses) VALUES ('ULUOFD', 15.0, 0, 5)")
    conn.commit()
    conn.close()

init_db()

CASES = {
    "oasis": {
        "name": "РОЗОВЫЙ ОАЗИС", 
        "price": 32.0, 
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
    return HTMLResponse(content=""""
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bulldrop</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            body { background: #0b0f19; color: #fff; min-height: 100vh; display: flex; flex-direction: column; }
            
            /* Top Header Bar */
            header { display: flex; justify-content: space-between; align-items: center; background: #131b2e; padding: 12px 20px; border-bottom: 1px solid #1f2b45; }
            .logo { font-size: 22px; font-weight: bold; color: #ff3366; display: flex; align-items: center; gap: 5px; }
            .header-right { display: flex; align-items: center; gap: 10px; }
            
            .balance-container { background: #1a233a; border: 1px solid #2a3a5a; padding: 6px 14px; border-radius: 20px; font-weight: bold; color: #ffcc00; display: flex; align-items: center; gap: 6px; font-size: 15px; }
            .btn-plus { background: #ff3366; color: #fff; border: none; width: 24px; height: 24px; border-radius: 50%; cursor: pointer; font-weight: bold; font-size: 15px; display: flex; align-items: center; justify-content: center; }

            /* Main Container */
            .container { max-width: 1200px; margin: 0 auto; width: 100%; padding: 20px; flex: 1; padding-bottom: 90px; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }

            /* Cases Grid */
            .cases-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }
            .case-card { background: #131b2e; border: 1px solid #1f2b45; border-radius: 14px; padding: 20px; text-align: center; cursor: pointer; transition: 0.2s; }
            .case-card:hover { border-color: #ff3366; transform: translateY(-3px); }
            .case-img { font-size: 55px; margin: 10px 0; }
            .btn-open { background: #ff3366; color: #fff; border: none; padding: 10px; width: 100%; border-radius: 8px; font-weight: bold; margin-top: 10px; cursor: pointer; }

            /* Roulette Animation */
            .roulette-container { background: #131b2e; border: 1px solid #1f2b45; border-radius: 14px; padding: 30px; text-align: center; max-width: 650px; margin: 20px auto; }
            .roulette-track-window { width: 100%; overflow: hidden; position: relative; height: 130px; background: #0b0f19; border-radius: 10px; border: 1px solid #2a3a5a; margin-bottom: 20px; }
            .roulette-pointer { position: absolute; top: 0; bottom: 0; left: 50%; width: 3px; background: #ff3366; transform: translateX(-50%); z-index: 10; }
            .roulette-track { display: flex; position: absolute; left: 0; top: 8px; transition: transform 4s cubic-bezier(0.08, 0.82, 0.17, 1); }
            .roulette-item { min-width: 110px; height: 110px; background: #1a233a; border: 1px solid #2a3a5a; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0 6px; font-weight: bold; }

            /* Panel / Forms */
            .panel { background: #131b2e; border: 1px solid #1f2b45; padding: 25px; border-radius: 14px; max-width: 420px; margin: 0 auto; }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; margin-bottom: 6px; color: #8b9bb4; font-size: 13px; }
            .form-group input { width: 100%; padding: 11px; background: #0b0f19; border: 1px solid #1f2b45; color: #fff; border-radius: 8px; font-size: 14px; }
            .btn-submit { background: #ff3366; color: #fff; border: none; padding: 11px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; }

            /* Profile Tab (Bulldrop Profile Style) */
            .profile-card { background: #131b2e; border: 1px solid #1f2b45; padding: 25px; border-radius: 14px; max-width: 450px; margin: 0 auto; text-align: center; }
            .avatar { font-size: 50px; background: #1a233a; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px auto; border: 2px solid #ff3366; }

            /* Bottom Navigation Bar (Bulldrop Style) */
            .bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: #131b2e; border-top: 1px solid #1f2b45; display: flex; justify-content: space-around; padding: 10px 0; z-index: 100; }
            .nav-item { background: transparent; border: none; color: #8b9bb4; cursor: pointer; font-size: 12px; display: flex; flex-direction: column; align-items: center; gap: 3px; font-weight: 600; transition: 0.2s; }
            .nav-item:hover, .nav-item.active { color: #ff3366; }
            .nav-item span.icon { font-size: 20px; }
        </style>
    </head>
    <body>

        <header>
            <div class="logo">⚡ BULLDROP</div>
            <div class="header-right">
                <div class="balance-container">
                    <span id="balance">0.02</span> 🪙
                    <button class="btn-plus" onclick="switchTab('wallet', document.querySelectorAll('.bottom-nav button')[1])">+</button>
                </div>
            </div>
        </header>

        <div class="container">
            
            <!-- CASES TAB -->
            <div id="cases-tab" class="tab-content active">
                <h3 style="margin-bottom: 15px; font-size: 18px;">Кейсы</h3>
                <div class="cases-grid">
                    <div class="case-card" onclick="startRoulette('oasis', 32.0)">
                        <div class="case-img">🦩</div>
                        <h4 style="font-size: 14px;">РОЗОВЫЙ ОАЗИС</h4>
                        <p style="color:#ffcc00; margin: 8px 0; font-weight: bold;">32.0 🪙</p>
                        <button class="btn-open">Открыть за 32.0 🪙</button>
                    </div>
                </div>
            </div>

            <!-- ROULETTE ANIMATION TAB -->
            <div id="roulette-tab" class="tab-content">
                <div class="roulette-container">
                    <h3 style="margin-bottom: 15px;">Кейс открывается...</h3>
                    <div class="roulette-track-window">
                        <div class="roulette-pointer"></div>
                        <div class="roulette-track" id="track"></div>
                    </div>
                    <div id="win-result" style="font-size: 18px; font-weight: bold; color: #00ffcc; margin-bottom: 15px; min-height: 25px;"></div>
                    <button class="btn-submit" onclick="switchTab('cases', document.querySelectorAll('.bottom-nav button')[0])" id="back-btn" style="display:none; max-width: 180px; margin: 0 auto;">К кейсам</button>
                </div>
            </div>

            <!-- WALLET TAB (20% Hamkor Promokodi faqat shu yerda ishlaydi) -->
            <div id="wallet-tab" class="tab-content">
                <div class="panel">
                    <h3 style="margin-bottom: 15px;">Пополнить баланс</h3>
                    <div class="form-group">
                        <label>Сумма пополнения (🪙):</label>
                        <input type="number" id="pay-amount" value="50">
                    </div>
                    <div class="form-group">
                        <label>Промокод (20% бонус):</label>
                        <input type="text" id="wallet-promo" placeholder="Например: RAVOX">
                    </div>
                    <button class="btn-submit" onclick="makePayment()">Пополнить баланс</button>
                    <p id="wallet-msg" style="margin-top: 12px; font-size: 13px; text-align: center;"></p>
                </div>
            </div>

            <!-- PROMO TAB (Keys promokodlari uchun) -->
            <div id="promo-tab" class="tab-content">
                <div class="panel">
                    <h3 style="margin-bottom: 15px;">Активация промокода</h3>
                    <div class="form-group">
                        <input type="text" id="promo-input" placeholder="Введите промокод...">
                    </div>
                    <button class="btn-submit" onclick="activatePromo()">Активировать</button>
                    <p id="promo-msg" style="margin-top: 12px; font-size: 13px; text-align: center;"></p>
                </div>
            </div>

            <!-- PROFILE TAB (Bulldrop kabinet) -->
            <div id="profile-tab" class="tab-content">
                <div class="profile-card">
                    <div class="avatar">🦹‍♂️</div>
                    <h3 style="margin-bottom: 5px;">MUBORAKXON...</h3>
                    <p style="color: #8b9bb4; font-size: 13px; margin-bottom: 20px;">ID: 9758659</p>
                    <button class="btn-submit" style="background: #1a233a; border: 1px solid #2a3a5a;" onclick="switchTab('wallet', document.querySelectorAll('.bottom-nav button')[1])">Пополнить баланс</button>
                </div>
            </div>

        </div>

        <!-- BULLDROP BOTTOM NAVIGATION BAR -->
        <nav class="bottom-nav">
            <button class="nav-item active" onclick="switchTab('cases', this)">
                <span class="icon">📦</span> Кейсы
            </button>
            <button class="nav-item" onclick="switchTab('wallet', this)">
                <span class="icon">💳</span> Пополнить
            </button>
            <button class="nav-item" onclick="switchTab('promo', this)">
                <span class="icon">🎁</span> Промокод
            </button>
            <button class="nav-item" onclick="switchTab('profile', this)">
                <span class="icon">👤</span> Профиль
            </button>
        </nav>

        <script>
            let balance = 0.02;

            function switchTab(tabName, btn) {
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                document.getElementById(tabName + '-tab').classList.add('active');
                if(btn) btn.classList.add('active');
            }

            async function makePayment() {
                let amount = parseFloat(document.getElementById('pay-amount').value) || 0;
                let code = document.getElementById('wallet-promo').value.trim();
                let msg = document.getElementById('wallet-msg');

                let res = await fetch('/topup', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `amount=${amount}&code=${code}&user_id=1`
                });
                let data = await res.json();
                if(data.success) {
                    balance = data.new_balance;
                    document.getElementById('balance').innerText = balance.toFixed(2);
                    msg.style.color = "#00ffcc";
                    msg.innerText = "✅ " + data.msg;
                } else {
                    msg.style.color = "#ff3366";
                    msg.innerText = "❌ " + data.msg;
                }
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
                if(balance < price) { alert("Недостаточно средств на балансе!"); return; }
                
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
                
                let itemsHtml = '';
                let winningIndex = 35;
                for(let i = 0; i < 50; i++) {
                    let item = (i === winningIndex) ? data.win_item : data.random_items[i % data.random_items.length];
                    itemsHtml += `<div class="roulette-item"><span>${item.img}</span><span style="font-size:11px; margin-top:4px;">${item.val} 🪙</span></div>`;
                }
                track.innerHTML = itemsHtml;

                setTimeout(() => {
                    track.style.transition = 'transform 4s cubic-bezier(0.08, 0.82, 0.17, 1)';
                    let targetOffset = (winningIndex * 122) - 250; 
                    track.style.transform = `translateX(-${targetOffset}px)`;
                }, 50);

                setTimeout(() => {
                    balance += data.win_item.val;
                    document.getElementById('balance').innerText = balance.toFixed(2);
                    document.getElementById('win-result').innerHTML = `🎉 Поздравляем! Вы выиграли: ${data.win_item.name} (${data.win_item.val} 🪙)`;
                    document.getElementById('back-btn').style.display = "block";
                }, 4100);
            }
        </script>
    </body>
    </html>
    """)

@app.post("/topup")
async def topup(amount: float = Form(...), code: str = Form(""), user_id: int = Form(1)):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    bonus = 0.0
    if code:
        cursor.execute("SELECT reward, is_partner FROM promos WHERE code = ?", (code.upper(),))
        promo = cursor.fetchone()
        if promo and promo[1] == 1:
            bonus = amount * promo[0] # 20% bonus (0.20)
            cursor.execute("UPDATE users SET partner_earned = partner_earned + ? WHERE partner_code = ?", (bonus, code.upper()))

    total_add = amount + bonus
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (total_add, user_id))
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    new_balance = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    
    msg = f"Баланс успешно пополнен на {amount} 🪙!"
    if bonus > 0:
        msg += f" Промокод активирован: +{bonus:.2f} 🪙 бонус!"
        
    return {"success": True, "new_balance": new_balance, "msg": msg}

@app.post("/activate_promo")
async def activate_promo(code: str = Form(...), user_id: int = Form(1)):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT reward, is_partner, max_uses, used_count FROM promos WHERE code = ?", (code.upper(),))
    promo = cursor.fetchone()

    if not promo:
        conn.close()
        return {"success": False, "msg": "Промокод не найден!"}

    reward, is_partner, max_uses, used_count = promo

    if is_partner == 1:
        conn.close()
        return {"success": False, "msg": "Этот партнерский промокод используется только при пополнении баланса!"}

    if used_count >= max_uses:
        conn.close()
        return {"success": False, "msg": "Промокод закончился"}

    cursor.execute("UPDATE promos SET used_count = used_count + 1 WHERE code = ?", (code.upper(),))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
    conn.commit()
    conn.close()
    return {"success": True, "reward": reward, "msg": f"Промокод успешно активирован! +{reward} 🪙"}

@app.post("/open/{case_id}")
async def open_case(case_id: str):
    case = CASES[case_id]
    win_item = random.choice(case["items"])
    random_items = [random.choice(case["items"]) for _ in range(10)]
    return {"win_item": win_item, "random_items": random_items}
