import random
import sqlite3
import time
import threading
from flask import Flask, render_template, request, redirect, session, jsonify, url_for

app = Flask(__name__)
app.secret_key = 'aimdrop_pubg_secret_key_2026_secure'

# --- GLOBAL CRASH O'YIN SERVERI (Hamma uchun bir xil vaqtda uchadi) ---
global_crash_multiplier = 1.0
crash_status = "waiting"

def crash_game_loop():
    global global_crash_multiplier, crash_status
    while True:
        crash_status = "waiting"
        global_crash_multiplier = 1.0
        time.sleep(5)
        
        crash_status = "running"
        target_crash = round(random.uniform(1.1, 10.0), 2)
        
        while global_crash_multiplier < target_crash and crash_status == "running":
            global_crash_multiplier = round(global_crash_multiplier + 0.05, 2)
            time.sleep(0.1)
            
        crash_status = "crashed"
        time.sleep(3)

threading.Thread(target=crash_game_loop, daemon=True).start()

def get_db():
    conn = sqlite3.connect('aimdrop_ecosystem.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_uuid TEXT UNIQUE,
            username TEXT,
            auth_provider TEXT,
            balance REAL DEFAULT 150.0,
            demo_balance REAL DEFAULT 1000.0,
            is_partner INTEGER DEFAULT 0,
            referrer_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_name TEXT,
            item_image TEXT,
            item_price REAL,
            status TEXT DEFAULT 'inventory'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            provider TEXT,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdraws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            pubg_id TEXT,
            uc_amount INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            bonus REAL,
            is_free_case INTEGER DEFAULT 0,
            partner_id INTEGER,
            uses_count INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promo_history (
            user_id INTEGER,
            promo_id INTEGER,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- 20 TA CASE VA HAR BIRIDAGI 30+ TA BUYUM (BULLDROP / AIMDROP USLUBIDA) ---
PUBG_ICONS = [
    "https://cdn-icons-png.flaticon.com/512/3076/3076137.png",
    "https://cdn-icons-png.flaticon.com/512/1069/1069158.png",
    "https://cdn-icons-png.flaticon.com/512/1069/1069216.png",
    "https://cdn-icons-png.flaticon.com/512/1046/1046857.png",
    "https://cdn-icons-png.flaticon.com/512/807/807281.png",
    "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
]

CASE_NAMES = [
    "AimDrop Glacier M416", "AimDrop Pharaoh X-Suit", "AimDrop Mummy Set", "AimDrop Blood Raven",
    "AimDrop Poseidon Box", "AimDrop Conqueror Crate", "AimDrop Classic Crate", "AimDrop Premium Crate",
    "AimDrop Supply Crate", "AimDrop Heroic Box", "AimDrop Neon Riot", "AimDrop Cyber 2077",
    "AimDrop Royal Pass", "AimDrop Godzilla Crate", "AimDrop Kong Box", "AimDrop Venom Set",
    "AimDrop Joker Bundle", "AimDrop Ghost Rider", "AimDrop Titan Crate", "AimDrop Apex Predator"
]

CASES = {}
for i in range(1, 21):
    case_key = f"case_{i}"
    price = round(10.0 + (i - 1) * 7.5, 1)
    items = []
    for j in range(1, 33):
        if j <= 3:
            tier = "Mythic"
            mult = random.uniform(15.0, 30.0)
        elif j <= 10:
            tier = "Legendary"
            mult = random.uniform(4.0, 12.0)
        else:
            tier = "Epic/Rare"
            mult = random.uniform(0.5, 3.5)
            
        items.append({
            "id": j,
            "name": f"{CASE_NAMES[i-1]} - Item #{j} ({tier})",
            "price": round(price * mult, 2),
            "img": PUBG_ICONS[j % len(PUBG_ICONS)]
        })
    CASES[case_key] = {
        "id": case_key,
        "name": CASE_NAMES[i-1],
        "price": price,
        "img": PUBG_ICONS[(i-1) % len(PUBG_ICONS)],
        "items": items
    }

# --- ASOSIY SAHIFA VA SHAXSIY KABINET ---
@app.route('/')
def index():
    user = None
    if 'user_uuid' in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_uuid = ?", (session['user_uuid'],))
        user = cursor.fetchone()
        conn.close()
    return render_template('index.html', user=user, cases=CASES)

@app.route('/login/<provider>')
def login(provider):
    import uuid
    fake_id = f"{provider}_{uuid.uuid4().hex[:8]}"
    username = f"AimUser_{uuid.uuid4().hex[:4]}"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_uuid = ?", (fake_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute("INSERT INTO users (user_uuid, username, auth_provider, balance, demo_balance) VALUES (?, ?, ?, ?, ?)",
                       (fake_id, username, provider, 200.0, 1000.0))
        conn.commit()
    
    session['user_uuid'] = fake_id
    conn.close()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_uuid', None)
    return redirect(url_for('index'))

# --- SHAXSIY KABINET API & BALANS TO'LDIRISH / UC YECHISH ---
@app.route('/api/profile')
def profile_api():
    if 'user_uuid' not in session:
        return jsonify({"success": False})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_uuid = ?", (session['user_uuid'],))
    user = dict(cursor.fetchone())
    
    cursor.execute("SELECT * FROM inventory WHERE user_id = ? AND status = 'inventory'", (user['id'],))
    inventory = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM payments WHERE user_id = ?", (user['id'],))
    payments = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM withdraws WHERE user_id = ?", (user['id'],))
    withdraws = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({
        "success": True,
        "user": user,
        "inventory": inventory,
        "payments": payments,
        "withdraws": withdraws
    })

@app.route('/api/topup', methods=['POST'])
def topup_balance():
    if 'user_uuid' not in session:
        return jsonify({"success": False, "msg": "Kirmagansiz!"})
    
    amount = float(request.form.get('amount', 0))
    provider = request.form.get('provider', 'Click/Payme')
    
    if amount <= 0:
        return jsonify({"success": False, "msg": "Noto'g'ri summa!"})
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_uuid = ?", (session['user_uuid'],))
    user = cursor.fetchone()
    
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user['id']))
    cursor.execute("INSERT INTO payments (user_id, amount, provider) VALUES (?, ?, ?)", (user['id'], amount, provider))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": f"{amount} balansga qo'shildi!"})

@app.route('/api/withdraw_uc', methods=['POST'])
def withdraw_uc():
    if 'user_uuid' not in session:
        return jsonify({"success": False, "msg": "Kirmagansiz!"})
    
    pubg_id = request.form.get('pubg_id', '').strip()
    uc_amount = int(request.form.get('uc_amount', 0))
    
    if not pubg_id or uc_amount < 60:
        return jsonify({"success": False, "msg": "Minimal UC yechish 60 UC va PUBG ID kiritilishi shart!"})
        
    # 1 UC = 0.015 balance hisobidan yechamiz
    cost = uc_amount * 0.015
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_uuid = ?", (session['user_uuid'],))
    user = cursor.fetchone()
    
    if user['balance'] < cost:
        conn.close()
        return jsonify({"success": False, "msg": "Balansingizda yetarli mablag' yo'q!"})
        
    cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (cost, user['id']))
    cursor.execute("INSERT INTO withdraws (user_id, pubg_id, uc_amount) VALUES (?, ?, ?)", (user['id'], pubg_id, uc_amount))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": f"PUBG ID: {pubg_id} ga {uc_amount} UC chiqarishga yuborildi!"})

# --- KASSA VA O'YINLAR (Case, Sell, Crash) ---
@app.route('/api/open_case/<case_id>', methods=['POST'])
def open_case(case_id):
    if 'user_uuid' not in session:
        return jsonify({"success": False, "msg": "Tizimga kirmagansiz!"})
    if case_id not in CASES:
        return jsonify({"success": False, "msg": "Case topilmadi!"})
        
    case = CASES[case_id]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_uuid = ?", (session['user_uuid'],))
    user = cursor.fetchone()
    
    if user['balance'] < case['price']:
        conn.close()
        return jsonify({"success": False, "msg": "Balansingiz yetarli emas!"})
    
    cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (case['price'], user['id']))
    won_item = random.choice(case['items'])
    
    cursor.execute("INSERT INTO inventory (user_id, item_name, item_image, item_price) VALUES (?, ?, ?, ?)",
                   (user['id'], won_item['name'], won_item['img'], won_item['price']))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "item": won_item})

@app.route('/api/sell_item/<int:item_id>', methods=['POST'])
def sell_item(item_id):
    if 'user_uuid' not in session:
        return jsonify({"success": False})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE id = ? AND status = 'inventory'", (item_id,))
    item = cursor.fetchone()
    if item:
        cursor.execute("UPDATE inventory SET status = 'sold' WHERE id = ?", (item_id,))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (item['item_price'], item['user_id']))
        conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/crash_status')
def crash_status_api():
    return jsonify({
        "multiplier": global_crash_multiplier,
        "status": crash_status
    })

@app.route('/api/activate_promo', methods=['POST'])
def activate_promo():
    if 'user_uuid' not in session:
        return jsonify({"success": False, "msg": "Avtorizatsiyadan o'ting!"})
    
    code = request.form.get('code', '').strip()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_uuid = ?", (session['user_uuid'],))
    user = cursor.fetchone()
    
    cursor.execute("SELECT * FROM promo_codes WHERE code = ?", (code,))
    promo = cursor.fetchone()
    
    if not promo:
        conn.close()
        return jsonify({"success": False, "msg": "Promo-kod topilmadi!"})
    
    cursor.execute("SELECT * FROM promo_history WHERE user_id = ? AND promo_id = ? AND datetime(used_at, '+24 hours') > datetime('CURRENT_TIMESTAMP')",
                   (user['id'], promo['id']))
    if cursor.fetchone() and promo['is_free_case'] == 1:
        conn.close()
        return jsonify({"success": False, "msg": "Bu 24 soatlik free case promosi allaqachon ishlatilgan!"})
    
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (promo['bonus'], user['id']))
    cursor.execute("INSERT INTO promo_history (user_id, promo_id) VALUES (?, ?)", (user['id'], promo['id']))
    cursor.execute("UPDATE promo_codes SET uses_count = uses_count + 1 WHERE id = ?", (promo['id'],))
    
    if promo['partner_id']:
        p_bonus = promo['bonus'] * 0.20
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (p_bonus, promo['partner_id']))
        
    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": f"Muvaffaqiyatli! +{promo['bonus']} qo'shildi."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
