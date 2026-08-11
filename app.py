from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import random

app = FastAPI()
templates = Jinja2Templates(directory="templates")

CASES = {
    "case_1": {
        "name": "Starter Case",
        "price": 10,
        "items": [{"name": f"Skin Item {i}", "chance": 3.3, "val": i * 5} for i in range(1, 31)]
    },
    "case_2": {
        "name": "Pro Case",
        "price": 30,
        "items": [{"name": f"Epic Item {i}", "chance": 3.3, "val": i * 10} for i in range(1, 31)]
    }
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "cases": CASES})

@app.post("/open/{case_id}")
async def open_case(case_id: str):
    case = CASES.get(case_id)
    if not case:
        return {"error": "Case topilmadi"}
    items = case["items"]
    result = random.choices(items, weights=[i['chance'] for i in items], k=1)[0]
    return {"item": result["name"], "price": result["val"]}
