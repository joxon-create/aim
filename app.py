import os
import random
import sqlite3
import time
import threading
import requests
from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'aimdrop_pubg_ultra_secure_key_2026'

UPLOAD_FOLDER = 'static/checks'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

TELEGRAM_BOT_TOKEN = "8253855521:AAHfeLKfiDq6TtVSdF-S1RRJ7b0weu4lpOQ"  
ADMIN_TELEGRAM_ID = "8692517241"      

def notify_telegram(message):
    try:
        if TELEGRAM_BOT_TOKEN != "8253855521:AAHfeLKfiDq6TtVSdF-S1RRJ7b0weu4lpOQ":
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": ADMIN_TELEGRAM_ID, "text": message, "parse_mode": "Markdown"})
    except Exception as e:
        print("Telegram error:", e)

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
            username TEXT UNIQUE,
            password TEXT,
            balance REAL DEFAULT 100.0,
            total_deposited REAL DEFAULT 0.0,
            last_free_case TIMESTAMP,
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
            card_number TEXT,
            check_image TEXT,
            status TEXT DEFAULT 'pending',
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
    cursor.execute("INSERT OR IGNORE INTO promo_codes (id, code, bonus) VALUES (1, 'AIM2026', 50.0)")
    conn.commit()
    conn.close()

init_db()

# 35 ta maxsus PUBG buyumlari (@aimdroppubg bepul case uchun: 0.15 UC dan 25 UC gacha)
FREE_CASE_ITEMS = []
PUBG_ICONS = [
    "https://cdn-icons-png.flaticon.com/512/3076/3076137.png",
    "https://cdn-icons-png.flaticon.com/512/1069/1069158.png",
    "https://cdn-icons-png.flaticon.com/512/1069/1069216.png",
    "https://cdn-icons-png.flaticon.com/512/1046/1046857.png",
    "https://cdn-icons-png.flaticon.com/512/807/807281.png"
]

for i in range(1, 36):
    if i == 1:
        price = 25.0  # Eng qimmati 25 UC
        name = "Glacier M416 (AIM Edition)"
    elif i <= 5:
        price = round(random.uniform(5.0, 15.0), 2)
        name = f"AIM Legendary Skin #{i}"
    else:
        price = round(random.uniform(0.15, 4.5), 2)  # Eng kami 0.15 UC
        name = f"PUBG Item #{i}"
        
    FREE_CASE_ITEMS.append({
        "id": i,
        "name": name,
        "price": price,
        "img": PUBG_ICONS[i % len(PUBG_ICONS)]
    })

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
    price = round(30.0 + (i - 1) * (970.0 / 19.0), 1)
    items = []
    for j in range(1, 36):
        items.append({
            "id": j,
            "name": f"{CASE_NAMES[i-1]} - Item #{j}",
            "price": round((price / 100.0) * random.uniform(0.1, 1.5), 2),
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
    if 'user_id' in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
    return render_template('index.html', user=user, cases=CASES)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = generate_password_hash(request.form.get('password'))
        ref_id = request.args.get('ref')
        
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", (username, password, 100.0))
            new_user_id = cursor.lastrowid
            
            if ref_id:
                cursor.execute("UPDATE users SET balance = balance + 20.0 WHERE id = ?", (ref_id,))
                
            conn.commit()
            session['user_id'] = new_user_id
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Bu username band!")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Login yoki parol noto'g'ri!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/api/open_free_case', methods=['POST'])
def open_free_case():
    if 'user_id' not in session:
        return jsonify({"success": False, "msg": "Tizimga kirmagansiz!"})
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    
    cursor.execute("SELECT datetime(last_free_case, '+24 hours') > datetime('CURRENT_TIMESTAMP') FROM users WHERE id = ?", (user['id'],))
    res = cursor.fetchone()
    if res and res[0]:
        conn.close()
        return jsonify({"success": False, "msg": "Kunlik bepul case-ni 24 soatda bir marta ochish mumkin! @aimdroppubg kanaliga obuna bo'ling."})
    
    won_item = random.choice(FREE_CASE_ITEMS)
    
    cursor.execute("INSERT INTO inventory (user_id, item_name, item_image, item_price, status) VALUES (?, ?, ?, ?, 'inventory')",
                   (user['id'], won_item['name'], won_item['img'], won_item['price']))
    cursor.execute("UPDATE users SET last_free_case = CURRENT_TIMESTAMP WHERE id = ?", (user['id'],))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "won_items": [won_item], "all_items": FREE_CASE_ITEMS})

@app.route('/api/topup', methods=['POST'])
def topup_balance():
    if 'user_id' not in session:
        return jsonify({"success": False, "msg": "Tizimga kirmagansiz!"})
    amount = float(request.form.get('amount', 0))
    file = request.files.get('check_image')
    if amount <= 0 or not file:
        return jsonify({"success": False, "msg": "Summa va chek rasmini kiritish majburiy!"})
    
    filename = secure_filename(f"{time.time()}_{file.filename}")
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    cursor.execute("INSERT INTO payments (user_id, amount, card_number, check_image, status) VALUES (?, ?, ?, ?, ?)", 
                   (user['id'], amount, '5614686507631458', filename, 'pending'))
    
    # Depozit qilinganda total_deposited ni yangilaymiz (Sliv / 3 barobar limit uchun)
    cursor.execute("UPDATE users SET total_deposited = total_deposited + ? WHERE id = ?", (amount, user['id']))
    conn.commit()
    conn.close()
    notify_telegram(f"🔔 **Yangi to'lov cheki!**\n👤 User: `{user['username']}`\n💰 Summa: `{amount} UC`")
    return jsonify({"success": True, "msg": "So'rovingiz yuborildi! Admin tasdiqlashini kuting."})

@app.route('/api/open_case/<case_id>/<int:count>', methods=['POST'])
def open_case_api(case_id, count):
    if 'user_id' not in session:
        return jsonify({"success": False, "msg": "Tizimga kirmagansiz!"})
    if case_id not in CASES or count not in [1, 2, 3, 5, 10]:
        return jsonify({"success": False, "msg": "Noto'g'ri so'rov!"})
        
    case = CASES[case_id]
    total_price = case['price'] * count
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    
    if user['balance'] < total_price:
        conn.close()
        return jsonify({"success": False, "msg": "Balansingiz yetarli emas!"})
    
    # --- SLIV VA 3 BAROBAR LIMIT MANTIQI ---
    # Agar foydalanuvchi depozit qilgan bo'lsa, uning balansi (total_deposited * 3) dan oshib ketishiga yo'l qo'ymaymiz (Sliv strategiyasi)
    if user['total_deposited'] > 0:
        max_allowed_balance = user['total_deposited'] * 3.0
        if user['balance'] >= max_allowed_balance:
            # Sliv mexanizmi: Balansni avtomatik ravishda limitga moslab qo'yamiz yoki yutuqni qisqartiramiz
            pass

    cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (total_price, user['id']))
    
    won_items = []
    for _ in range(count):
        # Stratejik yutuq nazorati (Mijoz foydasiga ishlashi uchun ehtimollikni boshqarish)
        won_item = random.choice(case['items'])
        cursor.execute("INSERT INTO inventory (user_id, item_name, item_image, item_price, status) VALUES (?, ?, ?, ?, 'inventory')",
                       (user['id'], won_item['name'], won_item['img'], won_item['price']))
        won_items.append(won_item)
        
    # Balans 3 barobardan oshib ketmasligini qat'iy nazorat qilamiz
    if user['total_deposited'] > 0:
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user['id'],))
        current_bal = cursor.fetchone()[0]
        max_limit = user['total_deposited'] * 3.0
        if current_bal > max_limit:
            cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (max_limit, user['id']))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "won_items": won_items, "all_items": case['items']})

@app.route('/api/inventory')
def get_inventory():
    if 'user_id' not in session:
        return jsonify({"items": []})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE user_id = ? AND status = 'inventory'", (session['user_id'],))
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"items": items})

@app.route('/api/sell_item/<int:item_id>', methods=['POST'])
def sell_item(item_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "msg": "Kirmagansiz!"})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE id = ? AND user_id = ? AND status = 'inventory'", (item_id, session['user_id']))
    item = cursor.fetchone()
    if not item:
        conn.close()
        return jsonify({"success": False, "msg": "Buyum topilmadi!"})
    
    cursor.execute("UPDATE inventory SET status = 'sold' WHERE id = ?", (item['id'],))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (item['item_price'], session['user_id']))
    
    # Sotgandan keyin ham 3 barobar limitni tekshiramiz
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    u_data = cursor.fetchone()
    if u_data['total_deposited'] > 0:
        max_limit = u_data['total_deposited'] * 3.0
        if u_data['balance'] > max_limit:
            cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (max_limit, u_data['id']))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": f"{item['item_price']} UC balansga qo'shildi!"})

@app.route('/api/sell_all_inventory', methods=['POST'])
def sell_all_inventory():
    if 'user_id' not in session:
        return jsonify({"success": False, "msg": "Kirmagansiz!"})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(item_price) FROM inventory WHERE user_id = ? AND status = 'inventory'", (session['user_id'],))
    total_sum = cursor.fetchone()[0]
    if not total_sum or total_sum <= 0:
        conn.close()
        return jsonify({"success": False, "msg": "Inventaringizda sotiladigan buyum yo'q!"})
        
    cursor.execute("UPDATE inventory SET status = 'sold' WHERE user_id = ? AND status = 'inventory'", (session['user_id'],))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (total_sum, session['user_id']))
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    u_data = cursor.fetchone()
    if u_data['total_deposited'] > 0:
        max_limit = u_data['total_deposited'] * 3.0
        if u_data['balance'] > max_limit:
            cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (max_limit, u_data['id']))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": f"Barcha buyumlar sotildi! Jami +{total_sum} UC qo'shildi."})

@app.route('/api/withdraw_uc', methods=['POST'])
def withdraw_uc():
    if 'user_id' not in session:
        return jsonify({"success": False, "msg": "Tizimga kirmagansiz!"})
    pubg_id = request.form.get('pubg_id', '').strip()
    uc_amount = int(request.form.get('uc_amount', 0))
    if not pubg_id or uc_amount < 60:
        return jsonify({"success": False, "msg": "Minimal UC yechish 60 UC va PUBG ID shart!"})
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    if user['balance'] < uc_amount:
        conn.close()
        return jsonify({"success": False, "msg": "Balansingizda yetarli UC yo'q!"})
        
    cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (uc_amount, user['id']))
    cursor.execute("INSERT INTO withdraws (user_id, pubg_id, uc_amount) VALUES (?, ?, ?)", (user['id'], pubg_id, uc_amount))
    conn.commit()
    conn.close()
    notify_telegram(f"📤 **Yangi UC yechish so'rovi!**\n👤 User: `{user['username']}`\n🆔 PUBG ID: `{pubg_id}`\n💎 Miqdor: `{uc_amount} UC`")
    return jsonify({"success": True, "msg": f"PUBG ID: {pubg_id} ga {uc_amount} UC yechishga yuborildi."})

@app.route('/api/activate_promo', methods=['POST'])
def activate_promo():
    if 'user_id' not in session:
        return jsonify({"success": False, "msg": "Kirmagansiz!"})
    code = request.form.get('code', '').strip()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM promo_codes WHERE code = ?", (code,))
    promo = cursor.fetchone()
    if not promo:
        conn.close()
        return jsonify({"success": False, "msg": "Promo-kod topilmadi!"})
    
    cursor.execute("SELECT * FROM promo_history WHERE user_id = ? AND promo_id = ? AND datetime(used_at, '+24 hours') > datetime('CURRENT_TIMESTAMP')",
                   (user['id'], promo['id']))
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "msg": "Bu promo-kodni 24 soatda 1 marta ishlatish mumkin!"})
    
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (promo['bonus'], user['id']))
    cursor.execute("INSERT INTO promo_history (user_id, promo_id) VALUES (?, ?)", (user['id'], promo['id']))
    cursor.execute("UPDATE promo_codes SET uses_count = uses_count + 1 WHERE id = ?", (promo['id'],))
    
    # Promo bonusdan keyin ham limitni tekshiramiz
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    u_data = cursor.fetchone()
    if u_data['total_deposited'] > 0:
        max_limit = u_data['total_deposited'] * 3.0
        if u_data['balance'] > max_limit:
            cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (max_limit, u_data['id']))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": f"Muvaffaqiyatli! +{promo['bonus']} UC qo'shildi."})

@app.route('/api/crash_status')
def crash_status_api():
    return jsonify({"multiplier": global_crash_multiplier, "status": crash_status})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
