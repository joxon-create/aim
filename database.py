import sqlite3

def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            site_id TEXT,
            balance REAL DEFAULT 0,
            status TEXT DEFAULT 'pending' -- pending, approved, blocked
        )
    """)
    
    # Adminlar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
    """)
    
    # Kunlik olingan coinlar (limit uchun)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_limits (
            user_id INTEGER,
            amount REAL,
            date TEXT
        )
    """)
    
    # Promokodlar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promos (
            code TEXT PRIMARY KEY,
            promo_type TEXT, -- '20_percent' yoki 'normal'
            max_activations INTEGER,
            current_activations INTEGER DEFAULT 0
        )
    """)
    
    # Depozitlar (20% promo statistikasi uchun)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            user_id INTEGER,
            amount REAL,
            promo_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Case buyumlari
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS case_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL
        )
    """)
    
    conn.commit()
    conn.close()

# Boshlang'ich adminni qo'shish (O'z Telegram IDingizni yozing)
def add_super_admin(admin_id: int):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (admin_id,))
    conn.commit()
    conn.close()
