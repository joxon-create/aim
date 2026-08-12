import random
import sqlite3
import time
import threading
from flask import Flask, render_template, request, redirect, session, jsonify, url_for

app = Flask(__name__)
app.secret_key = 'aimdrop_pubg_secret_key_2026_secure'

# --- GLOBAL CRASH O'YIN SERVERI ---
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
            balance REAL DEFAULT 500.0,
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
            card_number TEXT,
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
    
    # Test uchun hamkor promokod qo'shamiz (Bonus: 100 UC, 20% hamkorga tushadi)
    cursor.execute("INSERT OR IGNORE INTO promo_codes (id, code, bonus, partner_id) VALUES (1, 'AIM2026', 100.0, 1)")
    conn.commit()
    conn.close()

init_db()

# --- 20 TA CASE (30 UC dan 1000 UC gacha, katta yutqazish ehtimoli bilan 30+ buyum) ---
PUBG_ICONS = [
    "https://cdn-icons-png.flaticon.com/512/3076/3076137.png",
    "https://cdn-icons-png.flaticon.com/512/1069/1069158.png",
    "https://cdn-icons-png.flaticon.com/512/1069/1069216.png",
    "https://cdn-icons-png.flaticon.com/512/1046/1046857.png",
    "https://cdn-icons-png.flaticon.com/512/807/807281.png",
    "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
]

CASE_NAMES = [
    "AimDrop Beginner Box", "AimDrop Supply Crate", "AimDrop Classic Crate", "AimDrop Premium Crate",
    "AimDrop Heroic Box", "AimDrop Neon Riot", "AimDrop Cyber 2077", "AimDrop Royal Pass",
    "AimDrop Godzilla Crate", "AimDrop Kong Box", "AimDrop Venom Set", "AimDrop Joker Bundle",
    "AimDrop Ghost Rider", "AimDrop Titan Crate", "AimDrop Apex Predator", "AimDrop Blood Raven",
    "AimDrop Mummy Set", "AimDrop Poseidon Box", "AimDrop Pharaoh X-Suit", "AimDrop Glacier M416"
]

CASES = {}
for i in range(1, 21):
    case_key = f"case_{i}"
    # Narxlar 30 UC dan boshlanib 1000 UC gacha boradi
    price = round(30.0 + (i - 1) * (970.0 / 19.0), 1)
    
    items = []
    # Har bir case ichida 32 ta buyum (Katta qismi arzon, ya'ni yutqazish ehtimoli katta)
    for j in range(1, 33):
        if j == 1:
            tier = "Mythic (Super Rare)"
            multiplier = random.uniform(2.0, 5.0) # Faqat bitta itemgina qimmatroq bo'lishi mumkin
        elif j <= 5:
            tier = "Legendary"
            multiplier = random.uniform(0.8, 1.3)
        else:
            tier = "Loss/Common"
            multiplier = random.uniform(0.1, 0.5) # Case narxidan bir necha barobar arzon (yutqazish)
            
        items.append({
            "id": j,
            "name": f"{CASE_NAMES[i-1]} - Item #{j} ({tier})",
            "price": round(price * multiplier, 2),
            "img": PUBG_ICONS[j % len(PUBG_ICONS)]
        })
    
    CASES[case_key] = {
        "id": case_key,
        "name": CASE_NAMES[i-1],
        "price": price,
        "img": PUBG_ICONS[(i-1) % len(PUBG_ICONS)],
        "items": items
    }

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
                       (fake_id, username, provider, 500.0, 1000.0))
        conn.commit()
    
    session['user_uuid'] = fake_id
    conn.close()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_uuid', None)
    return redirect(url_for('index'))

@app.route('/api/topup', methods=['POST'])
def topup_balance():
    if 'user_uuid' not in session:
        return jsonify({"success": False, "msg": "Kirmagansiz!"})
    amount = float(request.form.get('amount', 0))
    card_number = request.form.get('card', '5614686507631458')
    
    if amount <= 0:
        return jsonify({"success": False, "msg": "Noto'g'ri summa!"})
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_uuid = ?", (session['user_uuid'],))
    user = cursor.fetchone()
    
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user['id']))
    cursor.execute("INSERT INTO payments (user_id, amount, provider, card_number) VALUES (?, ?, ?, ?)", 
                   (user['id'], amount, 'P2P Transfer', card_number))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": f"{amount} UC kartaga o'tkazma orqali balansga qo'shildi!"})

@app.route('/api/withdraw_uc', methods=['POST'])
def withdraw_uc():
    if 'user_uuid' not in session:
        return jsonify({"success": False, "msg": "Kirmagansiz!"})
    pubg_id = request.form.get('pubg_id', '').strip()
    uc_amount = int(request.form.get('uc_amount', 0))
    
    if not pubg_id or uc_amount < 60:
        return jsonify({"success": False, "msg": "Minimal UC yechish 60 UC va PUBG ID kiritilishi shart!"})
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_uuid = ?", (session['user_uuid'],))
    user = cursor.fetchone()
    
    if user['balance'] < uc_amount:
        conn.close()
        return jsonify({"success": False, "msg": "Balansingizda yetarli UC yo'q!"})
        
    cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (uc_amount, user['id']))
    cursor.execute("INSERT INTO withdraws (user_id, pubg_id, uc_amount) VALUES (?, ?, ?)", (user['id'], pubg_id, uc_amount))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": f"PUBG ID: {pubg_id} ga {uc_amount} UC chiqarishga yuborildi!"})

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
    
    # Tasodifiy buyum tanlash
    won_item = random.choice(case['items'])
    
    cursor.execute("INSERT INTO inventory (user_id, item_name, item_image, item_price) VALUES (?, ?, ?, ?)",
                   (user['id'], won_item['name'], won_item['img'], won_item['price']))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "item": won_item})

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
    
    # 24 soatlik chekrovni tekshirish
    cursor.execute("SELECT * FROM promo_history WHERE user_id = ? AND promo_id = ? AND datetime(used_at, '+24 hours') > datetime('CURRENT_TIMESTAMP')",
                   (user['id'], promo['id']))
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Bu promo-kodni 24 soatda 1 marta ishlatish mumkin!"})
    
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (promo['bonus'], user['id']))
    cursor.execute("INSERT INTO promo_history (user_id, promo_id) VALUES (?, ?)", (user['id'], promo['id']))
    cursor.execute("UPDATE promo_codes SET uses_count = uses_count + 1 WHERE id = ?", (promo['id'],))
    
    # Hamkor ulushi (20%)
    if promo['partner_id']:
        partner_bonus = promo['bonus'] * 0.20
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (partner_bonus, promo['partner_id']))
        
    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": f"Muvaffaqiyatli! +{promo['bonus']} UC qo'shildi."})

@app.route('/api/crash_status')
def crash_status_api():
    return jsonify({
        "multiplier": global_crash_multiplier,
        "status": crash_status
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
