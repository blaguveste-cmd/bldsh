import asyncio
from datetime import datetime, timezone
from pathlib import Path
from telethon import TelegramClient

from config import API_ID, API_HASH

BASE_DIR = Path(__file__).resolve().parent
ACCOUNTS_DIR = BASE_DIR / "accounts"


def _session_path(phone_clean: str) -> str:
    if not ACCOUNTS_DIR.exists():
        ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
    return str(ACCOUNTS_DIR / f"{phone_clean}.session")


async def check_session_alive(phone_clean: str, timeout: int = 20) -> bool:
    """
    Быстрая проверка: сессия существует и авторизована.
    Возвращает True, если аккаунт живой.
    """
    session_path = _session_path(phone_clean)
    if not __import__("os").path.exists(session_path):
        print(f"⚠️ Сессия не найдена: {session_path}")
        return False

    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await asyncio.wait_for(client.connect(), timeout=timeout)
        await asyncio.wait_for(client.get_me(), timeout=timeout)
        alive = await client.is_user_authorized()
        if not alive:
            print(f"⚠️ Сессия найдена, но аккаунт не авторизован: +{phone_clean}")
        return bool(alive)
    except asyncio.TimeoutError:
        print(f"⚠️ Таймаут проверки сессии +{phone_clean} ({timeout}с)")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка проверки сессии +{phone_clean}: {type(e).__name__}: {e}")
        return False
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def listen_for_telegram_code(phone_clean: str, timeout: int = 150) -> str:
    """
    Подключается к сессии и ждет код авторизации от Telegram (777000).
    Принимает код ТОЛЬКО если сообщение пришло в течение последних секунд.
    """
    session_path = _session_path(phone_clean)
    client = TelegramClient(session_path, API_ID, API_HASH)

    try:
        await asyncio.wait_for(client.connect(), timeout=30)
        await asyncio.wait_for(client.get_me(), timeout=30)

        if not await client.is_user_authorized():
            print(f"⚠️ Сессия +{phone_clean} не авторизована!")
            await client.disconnect()
            return ""

        start_time = datetime.now(timezone.utc)
        print(f"🚀 Успешно зашли в аккаунт +{phone_clean}. Время старта: {start_time}. Ожидаем код...")

        for _ in range(24):
            await asyncio.sleep(5)
            async for message in client.iter_messages(777000, limit=3):
                if message and message.text and message.date:
                    if message.date > start_time:
                        msg_text = message.text.lower()

                        if "код" in msg_text or "code" in msg_text:
                            words = message.text.split()
                            for word in words:
                                clean_word = "".join(filter(str.isdigit, word))
                                if len(clean_word) == 5:
                                    print(f"✅ Перехвачен СВЕЖИЙ код: {clean_word}")
                                    await client.disconnect()
                                    return clean_word

    except asyncio.TimeoutError:
        print(f"⏰ Таймаут подключения к сессии +{phone_clean}")
    except Exception as e:
        print(f"❌ Ошибка в скрипте перехвата: {e}")
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass

    return ""
