import asyncio
from telethon import TelegramClient

from config import API_ID, API_HASH

SESSION = "accounts/relayer.session"   # путь к файлу

async def main():
    print(f"Проверяю: {SESSION}")
    client = TelegramClient(SESSION, API_ID, API_HASH)

    try:
        await client.connect()
        if await client.is_user_authorized():
            me = await client.get_me()
            print("✅ Сессия ЖИВАЯ")
            print(f"   ID: {me.id}")
            print(f"   Имя: {me.first_name}")
            print(f"   Username: @{me.username}" if me.username else "   Username: нет")
        else:
            print("❌ Сессия МЁРТВАЯ — нужно создавать заново")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("   Сессия скорее всего битая или аккаунт забанен")
    finally:
        await client.disconnect()

asyncio.run(main())