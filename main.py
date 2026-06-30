import os
from pyrogram import Client, filters

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

app = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("பாட் ready. Audio அனுப்புங்க.")

@app.on_message(filters.audio)
async def protect_audio(client, message):
    await client.send_audio(
        chat_id=message.chat.id,
        audio=message.audio.file_id,
        protect_content=True
    )
    await message.delete()

app.run()
