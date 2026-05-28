import asyncio, os, re, logging
from pathlib import Path
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

API_ID       = int(os.getenv('TELEGRAM_API_ID', '33839831'))
API_HASH     = os.getenv('TELEGRAM_API_HASH', '2a8b7a66e1f27a359d3ede1c9cdf263b')
PHONE        = os.getenv('TELEGRAM_PHONE', '+41783381835')
CHANNEL      = "oboi_6666"
FOLDER       = "dumy_quotes_images"

IMAGE_EXTS   = ('.jpg', '.jpeg', '.png', '.gif', '.webp')

async def already_exists(msg_id: int) -> bool:
    return any(f"msg{msg_id}_" in f for f in os.listdir(FOLDER))

async def download_images(limit: int = None):
    Path(FOLDER).mkdir(exist_ok=True)
    client = TelegramClient('session', API_ID, API_HASH)

    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE)
        code = input(">>> Enter the Telegram code sent to your app: ").strip()
        await client.sign_in(PHONE, code)
    log.info(f"Logged in as {await client.get_me()}")

    channel = await client.get_entity(f"@{CHANNEL}")
    log.info(f"Channel: {channel.title}")

    downloaded, skipped = 0, 0

    async for msg in client.iter_messages(channel, limit=limit):
        if not msg.media:
            continue

        is_photo = isinstance(msg.media, MessageMediaPhoto)
        is_image_doc = (
            isinstance(msg.media, MessageMediaDocument)
            and msg.file
            and msg.file.mime_type
            and 'image' in msg.file.mime_type
        )

        if not (is_photo or is_image_doc):
            continue

        if await already_exists(msg.id):
            skipped += 1
            continue

        ext = '.jpg' if is_photo else (os.path.splitext(msg.file.name or '')[1] or '.jpg')
        path = os.path.join(FOLDER, f"msg{msg.id}_{downloaded}{ext}")

        try:
            result = await msg.download_media(file=path)
            if result and result.lower().endswith(IMAGE_EXTS):
                downloaded += 1
                if downloaded % 50 == 0:
                    log.info(f"Progress: {downloaded} downloaded...")
            elif result:
                os.remove(result)
        except Exception as e:
            log.error(f"Failed msg {msg.id}: {e}")

    log.info(f"Done — Downloaded: {downloaded}, Skipped: {skipped}, Total in folder: {len(os.listdir(FOLDER))}")
    await client.disconnect()

async def main():
    print("1. All images\n2. Last N images\n3. Exit")
    choice = input("Choose (1-3): ").strip()

    if choice == '1':
        await download_images()
    elif choice == '2':
        n = int(input("How many messages to scan: ").strip())
        await download_images(limit=n)
    else:
        print("Bye!")

if __name__ == "__main__":
    asyncio.run(main())