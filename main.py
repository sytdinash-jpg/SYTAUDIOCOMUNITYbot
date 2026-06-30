from pyrogram import Client, filters

# இங்க உங்களோட API ID, HASH, TOKEN ஆகியவற்றை சரியாக மாற்றுங்கள்
api_id = 36166001
api_hash = "3fa97b32387a32b43a4074122b32de48"
bot_token = "8974319677:AAG8hsnNN0HjiykXoYIgC7p9ijLPcz2jPy0"

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

app.run()
