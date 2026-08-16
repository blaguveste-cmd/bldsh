import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot
from telethon import TelegramClient, events
from telethon.tl import types
from telethon.utils import get_peer_id

from config import API_ID, API_HASH, RELAYER_SESSION
from database import add_balance, add_star_gift, get_pending_star_request

BASE_DIR = Path(__file__).resolve().parent
ACCOUNTS_DIR = BASE_DIR / "accounts"


def _relayer_session_path() -> str:
    path = ACCOUNTS_DIR / RELAYER_SESSION
    if not path.exists() and not path.with_suffix(path.suffix + ".session").exists():
        alt = BASE_DIR / RELAYER_SESSION
        if alt.exists() or alt.with_suffix(alt.suffix + ".session").exists():
            return str(alt)
    return str(path)


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("stars_listener")
log.setLevel(logging.INFO)
ALLOWED_GIFT_STARS = {15, 25, 50, 100}


def _get_gift_stars(action):
    if action is None:
        return None

    # Пробуем прямо на action (некоторые версии Telethon/Telegram могут хранить параметры здесь).
    for attr in ("stars", "amount", "value"):
        value = getattr(action, attr, None)
        if value is not None:
            try:
                value = int(value)
                if value > 0:
                    return value
            except (TypeError, ValueError):
                pass

    gift = getattr(action, "gift", None)
    if gift is None:
        return None

    for attr in ("stars", "amount", "value"):
        value = getattr(gift, attr, None)
        if value is not None:
            try:
                value = int(value)
                if value > 0:
                    return value
            except (TypeError, ValueError):
                pass

    return None


def _get_sender_id(message, action):
    # Для сервисного сообщения Telegram обычно хранит отправителя в action.from_id.
    for attr in ("from_id", "user_id", "sender_id"):
        from_id = getattr(action, attr, None)
        if from_id is not None:
            try:
                return int(get_peer_id(from_id))
            except Exception:
                pass

    for attr in ("from_id", "user_id", "sender_id"):
        from_id = getattr(message, attr, None)
        if from_id is not None:
            try:
                return int(get_peer_id(from_id))
            except Exception:
                pass

    peer_id = getattr(message, "peer_id", None)
    if peer_id is not None:
        try:
            return int(get_peer_id(peer_id))
        except Exception:
            pass

    return None


def _gift_key(message, peer_id=None):
    message_id = getattr(message, "id", None)
    if message_id is None:
        return None
    if peer_id is None:
        peer_id = getattr(message, "peer_id", None)
    try:
        peer_key = str(get_peer_id(peer_id)) if peer_id is not None else "unknown"
    except Exception:
        peer_key = str(peer_id)
    return f"{peer_key}:{message_id}"


async def _process_message(message, bot: Bot, source="raw"):
    """Обрабатывает обычные и service-сообщения Telegram."""
    action = getattr(message, "action", None)

    if action is None:
        return False

    stars = _get_gift_stars(action)
    if stars is None:
        log.info(
            "⭐ Сообщение msg=%s имеет action %s, но это не StarGift.",
            getattr(message, "id", None),
            type(action).__name__,
        )
        return False

    # Не принимаем возвращённые/отменённые подарки.
    if getattr(action, "refunded", False):
        log.info("⭐ Подарок msg=%s помечен refunded — пропуск.", getattr(message, "id", None))
        return True

    log.info(
        "🎁 Найден MessageActionStarGift | msg=%s | stars=%s | source=%s",
        getattr(message, "id", None), stars, source
    )

    if stars not in ALLOWED_GIFT_STARS:
        log.warning(
            "⭐ Неизвестный номинал подарка: %s ⭐ | msg=%s | допустимо=%s",
            stars, getattr(message, "id", None), sorted(ALLOWED_GIFT_STARS)
        )
        return True

    user_id = _get_sender_id(message, action)
    if not user_id:
        log.warning("⭐ Не удалось определить отправителя | msg=%s", getattr(message, "id", None))
        return True

    request = get_pending_star_request(user_id)
    if not request:
        log.info(
            "⭐ Подарок %s ⭐ от user=%s получен без активной заявки — НЕ зачисляем.",
            stars, user_id
        )
        return True

    key = _gift_key(message)

    result = add_star_gift(user_id=user_id, stars=stars, gift_key=key)
    request_info, credited_rub, received_stars, completed, duplicate = result

    if duplicate:
        log.warning("⭐ Дубликат подарка пропущен: key=%s user=%s", key, user_id)
        return True

    target_stars = int(request[3])

    if completed:
        log.info(
            "✅ STARS ПОПОЛНЕНИЕ | user=%s | +%s ⭐ | всего=%s ⭐ | цель=%s ⭐ | начислено=%s ₽",
            user_id, stars, received_stars, target_stars, credited_rub
        )
        if credited_rub > 0:
            add_balance(user_id, credited_rub)
        try:
            await bot.send_message(
                user_id,
                "✅ <b>Пополнение выполнено!</b>\n\n"
                f"⭐ Получено: <b>{received_stars} Stars</b>\n"
                f"💰 Зачислено: <b>{credited_rub} ₽</b>\n\n"
                "Баланс уже обновлён."
            )
        except Exception:
            log.exception("Не удалось отправить сообщение о завершении user=%s", user_id)
    else:
        remaining = max(0, target_stars - received_stars)
        log.info(
            "⭐ STARS ПРОГРЕСС | user=%s | +%s ⭐ | %s/%s ⭐ | осталось=%s ⭐",
            user_id, stars, received_stars, target_stars, remaining
        )
        try:
            await bot.send_message(
                user_id,
                "🎁 <b>Подарок получен!</b>\n\n"
                f"⭐ Получено: <b>{received_stars}/{target_stars} Stars</b>\n"
                f"⏳ Осталось: <b>{remaining} Stars</b>\n\n"
                "Можешь отправить следующий подарок."
            )
        except Exception:
            log.exception("Не удалось отправить сообщение о прогрессе user=%s", user_id)

    return True


def _extract_message(update):
    # Обычный новый message/service message.
    if isinstance(update, (types.UpdateNewMessage, types.UpdateNewChannelMessage)):
        return getattr(update, "message", None)

    if isinstance(update, (types.UpdateShortMessage, types.UpdateShortChatMessage)):
        return update

    # Некоторые версии Telethon используют контейнеры обновлений.
    if isinstance(update, types.Updates):
        for upd in getattr(update, "updates", []) or []:
            msg = _extract_message(upd)
            if msg is not None:
                return msg

    return None


async def start_stars_listener(bot: Bot):
    session_path = _relayer_session_path()

    if not os.path.exists(session_path) and not os.path.exists(session_path + ".session"):
        log.error("❌ Не найдена сессия релеера: %s", session_path)
        return None

    client = TelegramClient(session_path, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        log.error("❌ Сессия релеера не авторизована.")
        await client.disconnect()
        return None

    me = await client.get_me()
    log.info(
        "⭐ Stars listener запущен | relayer=@%s | id=%s",
        getattr(me, "username", None) or "—",
        getattr(me, "id", None),
    )

    @client.on(events.Raw)
    async def on_raw_update(update):
        try:
            message = _extract_message(update)
            if message is None:
                log.info(
                    "📨 RAW update ignored: no message extracted | update_type=%s",
                    type(update).__name__,
                )
                log.info("📨 RAW dump: %s", repr(update))
                return

            # Нас интересуют входящие сообщения. У service message поле out обычно False.
            if getattr(message, "out", False):
                return

            if isinstance(message, (types.UpdateNewMessage, types.UpdateNewChannelMessage)):
                log.info(
                    "📨 Incoming update message type=%s peer=%s action=%s",
                    type(message).__name__,
                    getattr(message, 'peer_id', None),
                    type(getattr(message, 'action', None)).__name__ if getattr(message, 'action', None) is not None else None,
                )

            # Специально дампим короткие сообщения, чтобы понять структуру UpdateShortMessage
            if isinstance(message, (types.UpdateShortMessage, types.UpdateShortChatMessage)):
                try:
                    body = getattr(message, 'message', None) or getattr(message, 'body', None)
                except Exception:
                    body = None
                log.info("📨 SHORT MSG received: user=%s text=%s repr=%s", getattr(message, 'user_id', None), body, repr(message))

            action = getattr(message, "action", None)
            stars = _get_gift_stars(action) if action is not None else None
            if stars is None:
                action_info = None
                if action is not None:
                    action_info = {
                        'type': type(action).__name__,
                        'stars': getattr(action, 'stars', None),
                        'amount': getattr(action, 'amount', None),
                        'gift': bool(getattr(action, 'gift', None)),
                    }
                log.info(
                    "📨 RAW update ignored: not StarGift | msg_type=%s action=%s info=%s",
                    type(message).__name__,
                    type(action).__name__ if action is not None else None,
                    action_info,
                )
                try:
                    log.info("📨 message dump: %s", repr(message))
                except Exception:
                    log.info("📨 message dump unavailable for type %s", type(message).__name__)
                return

            log.info(
                "📨 RAW STAR UPDATE | type=%s | msg=%s | peer=%s | from=%s | stars=%s | action=%s",
                type(update).__name__,
                getattr(message, "id", None),
                getattr(message, "peer_id", None),
                getattr(action, "from_id", None),
                stars,
                type(action).__name__,
            )
            await _process_message(message, bot, source=type(update).__name__)

        except Exception:
            log.exception("❌ Ошибка обработки RAW Telegram update")

    # Оставляем NewMessage как fallback для версий Telethon,
    # где событие удобнее преобразовать через EventBuilder.
    @client.on(events.NewMessage(incoming=True))
    async def on_new_message(event):
        try:
            action = getattr(event.message, "action", None)
            if action is not None:
                stars = _get_gift_stars(action)
                if stars is not None:
                    await _process_message(event.message, bot, source="NewMessage")
                    return
            # Для отладки выводим текст и репрезентацию сообщения
            try:
                text = getattr(event.message, 'message', None) or getattr(event.message, 'text', None)
            except Exception:
                text = None
            action_info = None
            if action is not None:
                action_info = {
                    'type': type(action).__name__,
                    'stars': getattr(action, 'stars', None),
                    'amount': getattr(action, 'amount', None),
                    'gift': bool(getattr(action, 'gift', None)),
                }
            log.info("📝 NewMessage ignored: text=%s action=%s info=%s repr=%s", text, type(action).__name__ if action is not None else None, action_info, repr(event.message))
        except Exception:
            log.exception("❌ Ошибка fallback-обработчика Star Gift")

    log.info("⭐ Stars listener: ожидаю входящие подарки...")
    return client


async def run_stars_listener_forever(bot: Bot):
    while True:
        client = None
        try:
            client = await start_stars_listener(bot)

            if client is None:
                await asyncio.sleep(15)
                continue

            await client.run_until_disconnected()

        except asyncio.CancelledError:
            if client:
                await client.disconnect()
            raise

        except Exception:
            log.exception("❌ Stars listener остановился, повтор через 5 секунд")

        finally:
            if client:
                try:
                    await client.disconnect()
                except Exception:
                    pass

        await asyncio.sleep(5)
