import os
import asyncio
from aiohttp import web
from pyrogram import Client, filters

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
bot_token = os.environ["BOT_TOKEN"]

async def handle(request):
    return web.Response(text="Bot is running perfectly!")

async def main():
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
        await message.delete()

    await app.start()

    server = web.Application()
    server.router.add_get("/", handle)
    runner = web.AppRunner(server)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await app.stop()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
