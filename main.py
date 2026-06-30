import os
import asyncio
from pyrogram import Client, filters

# ரகசிய எண்கள்
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("பாட் தயார்! ஆடியோவை அனுப்புங்க.")

@app.on_message(filters.audio)
async def protect_audio(client, message):
    await client.send_audio(
        chat_id=message.chat.id,
        audio=message.audio.file_id,
        protect_content=True
    )

async def start_services():
    # 1. பாட்டை ஆன் செய்கிறது
    await app.start()
    
    # 2. Render கேட்கும் வெப் போர்ட்டை எரர் வராமல் பின்புலத்தில் ஆன் செய்கிறது
    os.system(f"python3 -m http.server {os.environ.get('PORT', '8080')} &")
    
    # 3. பாட் தொடர்ந்து ஆன்லைனில் நீடிக்க லூப் செய்கிறது
    while True:
        await asyncio.sleep(10)

if __name__ == "__main__":
    # புதிய பைதான் 3.14 வெர்ஷனுக்கான லூப் செட்டிங்
    asyncio.run(start_services())
    
