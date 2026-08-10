from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import random

app = FastAPI(title="Aimdrop API", version="2.5")
DB_NAME = 'aimdrop.db'
CARD_NUMBER = "5614686507631458"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

class UCRequestModel(BaseModel):
    telegram_id: int
    pubg_id: str
    uc_amount: int
    price_som: float

class GamePlayModel(BaseModel):
    telegram_id: int
    bet_amount: float
    game_type: str # mines, tower, crush, roulette

@app.get("/")
def read_root():
    return {"status": "Aimdrop API serveri ishlamoqda 🚀", "donate_card": CARD_NUMBER}

@app.get("/user/{telegram_id}")
def get_user_info(telegram_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return dict(user)

@app.post("/pubg/withdraw")
def withdraw_uc(data: UCRequestModel):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (data.telegram_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    if user['balance'] < data.price_som:
        conn.close()
        raise HTTPException(status_code=400, detail="Balansda yetarli mablag' yo'q!")
    
    try:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (data.price_som, user['id']))
        cursor.execute("INSERT INTO uc_requests (user_id, pubg_id, uc_amount, price_som) VALUES (?, ?, ?, ?)",
                       (user['id'], data.pubg_id, data.uc_amount, data.price_som))
        conn.commit()
        conn.close()
        return {"success": True, "message": "PUBG UC so'rovingiz adminga yuborildi!"}
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/game/play")
def play_mini_game(data: GamePlayModel):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (data.telegram_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    
    if user['balance'] < data.bet_amount:
        conn.close()
        raise HTTPException(status_code=400, detail="Balans yetarli emas!")
    
    won = random.choice([True, False, False])
    multiplier = 2.0 if data.game_type in ["mines", "tower", "crush"] else 1.5
    
    if won:
        win_amount = data.bet_amount * multiplier
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (win_amount - data.bet_amount, user['id']))
        conn.commit()
        conn.close()
        return {"success": True, "won": True, "win_amount": win_amount, "message": f"Yutdingiz: {win_amount} so'm!"}
    else:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (data.bet_amount, user['id']))
        conn.commit()
        conn.close()
        return {"success": True, "won": False, "message": "Yutqazdingiz!"}

@app.get("/cases")
def get_cases():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases WHERE is_active = 1")
    cases = cursor.fetchall()
    conn.close()
    return [dict(row) for row in cases]
