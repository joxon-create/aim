from fastapi import FastAPI, Request
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
            balance REAL DEFAULT 0.01,
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
    # Standart sinov promokodlari
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
            {"name": "Kukri Ares", "val": 148.8},
            {"name": "AWM BOOM", "val": 781.9},
            {"name": "AKR Dragon", "val": 45.0},
            {"name": "USP Ghosts", "val": 12.5}
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
        <title>Bulldrop Pro</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            body { background: #0b0f19; color: #fff; min-height: 100vh; display: flex; flex-direction: column; align-items: center; }
            header { width: 100%; max-width: 1200px; display: flex; justify-content: space-between; align-items: center; background: #131b2e; padding: 15px 30px; border-bottom: 1px solid #1f2b45; }
            .logo { font-size: 24px; font-weight: bold; color: #ff3366; }
            .balance-box { background: #1a233a; border: 1px solid #2a3a5a; padding: 8px 16px; border-radius: 20px; font-weight: bold; color: #ffcc00; }
            .container { width: 100%; max-width: 1200px; padding: 20px; flex: 1; }
            .panel { background: #131b2e; border: 1px solid #1f2b45; padding: 30px; border-radius: 15px; max-width: 450px; margin: 20px auto; text-align: center; }
            .form-group { margin-bottom: 15px; text-align: left; }
            .form-group label { display: block; margin-bottom: 8px; color: #aaa; }
            .form-group input { width: 100%; padding: 12px; background: #0b0f19; border: 1px solid #1f2b45; color: #fff; border-radius: 8px; }
            .btn-submit { background: #ff3366; color: #fff; border: none; padding: 12px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; }
            .case-card { background: #131b2e; border: 1px solid #1f2b45; padding: 20px; border-radius: 15px; width: 240px; text-align: center; display: inline-block; cursor: pointer; }
            .btn-open { background: #ff3366; color: #fff; border: none; padding: 10px; width: 100%; border-radius: 8px; font-weight: bold; margin-top: 15px; cursor: pointer; }
        </style>
    </head>
    <body>
        <header>
            <div class="logo">⚡ BULLDROP</div>
            <div class="balance-box">Balans: <span id="balance">11.31</span> 🪙</div>
        </header>

        <div class="container">
            <h2 style="margin-bottom: 20px;">PUBG M & S20 Keyslar</h2>
            <div class="case-card" onclick="openCase()">
                <h3>Розовый оазис</h3>
                <p style="color:#ffcc00; margin: 10px 0;">24.03 🪙</p>
                <button class="btn-open">Ochish</button>
            </div>

            <div class="panel" style="margin-top: 40px;">
                <h2>Promokodni Faollashtirish</h2>
                <div class="form-group" style="margin-top: 15px;">
                    <input type="text" id="promo-input" placeholder="Promokodni kiriting...">
                </div>
                <button class="btn-submit" onclick="activatePromo()">Faollashtirish</button>
                <p id="promo-msg" style="margin-top: 15px;"></p>
            </div>
        </div>

        <script>
            let balance = 11.31;

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

            async function openCase() {
                if(balance < 24.03) { alert("Balans yetarli emas!"); return; }
                let res = await fetch('/open/oasis', {method: 'POST'});
                let data = await res.json();
                balance = balance - 24.03 + data.val;
                document.getElementById('balance').innerText = balance.toFixed(2);
                alert("🎉 Tabriklaymiz! Yutdingiz: " + data.name + " (" + data.val + " 🪙)");
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
        return {"success": False, "msg": "Promokod ishlash muddati tugadi / Промокод закончился"}

    # Limitni yangilash
    if not is_partner:
        cursor.execute("UPDATE promos SET used_count = used_count + 1 WHERE code = ?", (code.upper(),))
    else:
        # Hamkor promokodidan kelgan foydani hisobga qo'shish
        cursor.execute("UPDATE users SET partner_earned = partner_earned + ? WHERE partner_code = ?", (reward, code.upper()))

    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
    conn.commit()
    conn.close()
    return {"success": True, "reward": reward, "msg": f"Muvaffaqiyatli faollashtirildi! +{reward} 🪙 qo'shildi."}

@app.post("/open/{case_id}")
async def open_case(case_id: str):
    case = CASES[case_id]
    item = random.choice(case["items"])
    return {"name": item["name"], "val": item["val"]}
