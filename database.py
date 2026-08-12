import sqlite3

def init_db():
    conn = sqlite3.connect('pubg_ecosystem.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            username TEXT,
            balance REAL DEFAULT 0.0,
            demo_balance REAL DEFAULT 1000.0,
            is_partner INTEGER DEFAULT 0,
            referrer_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Inventar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_name TEXT,
            item_image TEXT,
            item_price REAL,
            status TEXT DEFAULT 'inventory' -- 'inventory' yoki 'sold'
        )
    ''')
    
    # Promo-kodlar jadvali
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
    
    # Promo ishlatganlar tarixi (24 soatlik cheklov uchun)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promo_history (
            user_id INTEGER,
            promo_id INTEGER,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
