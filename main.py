import os
from pyrogram import Client, filters

# ரகசிய எண்கள் மற்றும் டோக்கனை Render செட்டிங்ஸ்ல இருந்து பாதுகாப்பா எடுக்கும் முறை
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("பாட் தயார்! ஆியோவை அனுப்புங்க.")

@app.on_message(filters.audio)
async def protect_audio(client, message):
    # நீங்கள் கேட்ட பாதுகாப்பு வசதி (protect_content=True)
    await client.send_audio(
        chat_id=message.chat.id,
        audio=message.audio.file_id,
        protect_content=True
    )

app.run()
