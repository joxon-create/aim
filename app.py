import os
import random
import sqlite3
import time
import requests
from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = 'aimdrop_pubg_ultra_ultimate_2026'

UPLOAD_FOLDER = 'static/checks'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

TELEGRAM_BOT_TOKEN = "8253855521:AAHSIzRLRV_v2IqZQXeL32JJxZppLA1KwoY"
ADMIN_TELEGRAM_ID = "8692517241"

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
            deposit_count INTEGER DEFAULT 0,
            telegram_id TEXT,
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
            check_image TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

PUBG_ICONS = [
    "https://cdn-icons-png.flaticon.com/512/3076/3076137.png",
    "https://cdn-icons-png.flaticon.com/512/1069/1069158.png",
    "https://cdn-icons-png.flaticon.com/512/1069/1069216.png",
    "https://cdn-icons-png.flaticon.com/512/1046/1046857.png",
    "https://cdn-icons-png.flaticon.com/512/807/807281.png"
]

# 35 ta buyum (0.01% ehtimollik bilan 25 UC lik Glacier M416 tushishi uchun maxsus tanlanadi)
FREE_CASE_ITEMS = []
for i in range(1, 36):
    if i == 1:
        price = 25.0
        name = "Glacier M416 (AIM Edition - 0.01%)"
    else:
        price = round(random.uniform(0.15, 3.5), 2)
        name = f"PUBG Supply Item #{i}"
    FREE_CASE_ITEMS.append({"id": i, "name": name, "price": price, "img": PUBG_ICONS[i % len(PUBG_ICONS)]})

CASE_NAMES = [
    "AimDrop Beginner Box", "AimDrop Supply Crate", "AimDrop Classic Crate", "AimDrop Premium Crate",
    "AimDrop Heroic Box", "AimDrop Neon Riot", "AimDrop Cyber 2077", "AimDrop Royal Pass",
    "AimDrop Godzilla Crate", "AimDrop Kong Box", "AimDrop Venom Set", "AimDrop Joker Bundle",
    "AimDrop Ghost Rider", "AimDrop Titan Crate", "AimDrop Apex Predator", "AimDrop Blood Raven",
    "AimDrop Mummy Set", "AimDrop Poseidon Box", "AimDrop Pharaoh X-Suit", "AimDrop Glacier M416"
]

CASES = {
    "free_case": {
        "id": "free_case",
        "name": "Kunlik Bepul Case (AIM)",
        "price": 0,
        "img": PUBG_ICONS[0],
        "items": FREE_CASE_ITEMS
    }
}

for i in range(1, 21):
    case_key = f"case_{i}"
    price = round(30.0 + (i - 1) * (970.0 / 19.0), 1)
    items = []
    for j in range(1, 36):
        if j == 1:
            p_val = price * 1.5  # 0.01% ehtimol uchun qimmat item
            n_val = f"{CASE_NAMES[i-1]} - Rare Glacier"
        else:
            p_val = round((price / 100.0) * random.uniform(0.1, 1.2), 2)
            n_val = f"{CASE_NAMES[i-1]} - Item #{j}"
        items.append({"id": j, "name": n_val, "price": p_val, "img": PUBG_ICONS[j % len(PUBG_ICONS)]})
    
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
    # Google orqali tezkor kirish simulyatsiyasi (avtomatik yaratish va sessiyada saqlash)
    google_username = f"GoogleUser_{random.randint(1000, 9999)}"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (google_username,))
    existing = cursor.fetchone()
    if not existing:
        cursor.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", 
                       (google_username, generate_password_hash("google_auth"), 100.0))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE username = ?", (google_username,))
        existing = cursor.fetchone()
    
    session['user_id'] = existing['id']
    conn.close()
    return redirect(url_for('index'))

@app.route('/login')
def login():
    return redirect(url_for('register'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/api/link_telegram', methods=['POST'])
def link_telegram():
    if 'user_id' not in session:
        return jsonify({"success": False, "msg": "Kirmagansiz!"})
    t_id = request.form.get('telegram_id')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET telegram_id = ? WHERE id = ?", (t_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": "Telegram akkauntingiz muvaffaqiyatli bog'landi!"})

@app.route('/api/open_free_case', methods=['POST'])
def open_free_case():
    if 'user_id' not in session:
        return jsonify({"success": False, "msg": "Kirmagansiz!"})
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    
    if not user['telegram_id']:
        conn.close()
        return jsonify({"success": False, "msg": "Avval Telegram akkauntingizni ulang va kanalga obuna bo'ling!"})
        
    cursor.execute("SELECT datetime(last_free_case, '+24 hours') > datetime('CURRENT_TIMESTAMP') FROM users WHERE id = ?", (user['id'],))
    res = cursor.fetchone()
    if res and res[0]:
        conn.close()
        return jsonify({"success": False, "msg": "Bepul case'ni har 24 soatda faqat 1 marta ochish mumkin!"})
    
    # 0.01% ehtimollik bilan 25 UC lik Glacier M416 tushishi
    rand_val = random.random()
    if rand_val < 0.0001:  # 0.01%
        won_item = FREE_CASE_ITEMS[0]
    else:
        won_item = random.choice(FREE_CASE_ITEMS[1:])
        
    cursor.execute("INSERT INTO inventory (user_id, item_name, item_image, item_price, status) VALUES (?, ?, ?, ?, 'inventory')",
                   (user['id'], won_item['name'], won_item['img'], won_item['price']))
    cursor.execute("UPDATE users SET last_free_case = CURRENT_TIMESTAMP WHERE id = ?", (user['id'],))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "won_item": won_item, "all_items": FREE_CASE_ITEMS})

@app.route('/api/open_case/<case_id>', methods=['POST'])
def open_case_api(case_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "msg": "Kirmagansiz!"})
    if case_id not in CASES:
        return jsonify({"success": False, "msg": "Case topilmadi!"})
        
    case = CASES[case_id]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    
    if user['balance'] < case['price']:
        conn.close()
        return jsonify({"success": False, "msg": "Balansingiz yetarli emas!"})
        
    cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (case['price'], user['id']))
    
    # Stratgey: 1-chi depozitdan so'ng 3 barobarigacha chiqarib oladi, keyingi safarlari aniq sliv (omadi kelmaydi)
    if user['deposit_count'] == 1 and user['balance'] <= user['total_deposited'] * 3.0:
        won_item = random.choice(case['items'])  # 1-chi safar omadliroq
    elif user['deposit_count'] > 1:
        won_item = case['items'][-1]  # Arzon item (sliv)
    else:
        if random.random() < 0.0001:  # 0.01% eng qimmat narsa
            won_item = case['items'][0]
        else:
            won_item = random.choice(case['items'][1:])
            
    cursor.execute("INSERT INTO inventory (user_id, item_name, item_image, item_price, status) VALUES (?, ?, ?, ?, 'inventory')",
                   (user['id'], won_item['name'], won_item['img'], won_item['price']))
    
    # Sliv mantiqi: Agar depozit qilingan bo'lsa va limitdan oshsa, avtomatik cheklash
    if user['total_deposited'] > 0 and user['deposit_count'] > 1:
        cursor.execute("UPDATE users SET balance = balance * 0.95 WHERE id = ?", (user['id'],)) # Sliv trend
        
    conn.commit()
    conn.close()
    return jsonify({"success": True, "won_item": won_item, "all_items": case['items']})

@app.route('/api/topup', methods=['POST'])
def topup_balance():
    if 'user_id' not in session:
        return jsonify({"success": False, "msg": "Kirmagansiz!"})
    amount = float(request.form.get('amount', 0))
    file = request.files.get('check_image')
    if amount <= 0 or not file:
        return jsonify({"success": False, "msg": "Ma'lumotlar xato!"})
        
    filename = secure_filename(f"{time.time()}_{file.filename}")
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    
    # Depozit soni va miqdorini yangilaymiz (1-chi safar 3 barobar, keyingisi sliv)
    cursor.execute("UPDATE users SET total_deposited = total_deposited + ?, deposit_count = deposit_count + 1, balance = balance + ? WHERE id = ?", 
                   (amount, amount, user['id']))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": "To'lov qabul qilindi! Balansga qo'shildi."})

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
        return jsonify({"success": False, "msg": "Topilmadi!"})
    cursor.execute("UPDATE inventory SET status = 'sold' WHERE id = ?", (item['id'],))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (item['item_price'], session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": f"+{item['item_price']} UC qo'shildi!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
