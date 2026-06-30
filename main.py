import os
import asyncio
from aiohttp import web
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

# Render வெப் சர்வீஸ் எரர் வராமல் தடுக்க டமி வெப் பேஜ்
async def handle(request):
    return web.Response(text="Bot is running perfectly!")

async def main():
    # 1. பாட்டை பின்புலத்தில் ஆன் செய்கிறது
    await app.start()
    print("Bot started successfully!")

    # 2. Render கேட்கும் PORT-ஐ ஆன் செய்கிறது
    server = web.Application()
    server.router.add_get('/', handle)
    runner = web.AppRunner(server)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

    # 3. பாட் தொடர்ந்து ஆன்லைனில் நீடிக்க லூப் செய்கிறது
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
    
