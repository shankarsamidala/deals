import asyncio
import logging
import re
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import User, Channel
from telethon.errors import FloodWaitError

# -------------------- CONFIG --------------------
api_id = 23518980
api_hash = '61eb850c0dddf5938ad8e6fb40c4b6f6'
session_name = "my_session"  # ✅ Only one session file used

# -------------------- LOGGING --------------------
logging.basicConfig(
    level=logging.INFO,
    format="🕒 %(asctime)s | 📘 %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("TelegramPeerListener")

# -------------------- TELEGRAM CLIENT --------------------
client = TelegramClient(session_name, api_id, api_hash)

# Robust URL regex pattern (RFC 3986 simplified)
URL_REGEX = re.compile(
    r'(?i)\b((?:https?://|ftp://|www\d{0,3}[.]|'
    r'[a-z0-9.\-]+[.][a-z]{2,4}/)'
    r'(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+'
    r'(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))'
)

def extract_urls(text):
    matches = URL_REGEX.findall(text)
    return [match[0] for match in matches] if matches else []

@client.on(events.NewMessage)
async def handler(event):
    try:
        # Get sender info directly without caching
        sender = await event.get_sender()
        if isinstance(sender, User):
            sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip() or sender.username or "Unknown User"
        elif isinstance(sender, Channel):
            sender_name = getattr(sender, "title", "Unknown Channel")
        else:
            sender_name = getattr(sender, "username", "Unknown Sender")

        chat = await event.get_chat()
        chat_title = getattr(chat, "title", "Unknown Chat")
        chat_id = event.chat_id

        text = event.message.text or "<no text>"
        urls = extract_urls(text)

        message_time = event.message.date.replace(tzinfo=None)
        received_time = datetime.utcnow()
        delay = (received_time - message_time).total_seconds()

        log.info(f"\n📢 From: {sender_name} (Chat: {chat_title}, ID: {chat_id})")
        log.info(f"📩 Message: {text[:100]}{'...' if len(text) > 100 else ''}")
        log.info(f"🕒 Sent at:     {message_time}")
        log.info(f"🕒 Received at: {received_time}")
        log.info(f"⏱️ Delay:       {delay:.2f} seconds")

        if urls:
            log.info(f"🔗 URLs: {', '.join(urls)}")

        # Mark message as read ASAP
        await client.send_read_acknowledge(chat_id, event.message)
        log.info("✅ Marked as read")

    except FloodWaitError as e:
        log.warning(f"❌ Flood wait error encountered. Sleeping for {e.seconds} seconds.")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        log.error(f"❌ Error handling message: {e}")

async def main():
    log.info("🚀 Starting peer-based Telegram listener without caching for fastest processing...")
    await client.start()
    log.info("👂 Listening for new messages...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
