from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import random

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Case ichidagi 30 ta item (Namuna)
def generate_items():
    items = [{"name": f"Item {i}", "chance": 0.1 if i == 1 else 3.4, "val": i * 10} for i in range(1, 31)]
    return items

CASES = {f"case_{i}": {"price": i*50, "items": generate_items()} for i in range(1, 11)}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "cases": CASES})

@app.post("/open/{case_id}")
async def open_case(case_id: str):
    case = CASES.get(case_id)
    items = case["items"]
    # BullDrop probabillity logic
    result = random.choices(items, weights=[i['chance'] for i in items], k=1)[0]
    return {"item": result["name"], "price": result["val"]}
