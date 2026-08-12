import os
import random
import sqlite3
import time
from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = 'aimdrop_ultimate_secure_2026'

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
            balance REAL DEFAULT 150.0,
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

FREE_CASE_ITEMS = []
for i in range(1, 36):
    if i == 1:
        price, name = 25.0, "Glacier M416 (0.01% Rare)"
    else:
        price, name = round(random.uniform(0.15, 3.5), 2), f"PUBG Item #{i}"
    FREE_CASE_ITEMS.append({"id": i, "name": name, "price": price, "img": PUBG_ICONS[i % len(PUBG_ICONS)]})

CASE_NAMES = [
    "AimDrop Beginner Box", "AimDrop Supply Crate", "AimDrop Classic Crate", "AimDrop Premium Crate",
    "AimDrop Heroic Box", "AimDrop Neon Riot", "AimDrop Cyber 2077", "AimDrop Royal Pass",
    "AimDrop Godzilla Crate", "AimDrop Kong Box", "AimDrop Venom Set", "AimDrop Joker Bundle",
    "AimDrop Ghost Rider", "AimDrop Titan Crate", "AimDrop Apex Predator", "AimDrop Blood Raven",
    "AimDrop Mummy Set", "AimDrop Poseidon Box", "AimDrop Pharaoh X-Suit", "AimDrop Glacier M416"
]

CASES = {
    "free_case": {"id": "free_case", "name": "Kunlik Bepul Case (AIM)", "price": 0, "img": PUBG_ICONS[0], "items": FREE_CASE_ITEMS}
}

for i in range(1, 21):
    c_key = f"case_{i}"
    price = round(30.0 + (i - 1) * (970.0 / 19.0), 1)
    items = []
    for j in range(1, 36):
        p_val = price * 1.5 if j == 1 else round((price / 100.0) * random.uniform(0.1, 1.2), 2)
        items.append({"id": j, "name": f"{CASE_NAMES[i-1]} - Item #{j}", "price": p_val, "img": PUBG_ICONS[j % len(PUBG_ICONS)]})
    CASES[c_key] = {"id": c_key, "name": CASE_NAMES[i-1], "price": price, "img": PUBG_ICONS[(i-1) % len(PUBG_ICONS)], "items": items}

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

@app.route('/register')
def register():
    g_name = f"GoogleUser_{random.randint(1000, 9999)}"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", (g_name, generate_password_hash("google"), 150.0))
    conn.commit()
    cursor.execute("SELECT * FROM users WHERE username = ?", (g_name,))
    user = cursor.fetchone()
    session['user_id'] = user['id']
    conn.close()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/api/link_telegram', methods=['POST'])
def link_telegram():
    if 'user_id' not in session: return jsonify({"success": False})
    t_id = request.form.get('telegram_id')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET telegram_id = ? WHERE id = ?", (t_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": "Telegram muvaffaqiyatli bog'landi!"})

@app.route('/api/open_free_case', methods=['POST'])
def open_free_case():
    if 'user_id' not in session: return jsonify({"success": False, "msg": "Kirmagansiz!"})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    
    if not user['telegram_id']:
        conn.close()
        return jsonify({"success": False, "msg": "Avval Telegramni ulang va kanalga obuna bo'ling!"})
        
    cursor.execute("SELECT datetime(last_free_case, '+24 hours') > datetime('CURRENT_TIMESTAMP') FROM users WHERE id = ?", (user['id'],))
    res = cursor.fetchone()
    if res and res[0]:
        conn.close()
        return jsonify({"success": False, "msg": "Bepul case'ni har 24 soatda bir marta ochish mumkin!"})
    
    won_item = FREE_CASE_ITEMS[0] if random.random() < 0.0001 else random.choice(FREE_CASE_ITEMS[1:])
    cursor.execute("INSERT INTO inventory (user_id, item_name, item_image, item_price, status) VALUES (?, ?, ?, ?, 'inventory')",
                   (user['id'], won_item['name'], won_item['img'], won_item['price']))
    cursor.execute("UPDATE users SET last_free_case = CURRENT_TIMESTAMP WHERE id = ?", (user['id'],))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "won_item": won_item, "all_items": FREE_CASE_ITEMS})

@app.route('/api/open_case/<case_id>', methods=['POST'])
def open_case_api(case_id):
    if 'user_id' not in session: return jsonify({"success": False, "msg": "Kirmagansiz!"})
    case = CASES[case_id]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    
    if user['balance'] < case['price']:
        conn.close()
        return jsonify({"success": False, "msg": "Balans yetarli emas!"})
        
    cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (case['price'], user['id']))
    won_item = case['items'][0] if random.random() < 0.0001 else random.choice(case['items'][1:])
    
    cursor.execute("INSERT INTO inventory (user_id, item_name, item_image, item_price, status) VALUES (?, ?, ?, ?, 'inventory')",
                   (user['id'], won_item['name'], won_item['img'], won_item['price']))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "won_item": won_item, "all_items": case['items']})

@app.route('/api/inventory')
def get_inventory():
    if 'user_id' not in session: return jsonify({"items": []})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE user_id = ? AND status = 'inventory'", (session['user_id'],))
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"items": items})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
