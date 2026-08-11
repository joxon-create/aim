import re
import requests
from pyrogram import Client, filters

API_ID = 36752136
API_HASH = "f0278f2b7022fe6ad801765c6e396102"

# Render'dagi saytingiz manzili (oxiriga /topup_webhook yozishni unutmang)
SERVER_URL = "https://sizning-sayt.onrender.com/topup_webhook"

app = Client("card_userbot", api_id=API_ID, api_hash=API_HASH)

@app.on_message(filters.chat("CardXabarBot") & filters.incoming)
async def handle_card_sms(client, message):
    text = message.text or ""
    
    if "UZS" in text or "so'm" in text:
        clean_text = text.replace(',', '').replace(' ', '')
        numbers = re.findall(r'\d+', clean_text)
        
        if numbers:
            sum_amount = float(numbers[0])
            uc_amount = (sum_amount / 14000) * 60
            
            data = {"uc": round(uc_amount, 2), "user_id": 1}
            try:
                response = requests.post(SERVER_URL, data=data)
                if response.status_code == 200:
                    print(f"✅ To'lov qabul qilindi: {sum_amount} so'm -> {uc_amount:.1f} UC")
            except Exception as e:
                print(f"❌ Xatolik: {e}")

if __name__ == "__main__":
    print("Userbot ishga tushdi va xabarlarni kuzatmoqda...")
    app.run()
