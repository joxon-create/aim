from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3
import random

app = FastAPI(title="AimDrop Pro", version="3.0")
templates = Jinja2Templates(directory="templates")

# Kurs ma'lumotlari: 100 AIMCOIN = 14000 SUM = 60 UC
EXCHANGE_RATE_UC = 60
EXCHANGE_RATE_SUM = 14000

# 10 ta Case va ularning har birida 30 tadan buyum (Foizlar va narxlar bilan)
# 0.1% - eng qimmat buyumlar, qolganlari foiziga qarab taqsimlanadi
CASES = {}
case_prices = [10, 30, 60, 180, 300, 410, 500, 800, 1200, 2000]

for i, price in enumerate(case_prices, 1):
    items = []
    # 30 ta item yaratish
    for j in range(1, 31):
        if j == 1:
            chance = 0.1  # Eng qimmat buyum ehtimoli
            val = price * 10
            name = f"Legendary Skin #{j} (Case {i})"
        elif j <= 5:
            chance = 5.0  # O'rtacha qimmat
            val = price * 2
            name = f"Epic Item #{j} (Case {i})"
        else:
            chance = (100 - 0.1 - (4 * 5.0)) / 25  # Qolgan arzonga foizlar
            val = max(1, int(price * 0.2))
            name = f"Common Item #{j} (Case {i})"
        
        items.append({"name": name, "chance": round(chance, 2), "val": val})
    
    CASES[f"case_{i}"] = {"price": price, "items": items}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "cases": CASES, 
        "uc_rate": EXCHANGE_RATE_UC, 
        "sum_rate": EXCHANGE_RATE_SUM
    })

@app.post("/open-case/{case_key}")
async def open_case(case_key: str):
    if case_key not in CASES:
        raise HTTPException(status_code=404, detail="Case topilmadi")
    
    case = CASES[case_key]
    rand = random.uniform(0, 100)
    cumulative = 0
    
    selected_item = case["items"][-1]
    for item in case["items"]:
        cumulative += item["chance"]
        if rand <= cumulative:
            selected_item = item
            break
            
    return {"status": "success", "item": selected_item["name"], "value": selected_item["val"]}
