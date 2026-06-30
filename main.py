import os
import asyncio
import sqlite3
from datetime import datetime, timezone

from aiohttp import web
from pyrogram import Client, filters
from pyrogram.errors import RPCError

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

def parse_id_set(value: str):
    ids = set()
    for part in value.replace(",", " ").split():
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids

OWNER_IDS = parse_id_set(os.getenv("OWNER_IDS", ""))
ADMIN_IDS = parse_id_set(os.getenv("ADMIN_IDS", ""))
SUBADMIN_IDS = parse_id_set(os.getenv("SUBADMIN_IDS", ""))

MANAGER_IDS = OWNER_IDS | ADMIN_IDS | SUBADMIN_IDS
DB_PATH = os.getenv("DB_PATH", "bot.db")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS approved_users (
            user_id INTEGER PRIMARY KEY,
            approved_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS download_users (
            user_id INTEGER PRIMARY KEY,
            granted_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_users (
            user_id INTEGER PRIMARY KEY,
            requested_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS media_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            file_id TEXT NOT NULL,
            caption TEXT,
            added_by INTEGER NOT NULL,
            added_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def is_manager(user_id: int) -> bool:
    return user_id in MANAGER_IDS


def is_approved(user_id: int) -> bool:
    if is_manager(user_id):
        return True
    conn = db()
    cur = conn.execute(
        "SELECT 1 FROM approved_users WHERE user_id = ? LIMIT 1",
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row is not None


def can_download(user_id: int) -> bool:
    if is_manager(user_id):
        return True
    conn = db()
    cur = conn.execute(
        "SELECT 1 FROM download_users WHERE user_id = ? LIMIT 1",
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row is not None


def add_pending(user_id: int):
    conn = db()
    conn.execute(
        "INSERT OR REPLACE INTO pending_users(user_id, requested_at) VALUES(?, ?)",
        (user_id, now_utc()),
    )
    conn.commit()
    conn.close()


def approve(user_id: int):
    conn = db()
    conn.execute(
        "INSERT OR REPLACE INTO approved_users(user_id, approved_at) VALUES(?, ?)",
        (user_id, now_utc()),
    )
    conn.execute("DELETE FROM pending_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def deny(user_id: int):
    conn = db()
    conn.execute("DELETE FROM approved_users WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM pending_users WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM download_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def grant_download(user_id: int):
    conn = db()
    conn.execute(
        "INSERT OR REPLACE INTO download_users(user_id, granted_at) VALUES(?, ?)",
        (user_id, now_utc()),
    )
    conn.commit()
    conn.close()


def revoke_download(user_id: int):
    conn = db()
    conn.execute("DELETE FROM download_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def save_media(kind: str, file_id: str, caption: str | None, added_by: int):
    conn = db()
    conn.execute(
        """
        INSERT INTO media_items(kind, file_id, caption, added_by, added_at)
        VALUES(?, ?, ?, ?, ?)
        """,
        (kind, file_id, caption, added_by, now_utc()),
    )
    conn.commit()
    conn.close()


def latest_media():
    conn = db()
    cur = conn.execute(
        """
        SELECT kind, file_id, caption, added_by, added_at
        FROM media_items
        ORDER BY id DESC
        LIMIT 1
        """
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "kind": row[0],
        "file_id": row[1],
        "caption": row[2],
        "added_by": row[3],
        "added_at": row[4],
    }


def parse_target_user_id(message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id

    if message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) == 2 and parts[1].strip().isdigit():
            return int(parts[1].strip())

    return None


async def send_latest_to_user(client: Client, user_id: int, protected: bool):
    media = latest_media()
    if not media:
        return False

    kwargs = {
        "chat_id": user_id,
        "caption": media["caption"] or None,
    }
    if protected:
        kwargs["protect_content"] = True

    if media["kind"] == "audio":
        await client.send_audio(audio=media["file_id"], **kwargs)
    elif media["kind"] == "voice":
        await client.send_voice(voice=media["file_id"], **kwargs)
    else:
        return False

    return True


async def broadcast_latest(client: Client):
    media = latest_media()
    if not media:
        return 0

    conn = db()
    cur = conn.execute("SELECT user_id FROM approved_users")
    approved_ids = [row[0] for row in cur.fetchall()]
    conn.close()

    targets = sorted(set(approved_ids) | MANAGER_IDS)
    sent = 0

    for uid in targets:
        try:
            ok = await send_latest_to_user(client, uid, protected=True)
            if ok:
                sent += 1
        except RPCError:
            pass

    return sent


app = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


@app.on_message(filters.command("start"))
async def start_handler(client, message):
    user = message.from_user
    if not user:
        return

    if is_manager(user.id):
        await message.reply_text(
            "Owner/Admin/Subadmin ready.\n\n"
            "Commands:\n"
            "/request_access - user request\n"
            "/approve or /deny - reply to user or give ID\n"
            "/grantdownload or /revokedownload - reply to user or give ID\n"
            "/publish - reply to an audio/voice message\n"
            "/play - send protected latest media\n"
            "/download - send unprotected latest media if allowed\n"
        )
        return

    if is_approved(user.id):
        await message.reply_text(
            "Approved. /play is ready.\n"
            "Download only if admin grants it."
        )
    else:
        await message.reply_text(
            "Access இல்லை.\n"
            "Approval request அனுப்ப /request_access use பண்ணுங்க."
        )


@app.on_message(filters.command("request_access"))
async def request_access_handler(client, message):
    user = message.from_user
    if not user:
        return

    if is_approved(user.id):
        await message.reply_text("Already approved.")
        return

    add_pending(user.id)

    for manager_id in MANAGER_IDS:
        try:
            await client.send_message(
                manager_id,
                f"New access request\nUser ID: {user.id}\nName: {user.first_name or '-'}",
            )
        except RPCError:
            pass

    await message.reply_text("Request sent. Wait for approval.")


@app.on_message(filters.command("approve"))
async def approve_handler(client, message):
    user = message.from_user
    if not user or not is_manager(user.id):
        return

    target_id = parse_target_user_id(message)
    if not target_id:
        await message.reply_text("Usage: /approve <user_id> or reply /approve")
        return

    approve(target_id)
    await message.reply_text(f"Approved: {target_id}")


@app.on_message(filters.command("deny"))
async def deny_handler(client, message):
    user = message.from_user
    if not user or not is_manager(user.id):
        return

    target_id = parse_target_user_id(message)
    if not target_id:
        await message.reply_text("Usage: /deny <user_id> or reply /deny")
        return

    deny(target_id)
    await message.reply_text(f"Denied: {target_id}")


@app.on_message(filters.command("grantdownload"))
async def grant_download_handler(client, message):
    user = message.from_user
    if not user or not is_manager(user.id):
        return

    target_id = parse_target_user_id(message)
    if not target_id:
        await message.reply_text("Usage: /grantdownload <user_id> or reply /grantdownload")
        return

    grant_download(target_id)
    await message.reply_text(f"Download allowed: {target_id}")


@app.on_message(filters.command("revokedownload"))
async def revoke_download_handler(client, message):
    user = message.from_user
    if not user or not is_manager(user.id):
        return

    target_id = parse_target_user_id(message)
    if not target_id:
        await message.reply_text("Usage: /revokedownload <user_id> or reply /revokedownload")
        return

    revoke_download(target_id)
    await message.reply_text(f"Download revoked: {target_id}")


@app.on_message(filters.command("publish"))
async def publish_handler(client, message):
    user = message.from_user
    if not user or not is_manager(user.id):
        return

    src = message.reply_to_message
    if not src:
        await message.reply_text("Reply to an audio/voice message with /publish")
        return

    kind = None
    file_id = None
    caption = src.caption

    if src.audio:
        kind = "audio"
        file_id = src.audio.file_id
    elif src.voice:
        kind = "voice"
        file_id = src.voice.file_id
    else:
        await message.reply_text("Reply must be audio or voice.")
        return

    save_media(kind, file_id, caption, user.id)
    await message.reply_text("Saved. Broadcasting protected copy...")

    sent = await broadcast_latest(client)
    await message.reply_text(f"Broadcast done. Sent to {sent} users.")


@app.on_message(filters.command("play"))
async def play_handler(client, message):
    user = message.from_user
    if not user:
        return

    if not is_approved(user.id):
        await message.reply_text("Access இல்லை. முதலில் /request_access.")
        return

    ok = await send_latest_to_user(client, user.id, protected=True)
    if not ok:
        await message.reply_text("No media published yet.")


@app.on_message(filters.command("download"))
async def download_handler(client, message):
    user = message.from_user
    if not user:
        return

    if not is_approved(user.id):
        await message.reply_text("Access இல்லை.")
        return

    if not can_download(user.id):
        await message.reply_text("Download permission இல்லை.")
        return

    ok = await send_latest_to_user(client, user.id, protected=False)
    if not ok:
        await message.reply_text("No media published yet.")


async def health(request):
    return web.Response(text="OK")


async def run_web_server():
    server = web.Application()
    server.router.add_get("/", health)

    runner = web.AppRunner(server)
    await runner.setup()

    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    return runner


async def main():
    runner = await run_web_server()
    await app.start()
    print("Bot started")

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await app.stop()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
