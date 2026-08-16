import asyncio
import os
import time
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile, BotCommand, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ForceReply
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import sys
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

BASE_DIR = Path(__file__).resolve().parent
ACCOUNTS_DIR = BASE_DIR / "accounts"
SOLD_ACCOUNTS_DIR = BASE_DIR / "sold_accounts"


def _session_path(phone_clean: str) -> str:
    if not ACCOUNTS_DIR.exists():
        ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
    return str(ACCOUNTS_DIR / f"{phone_clean}.session")


def _sold_session_path(phone_clean: str) -> str:
    if not SOLD_ACCOUNTS_DIR.exists():
        SOLD_ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
    return str(SOLD_ACCOUNTS_DIR / f"{phone_clean}.session")

from telegram_auth import listen_for_telegram_code, check_session_alive
from database import get_pending_payments
from config import BOT_TOKEN, ADMIN_ID, RUB_PAYMENT_DETAILS, STARS_RATE, RELAYER_USERNAME, REFUND_PERCENT
from states import AdminStates, PaymentStates, GiftStates, TransferStates
from keyboards import (
    main_keyboard, back_keyboard, products_keyboard, buy_product_keyboard,
    admin_keyboard, delete_keyboard, deposit_methods_keyboard, pay_invoice_keyboard,
    admin_manual_payment_keyboard, after_purchase_keyboard, subscribe_keyboard,
)
import texts as t

from database import (
    create_refund_request, get_refund_request, approve_refund, reject_refund,
    get_pending_refund_requests,
    add_user, get_balance, add_balance, get_user_by_username, add_payment, get_payment, create_star_request,
    add_star_gift, get_pending_star_request, get_last_star_request, cancel_pending_star_requests,
    complete_payment, get_products, get_product, add_product,
    sell_product, delete_product, add_order, get_orders,
    create_manual_payment, get_manual_payment, approve_manual_payment, reject_manual_payment,
    add_getsms_order, get_getsms_order, get_user_getsms_orders, update_getsms_order,
    get_all_user_ids,
)
from cryptobot import create_invoice, check_invoice


if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN is not set. Create a .env file or set BOT_TOKEN environment variable. See .env.example.")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

PHOTO_PATH = "start.jpg"

# Постоянные картинки разделов (положи файлы в папку бота)
SECTION_PHOTOS = {
    "start": "start.jpg",
    "catalog": "catalog.jpg",
    "balance": "balance.jpg",
    "profile": "profile.jpg",
    "info": "info.jpg",
    "orders": "orders.jpg",
    "support": "support.jpg",
}


def section_photo(name: str) -> str | None:
    """Возвращает путь к картинке раздела, если файл есть."""
    path = SECTION_PHOTOS.get(name)
    if path and os.path.isfile(path):
        return path
    return None


# Защита от двойной покупки
_processing_products: set[int] = set()
_processing_users: set[int] = set()


def log(msg: str):
    """Простое логирование в консоль."""
    from datetime import datetime
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def main_text(user_id, first_name=None):
    return t.main_menu_text(get_balance(user_id), first_name)


async def show_section(callback: CallbackQuery, text: str, reply_markup=None, section: str | None = None):
    """
    Обновляет ОДНО И ТО ЖЕ сообщение на месте.
    Ничего не удаляет и не шлёт новое, если можно отредактировать.
    """
    msg = callback.message
    photo_path = section_photo(section) if section else None

    # 1) Есть картинка раздела — меняем media + caption
    if photo_path:
        try:
            await msg.edit_media(
                media=InputMediaPhoto(media=FSInputFile(photo_path), caption=text),
                reply_markup=reply_markup,
            )
            return
        except Exception:
            # Возможно то же самое фото / сообщение без фото — пробуем caption
            try:
                if msg.photo:
                    await msg.edit_caption(caption=text, reply_markup=reply_markup)
                    return
            except Exception:
                pass
            try:
                await msg.edit_text(text=text, reply_markup=reply_markup)
                return
            except Exception:
                pass
            # Совсем крайний случай
            try:
                await callback.message.answer_photo(
                    FSInputFile(photo_path), caption=text, reply_markup=reply_markup
                )
            except Exception:
                await callback.message.answer(text, reply_markup=reply_markup)
            return

    # 2) Без картинки раздела — только текст/caption
    await safe_edit(callback, text, reply_markup)


async def safe_edit(callback: CallbackQuery, text: str, reply_markup=None):
    """
    Редактирует текущее сообщение на месте. Без удаления.
    """
    msg = callback.message
    try:
        if msg.photo:
            await msg.edit_caption(caption=text, reply_markup=reply_markup)
            return
    except Exception:
        pass

    try:
        await msg.edit_text(text=text, reply_markup=reply_markup)
        return
    except Exception:
        pass

    # Только если edit совсем невозможен (например, сообщение слишком старое)
    try:
        await callback.message.answer(text, reply_markup=reply_markup)
    except Exception:
        pass


@dp.message(Command("start"))
async def start(message: Message):
    is_new = add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    text = main_text(message.from_user.id, message.from_user.first_name)
    try:
        await message.answer_photo(FSInputFile(PHOTO_PATH), caption=text, reply_markup=main_keyboard)
    except Exception:
        await message.answer(text, reply_markup=main_keyboard)

    # При первом заходе предлагаем подписаться на канал
    if is_new:
        await message.answer(
            t.subscribe_prompt_text(),
            reply_markup=subscribe_keyboard(),
        )


@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(t.admin_panel_text(), reply_markup=admin_keyboard)


@dp.callback_query(F.data == "broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.broadcast)
    await callback.message.answer(
        "<b>📢 Рассылка</b>\n\n"
        "Отправь сообщение, которое нужно разослать всем пользователям.\n"
        "Поддерживается текст или фото с подписью.\n\n"
        "Чтобы отменить, отправь /cancel или нажми Назад."
    )
    await callback.answer()


@dp.message(AdminStates.broadcast)
async def broadcast_send(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return

    if message.text and message.text.lower() in {"/cancel", "/start"}:
        await state.clear()
        await message.answer("❌ Рассылка отменена.", reply_markup=admin_keyboard)
        return

    user_ids = get_all_user_ids()
    if not user_ids:
        await message.answer("Нет пользователей для рассылки.", reply_markup=admin_keyboard)
        await state.clear()
        return

    status_msg = await message.answer(f"⏳ Рассылка... 0 / {len(user_ids)}")

    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            if message.photo:
                caption = message.caption or ""
                await message.bot.send_photo(chat_id=uid, photo=message.photo[-1].file_id, caption=caption)
            elif message.text:
                await message.bot.send_message(chat_id=uid, text=message.text)
            else:
                failed += 1
                continue
            sent += 1
        except Exception:
            failed += 1

        if sent % 50 == 0 or sent == len(user_ids):
            try:
                await status_msg.edit_text(f"⏳ Рассылка... {sent} / {len(user_ids)}")
            except Exception:
                pass

    await message.answer(
        f"✅ Рассылка завершена.\n"
        f"Доставлено: <b>{sent}</b>\n"
        f"Не доставлено: <b>{failed}</b>",
        reply_markup=admin_keyboard,
    )
    await state.clear()



@dp.message(Command("setbal"))
async def set_user_balance(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        args = message.text.split()
        user_id = int(args[1])
        amount = int(args[2])
        add_balance(user_id, amount)
        await message.answer(
            f"<b>✅ Баланс пользователя <code>{user_id}</code> изменён на {t.fmt_money(amount)}</b>"
        )
        try:
            await bot.send_message(chat_id=user_id, text=t.balance_topup_text(amount))
        except Exception:
            pass
    except Exception:
        await message.answer("<b>❌ Формат:</b>\n<code>/setbal ID СУММА</code>")


@dp.message(Command("star_test"))
async def star_test(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    target_rub = 20
    target_stars = 30
    cancel_pending_star_requests(message.from_user.id)
    create_star_request(message.from_user.id, target_rub, target_stars)

    await message.answer(
        f"✅ Тестовая Star-заявка создана.\n"
        f"Пользователь: <code>{message.from_user.id}</code>\n"
        f"Цель: <b>{target_stars} ⭐</b> (~{t.fmt_money(target_rub)})\n"
        f"Команды: /star_status, /star_simulate 25, /star_reset"
    )


@dp.message(Command("star_status"))
async def star_status(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    request = get_pending_star_request(message.from_user.id)
    if not request:
        await message.answer("❌ Нет активной Star-заявки для этого пользователя.")
        return

    _, _, target_rub, target_stars, received_stars, credited_rub, status = request
    await message.answer(
        f"📊 Star-заявка: \n"
        f"Статус: <b>{status}</b>\n"
        f"Цель: <b>{target_stars} ⭐</b> (~{t.fmt_money(target_rub)})\n"
        f"Получено: <b>{received_stars} ⭐</b>\n"
        f"Зачислено: <b>{t.fmt_money(int(credited_rub or 0))}</b>"
    )


@dp.message(Command("star_simulate"))
async def star_simulate(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("<b>❌ Формат:</b>\n<code>/star_simulate 25</code>")
        return

    stars = int(args[1])
    request = get_pending_star_request(message.from_user.id)
    if not request:
        await message.answer("❌ Нет активной Star-заявки для этого пользователя.")
        return

    gift_key = f"admin_star_sim_{message.from_user.id}_{int(time.time())}"
    request_info, credited_rub, received_stars, completed, duplicate = add_star_gift(
        user_id=message.from_user.id,
        stars=stars,
        gift_key=gift_key,
    )

    if duplicate:
        await message.answer("⚠️ Повторное симулированное пополнение пропущено.")
        return

    if completed and credited_rub > 0:
        add_balance(message.from_user.id, credited_rub)

    request = get_pending_star_request(message.from_user.id)
    got = request[4] if request else received_stars

    await message.answer(
        f"✅ Симуляция Star-подарка: <b>{stars} ⭐</b>\n"
        f"Получено всего: <b>{got} ⭐</b>\n"
        f"Статус: <b>{'завершено' if completed else 'в процессе'}</b>\n"
        f"Зачислено сейчас: <b>{t.fmt_money(credited_rub)}</b>\n"
        f"Баланс теперь: <b>{t.fmt_money(get_balance(message.from_user.id))}</b>"
    )


@dp.message(Command("star_reset"))
async def star_reset(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    cancel_pending_star_requests(message.from_user.id)
    await message.answer("✅ Все активные Star-заявки пользователя сброшены.")


@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    bal = get_balance(message.from_user.id)
    await message.answer(f"💰 Твой баланс: <b>{t.fmt_money(bal)}</b>")


@dp.message(Command("catalog"))
async def cmd_catalog(message: Message):
    products = get_products()
    text = t.catalog_text(len(products))
    markup = products_keyboard(products) if products else back_keyboard
    await message.answer(text, reply_markup=markup)


@dp.message(Command("orders"))
async def cmd_orders(message: Message):
    await message.answer(
        t.orders_text(get_orders(message.from_user.id)),
        reply_markup=back_keyboard,
    )


@dp.message(Command("getsms_status"))
async def getsms_status(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("<b>❌ Формат:</b>\n<code>/getsms_status ORDER_ID</code>")
        return

    order_id = args[1].strip()
    row = get_getsms_order(order_id)
    if not row:
        await message.answer("❌ Заказ не найден. Проверь ID заказа.")
        return

    api_order, error = await get_order(order_id)
    if error:
        await message.answer(f"❌ Ошибка GetSMS: {error.get('error_code', 'UNKNOWN')}")
        return

    phone = api_order.get("phone_number") or api_order.get("phone")
    status = api_order.get("status")
    last_code = api_order.get("last_code")
    received_codes = api_order.get("received_codes")

    update_getsms_order(
        order_id,
        status=status,
        last_code=last_code,
        received_codes=received_codes,
        phone_number=phone,
        raw_data=str(api_order),
    )

    await message.answer(
        t.getsms_order_status_text(status or '—', last_code, received_codes),
        reply_markup=back_keyboard,
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(t.help_text())


@dp.callback_query(F.data == "buy")
async def buy(callback: CallbackQuery):
    products = get_products()
    caption = t.catalog_text(len(products))
    markup = products_keyboard(products) if products else back_keyboard
    await show_section(callback, caption, markup, section="catalog")
    await callback.answer()


@dp.callback_query(F.data.startswith("product_"))
async def product_info(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[-1])
    product = get_product(product_id)
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    text = t.product_text(product[1], product[2], product[3])
    markup = buy_product_keyboard(product_id, product[3], gift=True)

    # product: id, title, description, price, delivery_data, sold, photo(optional)
    photo = product[6] if len(product) > 6 else None

    if photo:
        try:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=photo, caption=text),
                reply_markup=markup,
            )
            await callback.answer()
            return
        except Exception:
            try:
                if callback.message.photo:
                    await callback.message.edit_caption(caption=text, reply_markup=markup)
                    await callback.answer()
                    return
            except Exception as e:
                log(f"⚠️ Не удалось показать фото товара: {e}")

    await safe_edit(callback, text, markup)
    await callback.answer()


@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    await show_section(
        callback,
        t.profile_text(
            callback.from_user.id,
            callback.from_user.username,
            get_balance(callback.from_user.id),
        ),
        back_keyboard,
        section="profile",
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("buy_"))
async def buy_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    # Защита от двойной покупки
    if product_id in _processing_products or user_id in _processing_users:
        await callback.answer("⏳ Уже обрабатывается, подожди...", show_alert=True)
        return

    product = get_product(product_id)
    if not product or product[5] == 1:
        await callback.answer("❌ Товар уже продан или не найден!", show_alert=True)
        return

    balance = get_balance(user_id)
    product_price = product[3]
    if balance < product_price:
        await callback.answer("❌ Недостаточно средств на балансе!", show_alert=True)
        return

    _processing_products.add(product_id)
    _processing_users.add(user_id)

    try:
        # Показываем пользователю, что покупка в обработке
        await safe_edit(callback, t.purchase_processing_text(), None)
        await callback.answer()

        phone_number = str(product[4]).strip()
        phone_clean = "".join(filter(str.isdigit, phone_number))
        title = product[1]

        # Проверка, что сессия живая, ДО списания денег
        log(f"🔍 ПРОВЕРКА СЕССИИ | +{phone_clean} | товар #{product_id}")
        try:
            alive = await check_session_alive(phone_clean)
        except asyncio.TimeoutError:
            alive = False
            log(f"⏰ ТАЙМАУТ ПРОВЕРКИ СЕССИИ | +{phone_clean} | товар #{product_id} снят с продажи")
        except Exception as e:
            alive = False
            log(f"❌ ОШИБКА ПРОВЕРКИ СЕССИИ | +{phone_clean} | {type(e).__name__}: {e}")

        if not alive:
            log(f"⚠️ МЁРТВАЯ СЕССИЯ | +{phone_clean} | товар #{product_id} снят с продажи")
            sell_product(product_id)
            await callback.answer("❌ Этот аккаунт больше недоступен. Выбери другой.", show_alert=True)
            await safe_edit(callback, "❌ <b>Аккаунт недоступен</b>\n\nВыбери другой из каталога.", back_keyboard)
            return

        log(f"✅ СЕССИЯ ЖИВАЯ | +{phone_clean} | списываю {product_price}₽")
        add_balance(user_id, -product_price)

        # Оповещаем пользователя и админа о попытке покупки, но не фиксируем продажу до получения кода
        await safe_edit(callback, "⏳ <b>Покупка в процессе</b>\n\n<i>Сессия проверена. Ждём код из Telegram...</i>", None)
        await callback.answer()

        try:
            await bot.send_message(
                ADMIN_ID,
                f"🛒 <b>Покупка: попытка</b>\n\n"
                f"Пользователь: <code>{user_id}</code> (@{callback.from_user.username or '—'})\n"
                f"Товар: {title}\n"
                f"Номер: <code>+{phone_clean}</code>\n"
                f"Сумма: <b>{product_price} ₽</b>"
            )
        except Exception:
            pass

        log(f"🎧 ЖДУ КОД | +{phone_clean} | user={user_id}")
        try:
            captured_code = await listen_for_telegram_code(phone_clean)
        except asyncio.TimeoutError:
            captured_code = ""
            log(f"⏰ ТАЙМАУТ КОДА | +{phone_clean} | возврат {product_price}₽ user={user_id}")
        except Exception as e:
            captured_code = ""
            log(f"❌ ОШИБКА ПЕРЕХВАТА КОДА | +{phone_clean} | {type(e).__name__}: {e}")

        if captured_code:
            try:
                sell_product(product_id)
                add_order(user_id, product_id)

                log(f"🛒 ПОКУПКА | user={user_id} (@{callback.from_user.username}) | {title} | +{phone_clean} | {product_price}₽")

                log(f"✅ КОД | +{phone_clean} → {captured_code}")
                await safe_edit(callback, t.purchase_success_text(phone_clean), None)
                await callback.message.answer(
                    t.code_received_text(captured_code),
                    reply_markup=after_purchase_keyboard(),
                )
                try:
                    session_file = _session_path(phone_clean)
                    sold_file = _sold_session_path(phone_clean)
                    if os.path.exists(session_file):
                        os.rename(session_file, sold_file)
                except Exception as e:
                    log(f"⚠️ Не удалось переместить сессию {phone_clean}: {e}")
            except Exception as e:
                log(f"❌ ОШИБКА ФИНАЛИЗАЦИИ ПОКУПКИ | user={user_id} | product={product_id} | {type(e).__name__}: {e}")
                add_balance(user_id, product_price)
                await safe_edit(callback, "❌ <b>Ошибка при оформлении</b>\nСредства возвращены на баланс.", back_keyboard)
        else:
            # В случае таймаута кода не фиксируем продажу — возвращаем деньги и оставляем товар в каталоге
            add_balance(user_id, product_price)
            log(f"❌ ТАЙМАУТ КОДА | +{phone_clean} | возврат {product_price}₽ user={user_id}")
            await callback.message.answer(
                t.code_timeout_text(product_price),
                reply_markup=after_purchase_keyboard(),
            )
    finally:
        _processing_products.discard(product_id)
        _processing_users.discard(user_id)


@dp.callback_query(F.data == "gift")
async def gift(callback: CallbackQuery):
    products = get_products()
    caption = t.catalog_text(len(products))
    markup = products_keyboard(products) if products else back_keyboard
    await show_section(callback, caption, markup, section="catalog")
    await callback.answer()


@dp.callback_query(F.data.startswith("gift_"))
async def gift_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[-1])
    product = get_product(product_id)
    if not product or product[5] == 1:
        await callback.answer("❌ Товар уже продан или не найден!", show_alert=True)
        return

    await state.update_data(gift_product_id=product_id)
    await state.set_state(GiftStates.recipient)
    await callback.message.answer(t.gift_recipient_prompt())
    await callback.answer()


@dp.message(GiftStates.recipient)
async def gift_recipient(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("gift_product_id")
    if not product_id:
        await message.answer("<b>❌ Что-то пошло не так. Попробуй снова.</b>")
        await state.clear()
        return

    product = get_product(product_id)
    if not product or product[5] == 1:
        await message.answer("<b>❌ Товар уже продан или не найден.</b>")
        await state.clear()
        return

    user_id = message.from_user.id
    product_price = product[3]
    balance = get_balance(user_id)
    if balance < product_price:
        await message.answer("<b>❌ Недостаточно средств на балансе.</b>")
        await state.clear()
        return

    recipient_input = message.text.strip()
    if not recipient_input:
        await message.answer("<b>❌ Введи username получателя.</b>")
        return

    if recipient_input.startswith("@"):
        recipient_input = recipient_input[1:]

    recipient_id = None
    try:
        recipient_chat = await bot.get_chat(recipient_input)
        recipient_id = recipient_chat.id
    except Exception:
        # Попробуем найти в локальной БД по username
        try:
            recipient_id = get_user_by_username(recipient_input)
        except Exception:
            recipient_id = None

    if recipient_id is None:
        await message.answer(
            "<b>❌ Не удалось найти получателя.</b>\n"
            "Убедись, что он правильно ввёл username и начал диалог с ботом."
        )
        return
    _processing_products.add(product_id)
    _processing_users.add(user_id)

    try:
        phone_number = str(product[4]).strip()
        phone_clean = "".join(filter(str.isdigit, phone_number))
        title = product[1]

        log(f"🔍 ПРОВЕРКА СЕССИИ (подарок) | +{phone_clean} | товар #{product_id}")
        try:
            alive = await check_session_alive(phone_clean)
        except asyncio.TimeoutError:
            alive = False
            log(f"⏰ ТАЙМАУТ ПРОВЕРКИ СЕССИИ (подарок) | +{phone_clean} | товар #{product_id} снят с продажи")
        except Exception as e:
            alive = False
            log(f"❌ ОШИБКА ПРОВЕРКИ СЕССИИ (подарок) | +{phone_clean} | {type(e).__name__}: {e}")

        if not alive:
            log(f"⚠️ МЁРТВАЯ СЕССИЯ (подарок) | +{phone_clean} | товар #{product_id} снят с продажи")
            sell_product(product_id)
            await message.answer("<b>❌ Этот аккаунт больше недоступен. Выбери другой.</b>")
            await state.clear()
            return

        log(f"✅ СЕССИЯ ЖИВАЯ (подарок) | +{phone_clean} | списываю {product_price}₽")
        add_balance(user_id, -product_price)

        # Попытка покупки подарка — не фиксируем продажу до получения кода
        await message.answer(t.gift_purchase_success_text(recipient_input))

        recipient_sent = True
        try:
            await bot.send_message(recipient_id, t.gift_recipient_received_text(phone_clean))
        except Exception as e:
            recipient_sent = False
            log(f"⚠️ Не удалось отправить подарок получателю {recipient_input}: {e}")
            await message.answer(t.gift_recipient_unreachable_text(recipient_input))

        log(f"🎧 ЖДУ КОД (подарок) | +{phone_clean} | user={user_id} → recipient={recipient_input}")
        try:
            captured_code = await listen_for_telegram_code(phone_clean)
        except asyncio.TimeoutError:
            captured_code = ""
            log(f"⏰ ТАЙМАУТ КОДА (подарок) | +{phone_clean} | возврат {product_price}₽ user={user_id}")
        except Exception as e:
            captured_code = ""
            log(f"❌ ОШИБКА ПЕРЕХВАТА КОДА (подарок) | +{phone_clean} | {type(e).__name__}: {e}")

        if captured_code:
            try:
                sell_product(product_id)
                add_order(user_id, product_id)

                log(
                    f"🎁 ПОДАРОК | user={user_id} (@{message.from_user.username}) "
                    f"→ recipient={recipient_input} ({recipient_id}) | {title} | +{phone_clean} | {product_price}₽"
                )

                log(f"✅ КОД | +{phone_clean} → {captured_code}")
                if recipient_sent:
                    try:
                        await bot.send_message(recipient_id, t.gift_recipient_code_text(captured_code))
                    except Exception as e:
                        recipient_sent = False
                        log(f"⚠️ Не удалось отправить код получателю {recipient_input}: {e}")
                if not recipient_sent:
                    try:
                        await message.answer(t.gift_recipient_code_text(captured_code), reply_markup=after_purchase_keyboard())
                    except Exception:
                        pass
                else:
                    try:
                        await message.answer("<b>✅ Код получен и отправлен получателю.</b>", reply_markup=after_purchase_keyboard())
                    except Exception:
                        pass

                try:
                    session_file = _session_path(phone_clean)
                    sold_file = _sold_session_path(phone_clean)
                    if os.path.exists(session_file):
                        os.rename(session_file, sold_file)
                except Exception as e:
                    log(f"⚠️ Не удалось переместить сессию {phone_clean}: {e}")
            except Exception as e:
                log(f"❌ ОШИБКА ФИНАЛИЗАЦИИ ПОДАРКА | user={user_id} | product={product_id} | {type(e).__name__}: {e}")
                add_balance(user_id, product_price)
                await message.answer("❌ <b>Ошибка при оформлении подарка</b>\nСредства возвращены на баланс.")
        else:
            # В случае таймаута кода не фиксируем продажу — возвращаем деньги и оставляем товар в каталоге
            add_balance(user_id, product_price)
            log(f"❌ ТАЙМАУТ КОДА | +{phone_clean} | возврат {product_price}₽ user={user_id}")
            await message.answer(
                t.code_timeout_text(product_price),
                reply_markup=after_purchase_keyboard(),
            )
    finally:
        _processing_products.discard(product_id)
        _processing_users.discard(user_id)
        await state.clear()


@dp.callback_query(F.data == "add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(AdminStates.title)
    await callback.message.answer("<b>Введите название товара:</b>")
    await callback.answer()


@dp.message(AdminStates.title)
async def product_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AdminStates.description)
    await message.answer("<b>Введите описание:</b>")


@dp.message(AdminStates.description)
async def product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdminStates.price)
    await message.answer("<b>Введите цену:</b>")


@dp.message(AdminStates.price)
async def product_price(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("<b>❌ Введите число.</b>")
        return
    await state.update_data(price=int(message.text))
    await state.set_state(AdminStates.delivery_data)
    await message.answer("<b>Введите данные для выдачи (номер телефона без +):</b>")


@dp.message(AdminStates.delivery_data)
async def product_delivery(message: Message, state: FSMContext):
    await state.update_data(delivery_data=message.text)
    await state.set_state(AdminStates.photo)
    await message.answer(
        "<b>Пришли фото товара</b> (или отправь <code>-</code>, чтобы без фото):"
    )


@dp.message(AdminStates.photo)
async def product_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_id = None

    if message.photo:
        # Берём самое большое фото
        photo_id = message.photo[-1].file_id
    elif message.text and message.text.strip() == "-":
        photo_id = None
    else:
        await message.answer(
            "<b>Пришли именно фото</b> или отправь <code>-</code>, чтобы пропустить."
        )
        return

    add_product(
        data["title"],
        data["description"],
        data["price"],
        data["delivery_data"],
        photo=photo_id,
    )
    await state.clear()
    if photo_id:
        await message.answer("<b>✅ Товар добавлен с фото!</b>")
    else:
        await message.answer("<b>✅ Товар добавлен (без фото)!</b>")


@dp.callback_query(F.data == "delete_product")
async def delete_product_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    products = get_products()
    if not products:
        await callback.answer("Нет товаров для удаления", show_alert=True)
        return
    await callback.message.answer("<b>Выберите товар для удаления:</b>", reply_markup=delete_keyboard(products))
    await callback.answer()


@dp.callback_query(F.data.startswith("delete_"))
async def delete_product_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    delete_product(int(callback.data.split("_")[-1]))
    await callback.message.answer("<b>🗑 Товар удалён!</b>")
    await callback.answer()


@dp.callback_query(F.data == "balance")
async def balance_menu(callback: CallbackQuery):
    await show_section(callback, t.balance_menu_text(), deposit_methods_keyboard(), section="balance")
    await callback.answer()



@dp.callback_query(F.data == "request_refund")
async def request_refund_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    bal = get_balance(user_id)
    if bal <= 0:
        await callback.answer("❌ У тебя нет средств для возврата.", show_alert=True)
        return
    await state.set_state(PaymentStates.refund_reason)
    await callback.message.answer(t.refund_reason_prompt(), reply_markup=ForceReply(selective=True))
    await callback.answer()


@dp.message(PaymentStates.refund_reason)
async def refund_reason_handler(message: Message, state: FSMContext):
    reason = message.text.strip()
    await _submit_refund_request(message.from_user.id, reason, message)
    await state.clear()


async def _submit_refund_request(user_id: int, reason: str, message_obj: Message):
    """Create refund request, notify user and admin. Reusable from FSM and fallback reply."""
    amount_before = get_balance(user_id)
    percent = REFUND_PERCENT
    calculated = int(amount_before * percent / 100)

    req_id = create_refund_request(user_id, amount_before, percent, calculated, reason)

    try:
        await message_obj.answer(t.refund_submitted_user_text(amount_before, calculated))
    except Exception:
        pass

    # Уведомление админу с кнопками
    try:
        uname = (await bot.get_chat(user_id)).username if True else '—'
    except Exception:
        uname = None

    try:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"refund_approve_{req_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"refund_reject_{req_id}"),
            ]
        ])
        try:
            await bot.send_message(
                ADMIN_ID,
                t.admin_refund_request_text(req_id, user_id, uname, amount_before, calculated, reason),
                reply_markup=kb,
            )
            log(f"ℹ️ Refund request #{req_id} sent to admin {ADMIN_ID}")
        except Exception as e:
            # Если отправка админу упала, логируем и пробуем отправить короткое уведомление
            log(f"⚠️ Не удалось отправить заявку на возврат админу: {e}")
            try:
                await bot.send_message(ADMIN_ID, f"Заявка #{req_id} на возврат от {user_id} (ошибка при отправке полного сообщения)")
            except Exception as e2:
                log(f"⚠️ Повторная отправка админу тоже упала: {e2}")
    except Exception as e:
        log(f"⚠️ Ошибка при подготовке уведомления админу: {e}")


@dp.message(lambda m: m.reply_to_message is not None)
async def refund_reply_fallback(message: Message):
    """Fallback: if user replies to the bot's refund prompt, accept that reply as reason."""
    if not message.reply_to_message:
        return
    # Проверяем, что это ответ на сообщение с запросом причины
    reply_text = message.reply_to_message.text or ""
    if "Запрос на возврат средств" in reply_text or "Запрос на возврат" in reply_text:
        reason = message.text.strip()
        if not reason:
            return
        await _submit_refund_request(message.from_user.id, reason, message)


@dp.message(Command("refunds"))
async def admin_list_refunds(message: Message):
    log(f"/refunds called by {message.from_user.id}")
    if message.from_user.id != ADMIN_ID:
        log(f"/refunds: unauthorized user {message.from_user.id}")
        return
    rows = get_pending_refund_requests()
    if not rows:
        await message.answer("Нет ожидающих заявок на возврат.")
        return
    for row in rows:
        req_id, user_id, amount_before, percent_returned, calculated_amount, reason, status, created_at = row
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"refund_approve_{req_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"refund_reject_{req_id}"),
            ]
        ])
        try:
            await message.answer(t.admin_refund_request_text(req_id, user_id, None, amount_before, calculated_amount, reason), reply_markup=kb)
        except Exception as e:
            log(f"⚠️ Не удалось отправить заявку в чат админу: {e}")


@dp.message(lambda m: m.text and m.text.split()[0].lower().startswith('/refunds'))
async def admin_list_refunds_text(message: Message):
    log(f"/refunds (text) called by {message.from_user.id}")
    # Compatibility: handle commands like '/refunds@BotName' or plain text
    await admin_list_refunds(message)


@dp.callback_query(F.data.startswith("refund_approve_"))
async def refund_approve(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Только админ может подтверждать заявки.", show_alert=True)
        return
    try:
        req_id = int(callback.data.split("_")[-1])
    except Exception:
        await callback.answer("Некорректный ID заявки.", show_alert=True)
        return

    req = get_refund_request(req_id)
    if not req:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return
    if req[6] != 'pending':
        await callback.answer("Заявка уже обработана.", show_alert=True)
        return

    user_id = req[1]
    approved_amount = req[4]
    ok = approve_refund(req_id, approved_amount, callback.from_user.id)
    if ok:
        try:
            await bot.send_message(user_id, t.refund_approved_user_text(approved_amount))
        except Exception:
            pass
        await callback.answer("Заявка одобрена.")
        await callback.message.edit_reply_markup(None)
    else:
        await callback.answer("Не удалось одобрить заявку.", show_alert=True)


@dp.callback_query(F.data.startswith("refund_reject_"))
async def refund_reject(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Только админ может отклонять заявки.", show_alert=True)
        return
    try:
        req_id = int(callback.data.split("_")[-1])
    except Exception:
        await callback.answer("Некорректный ID заявки.", show_alert=True)
        return

    req = get_refund_request(req_id)
    if not req:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return
    if req[6] != 'pending':
        await callback.answer("Заявка уже обработана.", show_alert=True)
        return

    ok = reject_refund(req_id, callback.from_user.id)
    if ok:
        try:
            await bot.send_message(req[1], t.refund_rejected_user_text())
        except Exception:
            pass
        await callback.answer("Заявка отклонена.")
        await callback.message.edit_reply_markup(None)
    else:
        await callback.answer("Не удалось отклонить заявку.", show_alert=True)


@dp.callback_query(F.data == "getsms_service")
async def getsms_service(callback: CallbackQuery):
    # GetSMS service temporarily disabled
    await callback.message.answer("🔕 Смена номера временно отключена. Попробуйте позже.")
    await callback.answer()


@dp.callback_query(F.data.startswith("getsms_buy_"))
async def getsms_buy(callback: CallbackQuery):
    await callback.message.answer("🔕 Покупка виртуального номера временно отключена.")
    await callback.answer()


@dp.callback_query(F.data == "getsms_orders")
async def getsms_orders(callback: CallbackQuery):
    await callback.message.answer("🔕 Раздел с виртуальными номерами временно отключён.")
    await callback.answer()


@dp.callback_query(F.data == "pay_method_crypto")
async def pay_crypto_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.amount)
    await callback.message.answer(t.crypto_pay_prompt())
    await callback.answer()


@dp.message(PaymentStates.amount)
async def payment_amount(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("<b>❌ Введите число — сумму в рублях.</b>")
        return

    amount = int(message.text)
    if amount < 5:
        await message.answer("<b>❌ Минимальная сумма пополнения — 5 ₽.</b>")
        return

    invoice = await create_invoice(amount)
    if not invoice:
        await message.answer("<b>❌ Не удалось создать счёт. Попробуйте позже.</b>")
        return

    invoice_id = str(invoice["invoice_id"])
    pay_url = invoice.get("pay_url") or invoice.get("bot_invoice_url", "")

    add_payment(message.from_user.id, invoice_id, amount)
    await state.clear()

    await message.answer(
        t.crypto_invoice_text(amount),
        reply_markup=pay_invoice_keyboard(pay_url),
    )


@dp.callback_query(F.data == "pay_method_gifts")
async def pay_gifts_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.stars_amount)
    await callback.message.answer(t.stars_pay_prompt())
    await callback.answer()


@dp.message(PaymentStates.stars_amount)
async def stars_amount_handler(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("<b>❌ Введите сумму в рублях.</b>")
        return

    try:
        amount = float(message.text.replace(',', '.').replace(' ', ''))
    except ValueError:
        await message.answer("<b>❌ Введите сумму числом.</b>")
        return

    if amount <= 0:
        await message.answer("<b>❌ Сумма должна быть больше 0 ₽.</b>")
        return

    if amount < 12.5:
        await message.answer("<b>❌ Минимальная сумма — 12.50 ₽ (15 ⭐).</b>")
        return

    # Все обычные подарки имеют номинал, кратный 5 ⭐.
    # Округляем требуемое количество Stars вверх до ближайших 5 ⭐,
    # чтобы пользователь всегда мог собрать сумму существующими подарками.
    target_stars = max(15, int(((amount * 1.2) + 4.999999) // 5) * 5)

    create_star_request(message.from_user.id, amount, target_stars)
    await state.clear()
    await message.answer(t.gifts_pay_text(RELAYER_USERNAME, STARS_RATE, amount, target_stars))


# ── Оплата рублями (ручное подтверждение) ──────────────────

@dp.callback_query(F.data == "pay_method_rubles")
async def pay_rubles_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.rubles_amount)
    await callback.message.answer(t.rubles_pay_prompt())
    await callback.answer()


@dp.callback_query(F.data == "transfer_balance")
async def transfer_balance_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TransferStates.amount)
    await callback.message.answer(t.transfer_amount_prompt())
    await callback.answer()


@dp.message(PaymentStates.rubles_amount)
async def rubles_amount_handler(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("<b>❌ Введите число — сумму в рублях.</b>")
        return

    amount = int(message.text)
    if amount < 10:
        await message.answer("<b>❌ Минимальная сумма пополнения рублями — 10 ₽.</b>")
        return

    await state.update_data(rubles_amount=amount)
    await state.set_state(PaymentStates.rubles_receipt)

    await message.answer(
        t.rubles_payment_instructions(amount, RUB_PAYMENT_DETAILS)
    )
    await message.answer(t.rubles_receipt_prompt())


@dp.message(TransferStates.amount)
async def transfer_amount_handler(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("<b>❌ Введите сумму для перевода.</b>")
        return

    try:
        amount = int(message.text.replace(' ', ''))
    except ValueError:
        await message.answer("<b>❌ Введите целое число.</b>")
        return

    if amount < 1:
        await message.answer("<b>❌ Сумма должна быть не меньше 1 ₽.</b>")
        return

    user_id = message.from_user.id
    if get_balance(user_id) < amount:
        await message.answer("<b>❌ Недостаточно средств на балансе.</b>")
        return

    await state.update_data(transfer_amount=amount)
    await state.set_state(TransferStates.recipient)
    await message.answer(t.transfer_recipient_prompt())


@dp.message(PaymentStates.rubles_receipt)
async def rubles_receipt_handler(message: Message, state: FSMContext):
    # Принимаем фото или документ (pdf/скрин)
    if not (message.photo or message.document):
        await message.answer(
            "<b>❌ Пришли фото или файл чека.</b>\n"
            "Или /start чтобы отменить."
        )
        return

    data = await state.get_data()
    amount = data.get("rubles_amount")
    if not amount:
        await state.clear()
        await message.answer("<b>❌ Сессия сброшена. Начни пополнение заново.</b>")
        return

    user = message.from_user
    payment_id = create_manual_payment(
        user_id=user.id,
        amount=amount,
        username=user.username,
        full_name=user.full_name,
    )
    await state.clear()

    await message.answer(t.rubles_receipt_received())

    # Админу: текст заявки + чек + кнопки
    try:
        admin_text = t.admin_manual_request_text(
            payment_id=payment_id,
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            amount=amount,
        )
        markup = admin_manual_payment_keyboard(payment_id)

        if message.photo:
            await bot.send_photo(
                chat_id=ADMIN_ID,
                photo=message.photo[-1].file_id,
                caption=admin_text,
                reply_markup=markup,
            )
        else:
            await bot.send_document(
                chat_id=ADMIN_ID,
                document=message.document.file_id,
                caption=admin_text,
                reply_markup=markup,
            )
    except Exception as e:
        print(f"Не удалось отправить заявку админу: {e}")
        log(f"⚠️ Ошибка отправки чека админу: {e}")


@dp.callback_query(F.data.startswith("manual_approve_"))
async def manual_approve(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    payment_id = int(callback.data.split("_")[-1])
    row = get_manual_payment(payment_id)
    if not row:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    _, user_id, amount, status, *_ = row
    if status != "pending":
        await callback.answer("Заявка уже обработана", show_alert=True)
        return

    if approve_manual_payment(payment_id):
        add_balance(user_id, amount)
        log(f"💵 RUBLES | user={user_id} | +{amount}₽ | payment_id={payment_id}")
        try:
            await bot.send_message(
                chat_id=user_id,
                text=t.manual_approved_user_text(amount),
            )
        except Exception:
            pass
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ <b>Подтверждено. Баланс зачислен.</b>"
        )
        await callback.answer("Баланс зачислен")
    else:
        await callback.answer("Ошибка при подтверждении", show_alert=True)


@dp.message(TransferStates.recipient)
async def transfer_recipient_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("transfer_amount")
    if not amount:
        await state.clear()
        await message.answer("<b>❌ Сессия перевода сброшена. Начни заново.</b>")
        return

    recipient_input = message.text.strip()
    if not recipient_input:
        await message.answer("<b>❌ Введи username получателя.</b>")
        return

    if recipient_input.startswith("@"):
        recipient_input = recipient_input[1:]

    recipient_id = None
    try:
        recipient_chat = await bot.get_chat(recipient_input)
        recipient_id = recipient_chat.id
    except Exception:
        pass

    if recipient_id is None:
        recipient_id = get_user_by_username(recipient_input)

    if recipient_id is None and recipient_input.isdigit():
        recipient_id = int(recipient_input)

    if recipient_id is None:
        await message.answer(
            "<b>❌ Не удалось найти получателя.</b>\n"
            "Убедись, что он правильно ввёл username и начал диалог с ботом."
        )
        return

    sender_id = message.from_user.id

    if recipient_id == sender_id:
        await message.answer("<b>❌ Нельзя переводить себе.</b>")
        return

    if get_balance(sender_id) < amount:
        await message.answer("<b>❌ Недостаточно средств на балансе.</b>")
        await state.clear()
        return

    add_balance(sender_id, -amount)
    add_balance(recipient_id, amount)
    await state.clear()

    await message.answer(t.transfer_success_text(amount, f"@{recipient_input}"))
    try:
        await bot.send_message(recipient_id, t.transfer_received_text(amount, f"@{message.from_user.username or sender_id}"))
    except Exception as e:
        log(f"⚠️ Не удалось уведомить получателя перевода {recipient_input}: {e}")


@dp.callback_query(F.data.startswith("manual_reject_"))
async def manual_reject(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    payment_id = int(callback.data.split("_")[-1])
    row = get_manual_payment(payment_id)
    if not row:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    _, user_id, amount, status, *_ = row
    if status != "pending":
        await callback.answer("Заявка уже обработана", show_alert=True)
        return

    if reject_manual_payment(payment_id):
        try:
            await bot.send_message(
                chat_id=user_id,
                text=t.manual_rejected_user_text(),
            )
        except Exception:
            pass
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ <b>Отклонено.</b>"
        )
        await callback.answer("Заявка отклонена")
    else:
        await callback.answer("Ошибка при отклонении", show_alert=True)


@dp.callback_query(F.data == "orders")
async def orders(callback: CallbackQuery):
    await show_section(
        callback,
        t.orders_text(get_orders(callback.from_user.id)),
        back_keyboard,
        section="orders",
    )
    await callback.answer()


@dp.callback_query(F.data == "support")
async def support(callback: CallbackQuery):
    await show_section(callback, t.support_text(), back_keyboard, section="support")
    await callback.answer()


@dp.callback_query(F.data == "info")
async def info(callback: CallbackQuery):
    await show_section(callback, t.info_text(), back_keyboard, section="info")
    await callback.answer()


@dp.callback_query(F.data == "subscribe_later")
async def subscribe_later(callback: CallbackQuery):
    await callback.answer("Хорошо! Канал всегда можно найти в главном меню.")
    try:
        await callback.message.edit_text(
            "📢 Канал всегда можно найти в главном меню.",
            reply_markup=None,
        )
    except Exception:
        pass


@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    text = main_text(callback.from_user.id, callback.from_user.first_name)
    await show_section(callback, text, main_keyboard, section="start")
    await callback.answer()


async def check_payments():
    while True:
        await asyncio.sleep(10)
        try:
            pending = get_pending_payments()
            for pay in pending:
                invoice_id, user_id, amount = pay
                status = await check_invoice(invoice_id)

                if status == "paid":
                    complete_payment(invoice_id)
                    add_balance(user_id, amount)
                    log(f"💎 CRYPTO | user={user_id} | +{amount}₽ | invoice={invoice_id}")

                    try:
                        await bot.send_message(
                            chat_id=user_id,
                            text=t.balance_topup_text(amount),
                        )
                    except Exception as e:
                        log(f"⚠️ Не удалось уведомить user={user_id}: {e}")
        except Exception as e:
            print(f"Ошибка в цикле CryptoBot: {e}")


async def cleanup_old_sessions(days: int = 7):
    """Удаляет файлы сессий из sold_accounts старше N дней."""
    import time
    folder = SOLD_ACCOUNTS_DIR
    if not folder.exists():
        return
    now = time.time()
    max_age = days * 24 * 3600
    removed = 0
    for name in os.listdir(folder):
        if not name.endswith(".session"):
            continue
        path = folder / name
        try:
            age = now - path.stat().st_mtime
            if age > max_age:
                path.unlink()
                journal = str(path) + "-journal"
                if os.path.exists(journal):
                    os.remove(journal)
                removed += 1
                log(f"🗑 Удалена старая сессия: {name}")
        except Exception as e:
            log(f"⚠️ Ошибка очистки {name}: {e}")
    if removed:
        log(f"🗑 Очистка: удалено {removed} старых сессий (старше {days} дн.)")


async def cleanup_loop():
    while True:
        try:
            await cleanup_old_sessions(days=7)
        except Exception as e:
            log(f"Ошибка cleanup_loop: {e}")
        await asyncio.sleep(6 * 3600)  # раз в 6 часов


async def main():
    print("BLDSH SHOP запущен!")
    await bot.delete_webhook(drop_pending_updates=True)

    # Команды для обычных пользователей (видны при вводе /)
    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="catalog", description="Каталог аккаунтов"),
        BotCommand(command="balance", description="Мой баланс"),
        BotCommand(command="orders", description="Мои покупки"),
        BotCommand(command="help", description="Помощь"),
    ])

    asyncio.create_task(check_payments())
    asyncio.create_task(cleanup_loop())

    # Слушатель входящих Star Gifts на релеере
    from stars_listener import run_stars_listener_forever
    stars_task = asyncio.create_task(run_stars_listener_forever(bot))

    def _stars_task_done(task):
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception:
            log("❌ STARS LISTENER CRASH")
            import traceback
            traceback.print_exc()

    stars_task.add_done_callback(_stars_task_done)
    print("⭐ Stars listener: задача запущена.")

    await cleanup_old_sessions(days=7)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
