from telethon import TelegramClient

from config import API_ID, API_HASH

client = TelegramClient("accounts/relayer", API_ID, API_HASH)

async def main():
    await client.start()
    me = await client.get_me()
    print(f"✅ Готово! Аккаунт: @{me.username or me.id}")
    await client.disconnect()

import asyncio
asyncio.run(main())