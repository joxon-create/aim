from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import random

app = FastAPI()

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
async def index():
    # Jinja2 o'rniga to'g'ridan-to'g'ri HTML qaytarish — xatolikni 100% yo'qotadi
    html_content = """
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <title>AimDrop Pro</title>
        <style>
            body { background: #0f1923; color: white; font-family: sans-serif; text-align: center; padding: 50px; }
            .grid { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }
            .case-card { background: #1a2d3d; border: 2px solid #3d5a73; padding: 20px; border-radius: 10px; cursor: pointer; width: 200px; }
            .case-card:hover { border-color: gold; }
            #result { margin-top: 30px; font-size: 24px; color: gold; }
        </style>
    </head>
    <body>
        <h1>AIMDROP PRO</h1>
        <div class="grid">
            <div class="case-card" onclick="openCase('case_1')">
                <h3>Starter Case</h3>
                <p>Narxi: 10 UC</p>
            </div>
            <div class="case-card" onclick="openCase('case_2')">
                <h3>Pro Case</h3>
                <p>Narxi: 30 UC</p>
            </div>
        </div>
        
        <div id="result"></div>

        <script>
            async function openCase(caseId) {
                const response = await fetch(`/open/${caseId}`, { method: 'POST' });
                const resData = await response.json();
                if(resData.item) {
                    document.getElementById('result').innerText = `Yutdingiz: ${resData.item} (${resData.price} UC)`;
                } else {
                    document.getElementById('result').innerText = "Xatolik yuz berdi!";
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/open/{case_id}")
async def open_case(case_id: str):
    case = CASES.get(case_id)
    if not case:
        return {"error": "Case topilmadi"}
    items = case["items"]
    result = random.choices(items, weights=[i['chance'] for i in items], k=1)[0]
    return {"item": result["name"], "price": result["val"]}
