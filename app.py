from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import random

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# O'yinlar va caselar uchun baza
GAME_CONFIG = {
    "mines": {"min_bet": 1, "max_bet": 1000},
    "tower": {"risk": "medium"},
    "crush": {"multiplier": 1.0},
}

@app.post("/game/{game_name}/play")
async def play_game(game_name: str, bet: int):
    # BullDrop logikasi: random yutuq hisoblash
    if game_name == "mines":
        win = bet * random.uniform(1.1, 5.0)
        return {"status": "win", "amount": round(win, 2)}
    return {"status": "lost"}

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "games": GAME_CONFIG})
