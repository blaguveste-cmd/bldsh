"""Тексты BLDSH ACCS."""


def fmt_money(amount: int | float) -> str:
    if isinstance(amount, float):
        return f"{amount:,.1f}".replace(",", " ") + " ₽"
    return f"{amount:,}".replace(",", " ") + " ₽"


def main_menu_text(balance: int, first_name: str | None = None) -> str:
    name = first_name or "друг"
    return (
        f"🛍 <b><i>BLDSH ACCS</i></b>\n"
        f"<i>Тут ты можешь купить готовые Telegram-аккаунты</i>\n\n"
        f"Привет, <b>{name}</b>!\n"
        f"💰 Баланс: <code>{fmt_money(balance)}</code>\n\n"
        f"<b>Выбери действие</b> ниже и начни покупку или подарок."
    )


def catalog_text(count: int = 0) -> str:
    if count == 0:
        return (
            f"🛒 <b><i>Каталог</i></b>\n\n"
            f"<b>Сейчас свободных аккаунтов нет.</b>\n"
            f"<i>Новые товары появляются регулярно. Загляни позже.</i>"
        )
    return (
        f"🛒 <b><i>Каталог</i></b>\n\n"
        f"<b>Доступно:</b> <code>{count}</code> аккаунтов\n\n"
        f"<i>Выбери нужный вариант ниже.</i>"
    )


def product_text(title: str, description: str, price: int) -> str:
    return (
        f"📱 <b><i>{title}</i></b>\n\n"
        f"{description}\n\n"
        f"💵 <b>Цена:</b> <code>{fmt_money(price)}</code>\n\n"
        f"<b>Что будет дальше:</b>\n"
        f"1️⃣ Оплатишь товар\n"
        f"2️⃣ Номер и код придут автоматически\n"
        f"3️⃣ Код придёт в этот чат\n\n"
        f"<i>Покупай или сделай подарок другу в пару кликов.</i>"
    )


def gift_recipient_prompt() -> str:
    return (
        "🎁 <b><i>Подарок другу</i></b>\n\n"
        "Отправь <b>username</b> получателя.\n"
        "Он должен уже начать диалог с ботом.\n\n"
        "<b>Пример:</b> <code>@username</code>"
    )


def gift_purchase_success_text(recipient: str) -> str:
    return (
        "✅ <b><i>Подарок оформлен</i></b>\n\n"
        f"Товар будет доставлен получателю: <b>{recipient}</b>.\n"
        "Номер и код придут ему автоматически.\n\n"
        "<i>Если получатель не доступен, ты получишь сообщение с данными лично.</i>"
    )


def gift_recipient_received_text(phone: str) -> str:
    return (
        "🎁 <b><i>Тебе подарили аккаунт!</i></b>\n\n"
        f"📱 Номер: <code>+{phone}</code>\n\n"
        "Код придёт, как только он появится."
    )


def gift_recipient_code_text(code: str) -> str:
    return (
        "✅ <b><i>Код для подарка</i></b>\n\n"
        f"<code>{code}</code>\n\n"
        "Отправь его получателю вместе с номером, если потребуется."
    )


def gift_recipient_unreachable_text(recipient: str) -> str:
    return (
        "⚠️ <b><i>Не удалось доставить подарок</i></b>\n\n"
        f"Пользователь <b>{recipient}</b> не доступен для сообщений.\n"
        "Тебе придёт номер и код лично — перешли их вручную получателю."
    )


def profile_text(user_id: int, username: str | None, balance: int) -> str:
    uname = f"@{username}" if username else "—"
    return (
        f"👤 <b><i>Профиль</i></b>\n\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Username:</b> {uname}\n"
        f"💰 <b>Баланс:</b> <code>{fmt_money(balance)}</code>\n\n"
        f"<i>Используй баланс для покупки или подарков.</i>"
    )


def balance_menu_text() -> str:
    return (
        f"💳 <b><i>Пополнение баланса</i></b>\n\n"
        f"<b>Выбери способ пополнения:</b>\n\n"
        f"💎 <b>Crypto Bot</b> — скорость + авто\n"
        f"⭐ <b>Telegram Stars</b> — подарки в Telegram\n"
        f"💵 <b>Рубли</b> — перевод вручную\n"
        f"💱 <b>Перевести баланс</b> — отправить деньги другому пользователю\n\n"
        f"<i>Баланс обновится автоматически после оплаты или перевода.</i>"
    )


def refund_reason_prompt() -> str:
    effective_note = ""
    try:
        stars_effective = int(REFUND_PERCENT * (1 - 0.15))
        effective_note = f"Если часть пополнения была через Stars, учти комиссию обмена ~15% — итоговый возврат будет примерно <code>{stars_effective}%</code> от этой части."
    except Exception:
        effective_note = "Если часть баланса получена через Stars — учти, что может действовать комиссия."

    return (
        "↩️ <b><i>Запрос на возврат средств</i></b>\n\n"
        "Напиши причину, почему хочешь вернуть средства.\n"
        f"<b>Важно:</b> при одобрении возвращается <code>{REFUND_PERCENT}%</code> от текущего баланса.\n"
        f"({effective_note})"
    )


def refund_submitted_user_text(amount_before: int, calculated_amount: int) -> str:
    return (
        "✅ <b><i>Заявка отправлена</i></b>\n\n"
        f"Текущий баланс: <b>{fmt_money(amount_before)}</b>\n"
        f"Приблизительный возврат: <b>{fmt_money(calculated_amount)}</b> (<code>{REFUND_PERCENT}%</code> от баланса)\n\n"
        "Заявка отправлена администратору — он свяжется с тобой по решению."
    )


def admin_refund_request_text(request_id: int, user_id: int, username: str | None, amount_before: int, calculated_amount: int, reason: str) -> str:
    uname = f"@{username}" if username else "—"
    return (
        f"🔔 <b><i>Заявка на возврат #{request_id}</i></b>\n\n"
        f"Пользователь: <code>{user_id}</code> {uname}\n"
        f"Баланс: <b>{fmt_money(amount_before)}</b>\n"
        f"Предлагаемый возврат: <b>{fmt_money(calculated_amount)}</b>\n\n"
        f"Причина:\n{reason}\n\n"
        "Нажми кнопку, чтобы одобрить или отклонить заявку."
    )


def refund_approved_user_text(amount: int) -> str:
    return (
        "✅ <b><i>Заявка одобрена</i></b>\n\n"
        f"Мы вернём: <b>{fmt_money(amount)}</b>\n\n"
        "Средства будут отправлены вами по выбранному способу возврата (админ свяжется с вами)."
    )


def refund_rejected_user_text() -> str:
    return (
        "❌ <b><i>Заявка отклонена</i></b>\n\n"
        "К сожалению, администратор отклонил ваш запрос.\n"
        "Если нужны разъяснения — напиши в поддержку."
    )


def getsms_service_prompt() -> str:
    return (
        f"📱 <b><i>Смена номера</i></b>\n\n"
        f"Это услуга виртуального номера из GetSMS.\n"
        f"Цена будет рассчитана автоматически по выбранному сервису.\n\n"
        f"Нажми кнопку, чтобы увидеть цену и оформить заказ."
    )


def getsms_order_created_text(phone: str, price: float) -> str:
    return (
        f"✅ <b><i>Заказ создан</i></b>\n\n"
        f"📱 Номер: <code>{phone}</code>\n"
        f"💰 Цена: <b>{fmt_money(price)}</b>\n\n"
        f"Теперь открой Telegram и запроси код.\n"
        f"Когда код придёт, бот сообщит сам."
    )


def getsms_order_status_text(status: str, last_code: str | None, received_codes: int | None) -> str:
    text = (
        f"📊 <b><i>Статус заказа</i></b>\n\n"
        f"Статус: <b>{status}</b>\n"
    )
    if last_code:
        text += f"\nКод: <code>{last_code}</code>\n"
    if received_codes is not None:
        text += f"\nКодов получено: <b>{received_codes}</b>\n"
    return text


def getsms_order_price_text(price: float) -> str:
    return (
        f"📱 <b><i>Смена номера</i></b>\n\n"
        f"Цена: <b>{fmt_money(price)}</b>\n\n"
        f"Если всё подходит, оформи заказ.\n"
        f"Стоимость спишется с баланса."
    )


def getsms_order_list_text(orders: list) -> str:
    if not orders:
        return (
            f"📦 <b><i>Мои номера</i></b>\n\n"
            f"Пока нет заказов. Оформи номер через меню."
        )
    lines = [f"📦 <b><i>Мои номера</i></b>\n\n"]
    for i, order in enumerate(orders, 1):
        lines.append(
            f"<b>{i}.</b> #{order[1]} — <code>{order[4] or '—'}</code>\n"
            f"   Цена: {fmt_money(order[3])}\n"
            f"   Статус: <b>{order[5]}</b>\n"
        )
    return "\n".join(lines)


def crypto_pay_prompt() -> str:
    return (
        f"💎 <b><i>Crypto Bot</i></b>\n\n"
        f"Введи сумму в <b>рублях</b>.\n"
        f"Минимум: <b>5 ₽</b>\n\n"
        f"<i>После оплаты баланс зачислится сам.</i>"
    )


def crypto_invoice_text(amount: int) -> str:
    return (
        f"💳 <b><i>Счёт создан</i></b>\n\n"
        f"Сумма: <b>{fmt_money(amount)}</b>\n\n"
        f"Нажми кнопку ниже и оплати.\n"
        f"<i>Баланс придёт сразу после оплаты.</i>"
    )


def stars_pay_prompt() -> str:
    return (
        "⭐ <b><i>Пополнение через Telegram Stars</i></b>\n\n"
        "Введи, на сколько <b>рублей</b> хочешь пополнить баланс.\n"
        "<b>Курс:</b> <code>1 ₽ = 1.2 ⭐</code>\n\n"
        "Отправляй <b>несколько подарков</b> подряд: например, <code>15+15</code> ⭐ или <code>15+25</code> ⭐.\n"
        "<b>Доступные номиналы:</b> <i>15 / 25 / 50 / 100 ⭐</i>."
    )


def gifts_pay_text(relayer: str, rate: float = 1/1.2, amount: float | None = None, target_stars: int | None = None) -> str:
    if amount is None or target_stars is None:
        return (
            "⭐ <b><i>Оплата Stars</i></b>\n\n"
            f"<b>Отправляй подарки на {relayer}</b>.\n"
            "Можно отправить один или несколько подарков.\n\n"
            "📊 <b>Курс:</b> <code>1 ₽ = 1.2 ⭐</code>\n\n"
            "🎁 <b>Номиналы:</b> <i>15 / 25 / 50 / 100 ⭐</i>"
        )
    return (
        "⭐ <b><i>Оплата Stars</i></b>\n\n"
        f"<b>Сумма:</b> <code>{fmt_money(amount)}</code>\n"
        f"<b>Нужно получить:</b> <code>{target_stars} ⭐</code>\n"
        f"<b>Это примерно:</b> <code>{target_stars / 1.2:.2f} ₽</code> по курсу.\n\n"
        f"<b>Отправляй подарки на {relayer}</b>.\n"
        "Можно отправить несколько подарков подряд — например <code>15+15</code>, <code>15+25</code>, <code>25+50</code> и т.д.\n\n"
        "🎁 <b>Номиналы:</b> <i>15 / 25 / 50 / 100 ⭐</i>\n"
        "📊 <b>Курс:</b> <code>1 ₽ = 1.2 ⭐</code>\n\n"
        "<i>Можно отправлять подарки в любой комбинации. После достижения нужного количества Stars баланс пополнится автоматически. Если подарков окажется больше — лишние Stars тоже будут учтены.</i>"
    )


def rubles_pay_prompt() -> str:
    return (
        f"💵 <b><i>Оплата в рублях</i></b>\n\n"
        f"Введи сумму пополнения.\n"
        f"Минимум: <b>10 ₽</b>\n\n"
        f"<i>После перевода админ подтвердит платёж.</i>"
    )


def rubles_payment_instructions(amount: int, details: str) -> str:
    return (
        f"💵 <b><i>Реквизиты</i></b>\n\n"
        f"Сумма: <b>{fmt_money(amount)}</b>\n\n"
        f"Куда переводить:\n"
        f"<code>{details}</code>\n\n"
        f"1. Переведи <b>точно</b> эту сумму\n"
        f"2. Пришли <b>чек / скрин перевода</b> сюда\n\n"
        f"<i>После проверки чека баланс зачислят.</i>"
    )


def rubles_receipt_prompt() -> str:
    return (
        f"🧾 <b><i>Пришли чек</i></b>\n\n"
        f"Отправь <b>фото</b> или <b>файл</b> чека о переводе.\n\n"
        f"<i>Без чека заявка не уйдёт админу.</i>"
    )


def rubles_receipt_received() -> str:
    return (
        f"✅ <b><i>Чек получен</i></b>\n\n"
        f"Заявка отправлена на проверку.\n"
        f"Обычно это занимает <b>1–15 минут</b>."
    )


def admin_manual_request_text(payment_id: int, user_id: int, username: str | None, full_name: str | None, amount: int) -> str:
    uname = f"@{username}" if username else "—"
    name = full_name or "—"
    return (
        f"🔔 <b><i>Заявка на пополнение</i></b>\n\n"
        f"№ <code>#{payment_id}</code>\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Username:</b> {uname}\n"
        f"👤 <b>Имя:</b> {name}\n"
        f"💰 <b>Сумма:</b> <code>{fmt_money(amount)}</code>\n\n"
        f"<i>Подтвердить?</i>"
    )


def manual_approved_user_text(amount: int) -> str:
    return (
        f"✅ <b><i>Платёж подтверждён</i></b>\n\n"
        f"Зачислено: <b>+{fmt_money(amount)}</b>\n\n"
        f"<i>Можешь покупать аккаунт.</i>"
    )


def manual_rejected_user_text() -> str:
    return (
        f"❌ <b><i>Платёж отклонён</i></b>\n\n"
        f"Перевод не подтвердили.\n"
        f"Если деньги уже ушли — напиши в <b>поддержку</b>."
    )


def orders_text(orders: list) -> str:
    if not orders:
        return (
            f"📦 <b><i>Мои покупки</i></b>\n\n"
            f"Пока <b>пусто</b>.\n"
            f"<i>Оформляй покупки в каталоге.</i>"
        )
    lines = [f"📦 <b><i>Мои покупки</i></b>\n\n"]
    for i, order in enumerate(orders, 1):
        lines.append(
            f"<b>{i}.</b> {order[0]}\n"
            f"   📱 {order[3]}\n"
            f"   💰 {fmt_money(order[2])}\n"
        )
    return "\n".join(lines)


def support_text(admin: str = "@baldush") -> str:
    return (
        f"💬 <b><i>Поддержка</i></b>\n\n"
        f"Вопрос или проблема — пиши:\n\n"
        f"👉 <b>{admin}</b>"
    )


def info_text() -> str:
    return (
        f"ℹ️ <b><i>О магазине</i></b>\n\n"
        f"🔹 Готовые Telegram-аккаунты\n"
        f"🔹 Номер и код приходят автоматически\n"
        f"🔹 Поддержка 24/7\n"
        f"🔹 Оплата: Crypto, Stars, рубли\n\n"
        f"<i>Удобно, быстро и без лишних действий.</i>"
    )


def purchase_success_text(phone: str) -> str:
    return (
        f"✅ <b><i>Оплата прошла</i></b>\n\n"
        f"📱 Номер: <code>+{phone}</code>\n\n"
        f"<b>Что дальше:</b>\n"
        f"1️⃣ Открой Telegram\n"
        f"2️⃣ Введи этот номер\n"
        f"3️⃣ Запроси код\n"
        f"4️⃣ Бот пришлёт код сам\n\n"
        f"📩 <i>Код получен и отправлен ниже.</i>"
    )


def purchase_processing_text() -> str:
    return (
        "⏳ <b><i>Покупка в процессе</i></b>\n\n"
        "Мы обрабатываем твой платёж и подготавливаем аккаунт.\n"
        "Пожалуйста, немного подожди — это займёт несколько секунд."
    )


def purchase_failed_text(reason: str | None = None) -> str:
    text = (
        "❌ <b><i>Не удалось оформить покупку</i></b>\n\n"
        "Произошла ошибка при попытке купить аккаунт.\n"
    )
    if reason:
        text += f"\nПричина: <code>{reason}</code>\n"
    text += "\nСредства будут возвращены на баланс, если списание уже произошло."
    return text


def code_received_text(code: str) -> str:
    return (
        f"📩 <b><i>Код получен</i></b>\n\n"
        f"<code>{code}</code>\n\n"
        f"<i>Введи его в Telegram.</i>"
    )


def code_timeout_text(amount: int) -> str:
    return (
        f"⏰ <b><i>Код не пришёл</i></b>\n\n"
        f"Время вышло.\n"
        f"<b>{fmt_money(amount)}</b> вернули на баланс.\n\n"
        f"<i>Можешь взять другой аккаунт.</i>"
    )


def balance_topup_text(amount: int) -> str:
    return (
        f"💎 <b><i>Баланс пополнен</i></b>\n\n"
        f"Зачислено: <b>+{fmt_money(amount)}</b>\n\n"
        f"<i>Можешь переходить к покупке.</i>"
    )


def transfer_amount_prompt() -> str:
    return (
        "💱 <b><i>Перевод баланса</i></b>\n\n"
        "Введи сумму, которую хочешь перевести.\n"
        "<b>Сумма списывается с твоего баланса.</b>\n\n"
        "<i>Минимум 1 ₽.</i>"
    )


def transfer_recipient_prompt() -> str:
    return (
        "💱 <b><i>Кому перевести</i></b>\n\n"
        "Отправь username получателя.\n"
        "Получатель должен уже начать диалог с ботом.\n\n"
        "<b>Пример:</b> <code>@username</code>"
    )


def transfer_success_text(amount: int, recipient: str) -> str:
    return (
        "✅ <b><i>Перевод выполнен</i></b>\n\n"
        f"С баланса списано: <b>{fmt_money(amount)}</b>\n"
        f"Получатель: <b>{recipient}</b>\n\n"
        "<i>Он получит уведомление и зачисление.</i>"
    )


def transfer_received_text(amount: int, sender: str) -> str:
    return (
        "💸 <b><i>Тебе поступили деньги</i></b>\n\n"
        f"Сумма: <b>{fmt_money(amount)}</b>\n"
        f"От: <b>{sender}</b>\n\n"
        "<i>Баланс пополнен автоматически.</i>"
    )


def admin_panel_text() -> str:
    return (
        f"👑 <b><i>Admin Panel</i></b>\n\n"
        f"<i>Управление магазином</i>"
    )


def lolz_panel_text(token_set: bool) -> str:
    status = "<b>токен установлен</b>" if token_set else "<b>токен не задан</b>"
    return (
        f"💼 <b><i>Lolz API</i></b>\n\n"
        f"Статус: {status}\n\n"
        f"Здесь можно настроить Lolz API и импортировать аккаунты прямо в каталог."
    )


def lolz_token_prompt() -> str:
    return (
        "🔑 <b><i>Установи Lolz API токен</i></b>\n\n"
        "Введи токен, который используется для доступа к Lolz API."
    )


def lolz_token_saved_text() -> str:
    return (
        "✅ <b><i>Токен Lolz API сохранён</i></b>\n\n"
        "Теперь можно импортировать аккаунты из Lolz."
    )


def lolz_import_service_prompt() -> str:
    return (
        "⬇️ <b><i>Импорт аккаунта из Lolz</i></b>\n\n"
        "Введи категорию или название услуги Lolz, например <code>USA</code>."
    )


def lolz_import_price_prompt(service: str) -> str:
    return (
        f"⬇️ <b><i>Импорт аккаунта {service}</i></b>\n\n"
        "Введите вашу цену продажи в рублях — например, <code>35</code>.\n"
        "Аккаунт будет добавлен в каталог по этой цене."
    )


def lolz_import_result_text(success: bool, message: str) -> str:
    if success:
        return (
            f"✅ <b><i>Аккаунт импортирован</i></b>\n\n"
            f"{message}"
        )
    return (
        f"❌ <b><i>Не удалось импортировать</i></b>\n\n"
        f"{message}"
    )


def help_text() -> str:
    return (
        f"📖 <b><i>Помощь</i></b>\n\n"
        f"<code>/start</code> — меню\n"
        f"<code>/catalog</code> — каталог аккаунтов\n"
        f"<code>/balance</code> — баланс\n"
        f"<code>/orders</code> — покупки\n"
        f"<code>/help</code> — эта справка\n\n"
        f"📢 Канал: <b>t.me/bldshaccs</b>"
    )


def subscribe_prompt_text() -> str:
    return (
        f"📢 <b><i>Новости</i></b>\n\n"
        f"Подпишись, чтобы не пропускать новые аккаунты и акции.\n\n"
        f"👉 <b>t.me/bldshaccs</b>"
    )
