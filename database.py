import sqlite3

DB_NAME = 'aimdrop.db'

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Foydalanuvchilar
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        balance REAL DEFAULT 0.00,
        demo_balance REAL DEFAULT 0.00,
        is_partner INTEGER DEFAULT 0,
        partner_requested INTEGER DEFAULT 0,
        pass_level INTEGER DEFAULT 1,
        pass_xp INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 2. Adminlar
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        added_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 3. Qutilar (Cases)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        image_url TEXT,
        is_free INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    )
    ''')
    
    # 4. Buyumlar (Skins)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        image_url TEXT,
        drop_chance REAL NOT NULL,
        FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
    )
    ''')
    
    # 5. PUBG UC chiqarish so'rovlari
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS uc_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        pubg_id TEXT NOT NULL,
        uc_amount INTEGER NOT NULL,
        price_som REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # 6. Promo-kodlar
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS promo_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        reward_amount REAL NOT NULL,
        max_uses INTEGER DEFAULT 100,
        used_count INTEGER DEFAULT 0,
        is_partner INTEGER DEFAULT 0,
        partner_id INTEGER,
        total_donated REAL DEFAULT 0.00,
        FOREIGN KEY (partner_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_promos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        promo_id INTEGER,
        UNIQUE(user_id, promo_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (promo_id) REFERENCES promo_codes(id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    conn.close()

create_tables()

def is_admin(telegram_id: int) -> bool:
    if telegram_id == 8692517241:
        return True
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE telegram_id = ?", (telegram_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None
