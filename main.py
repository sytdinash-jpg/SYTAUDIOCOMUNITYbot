import os
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

# வெப் சர்வீஸ் எரர் வராமல் தடுக்க இந்த ஒரு வரி மிக முக்கியம்!
os.system(f"python3 -m http.server {os.environ.get('PORT', '8080')}")

app.run()
