from telethon import TelegramClient
from config import API_ID, API_HASH

phone = input("Введи номер телефона (например, 79991112233): ").strip()
client = TelegramClient(f"accounts/{phone}", API_ID, API_HASH)

async def main():
    await client.start()
    me = await client.get_me()
    print(f"✅ Сессия создана: @{me.username or me.id}")
    await client.disconnect()

import asyncio
asyncio.run(main())