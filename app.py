import random
import sqlite3
import requests
from flask import Flask, jsonify, session, request

app = Flask(__name__)
app.secret_key = 'aimdrop_ultimate_secure_2026'

# --- KONFIGURATSIYA ---
BOT_TOKEN = '8253855521:AAHSIzRLRV_v2IqZQXeL32JJxZppLA1KwoY' # BotFather'dan olingan token
ADMIN_ID = '8692517241' # Xabarlar sizga kelishi uchun ID

# --- 1. TELEGRAM XABAR YUBORISH FUNKSIYASI ---
def send_telegram(chat_id, text):
    if not chat_id: return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'})
    except Exception as e:
        print(f"Telegram error: {e}")

# --- 2. BAZA VA CASE GENERATOR ---
def get_db():
    conn = sqlite3.connect('aimdrop_ecosystem.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# 20 ta Case va 30 tadan buyum generatsiyasi
CASE_NAMES = ['Beginner', 'Supply', 'Classic', 'Premium', 'Heroic', 'Neon', 'Cyber', 'Royal', 
              'Godzilla', 'Kong', 'Venom', 'Joker', 'Ghost', 'Titan', 'Apex', 'Blood', 
              'Mummy', 'Poseidon', 'Pharaoh', 'Glacier']
CASES = {}
for i in range(1, 21):
    case_id = f'case_{i}'
    price = round(20.0 + (i * 45.0), 1)
    items = [{'name': f'{CASE_NAMES[i-1]} Jackpot', 'price': price * 50, 'chance': 0.005}]
    for j in range(1, 31):
        items.append({'name': f'{CASE_NAMES[i-1]} Skin #{j}', 'price': round(price * random.uniform(0.1, 1.5), 2), 'chance': 0.995/30})
    CASES[case_id] = {'name': f'AimDrop {CASE_NAMES[i-1]} Box', 'price': price, 'items': items}

# --- 3. ASOSIY LOGIKA (UC YECHISH VA XABARLASH) ---
@app.route('/api/open_case/<case_id>', methods=['POST'])
def open_case(case_id):
    if 'user_id' not in session: return jsonify({'success': False, 'msg': 'Tizimga kiring!'})
    case = CASES.get(case_id)
    if not case: return jsonify({'success': False, 'msg': 'Case topilmadi!'})
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    if user['balance'] < case['price']:
        conn.close()
        return jsonify({'success': False, 'msg': 'Balans yetarli emas!'})

    # Yutuqni aniqlash
    rand = random.random()
    cumulative = 0
    won_item = case['items'][-1]
    for item in case['items']:
        cumulative += item['chance']
        if rand <= cumulative:
            won_item = item
            break

    # Balansni yangilash
    new_balance = round(user['balance'] - case['price'], 2)
    conn.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user['id']))
    conn.execute("INSERT INTO inventory (user_id, item_name, item_price) VALUES (?, ?, ?)", 
                 (user['id'], won_item['name'], won_item['price']))
    conn.commit()
    conn.close()

    # --- TELEGRAM XABARLAR ---
    # Foydalanuvchiga
    if user['telegram_id']:
        msg = (f"🔔 <b>YUTUQ!</b>\n📦 Case: {case['name']}\n💎 Yutuq: {won_item['name']}\n"
               f"💰 Yechildi: {case['price']} UC\n💳 Balans: {new_balance} UC")
        send_telegram(user['telegram_id'], msg)
    
    # Sizga (Admin)
    admin_msg = (f"🚨 <b>YANGI YECHIM</b>\n👤 User: {user['username']}\n"
                 f"📦 Case: {case['name']}\n💰 Yechildi: {case['price']} UC\n"
                 f"💎 Yutuq: {won_item['name']}")
    send_telegram(ADMIN_ID, admin_msg)

    return jsonify({'success': True, 'won_item': won_item['name'], 'balance': new_balance})

if __name__ == '__main__':
    app.run(debug=True)
