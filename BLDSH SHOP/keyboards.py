from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

CHANNEL_URL = "https://t.me/bldshaccs"


def _blue(text: str) -> str:
    # Эмодзи удалено по запросу — возвращаем оригинальный текст
    return text

main_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=_blue("🛒 Купить аккаунт"), callback_data="buy")],
    [InlineKeyboardButton(text=_blue("🎁 Подарить аккаунт"), callback_data="gift")],
    [InlineKeyboardButton(text=_blue("💳 Пополнить баланс"), callback_data="balance")],
    [
        InlineKeyboardButton(text=_blue("📦 Покупки"), callback_data="orders"),
        InlineKeyboardButton(text=_blue("👤 Профиль"), callback_data="profile"),
    ],
    [
        InlineKeyboardButton(text=_blue("💬 Поддержка"), callback_data="support"),
        InlineKeyboardButton(text=_blue("💬 Отзывы"), url="https://t.me/baldushrep"),
    ],
    [InlineKeyboardButton(text=_blue("ℹ️ О магазине"), callback_data="info")],
    [InlineKeyboardButton(text=_blue("📢 Новости"), url=CHANNEL_URL)],
])


back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=_blue("◀️ Назад"), callback_data="back")],
])


def products_keyboard(products):
    buttons = []
    for product in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"📱 {product[1]}  ·  {product[3]} ₽",
                callback_data=f"product_{product[0]}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def buy_product_keyboard(product_id, price: int = 0, gift: bool = True):
    label = f"✅ Купить за {price} ₽" if price else "✅ Купить"
    buttons = [[InlineKeyboardButton(text=_blue(label), callback_data=f"buy_{product_id}")]]
    if gift:
        buttons.append([InlineKeyboardButton(text=_blue("🎁 Подарить"), callback_data=f"gift_{product_id}")])
    buttons.append([InlineKeyboardButton(text=_blue("◀️ К каталогу"), callback_data="buy")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=_blue("➕ Добавить аккаунт"), callback_data="add_product")],
    [InlineKeyboardButton(text=_blue("🗑 Удалить аккаунт"), callback_data="delete_product")],
    [InlineKeyboardButton(text=_blue("📢 Рассылка"), callback_data="broadcast")],
])


def delete_keyboard(products):
    buttons = []
    for product in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {product[1]}  ·  {product[3]} ₽",
                callback_data=f"delete_{product[0]}",
            )
        ])
    buttons.append([InlineKeyboardButton(text=_blue("◀️ Закрыть"), callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def deposit_methods_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_blue("💎 Crypto Bot  ·  USDT / TON"), callback_data="pay_method_crypto")],
        [InlineKeyboardButton(text=_blue("⭐ Telegram Stars"), callback_data="pay_method_gifts")],
        [InlineKeyboardButton(text=_blue("💵 Рубли  ·  перевод"), callback_data="pay_method_rubles")],
        [InlineKeyboardButton(text=_blue("💱 Перевести баланс"), callback_data="transfer_balance")],
        [InlineKeyboardButton(text=_blue("↩️ Попросить возврат средств"), callback_data="request_refund")],
        [InlineKeyboardButton(text=_blue("◀️ Назад"), callback_data="back")],
    ])





def pay_invoice_keyboard(pay_url: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_blue("💳 Оплатить"), url=pay_url)],
        [InlineKeyboardButton(text=_blue("◀️ Назад"), callback_data="back")],
    ])


def admin_manual_payment_keyboard(payment_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=_blue("✅ Подтвердить"), callback_data=f"manual_approve_{payment_id}"),
            InlineKeyboardButton(text=_blue("❌ Отклонить"), callback_data=f"manual_reject_{payment_id}"),
        ]
    ])


def after_purchase_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_blue("🛒 В каталог"), callback_data="buy")],
        [InlineKeyboardButton(text=_blue("🏠 В меню"), callback_data="back")],
    ])


def subscribe_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_blue("📢 Перейти в канал"), url=CHANNEL_URL)],
        [InlineKeyboardButton(text=_blue("⏳ Позже"), callback_data="subscribe_later")],
    ])
