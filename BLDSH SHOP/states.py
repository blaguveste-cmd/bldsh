from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    title = State()
    description = State()
    price = State()
    delivery_data = State()
    photo = State()
    broadcast = State()


class PaymentStates(StatesGroup):
    amount = State()           # crypto
    stars_amount = State()     # Stars: сумма в рублях
    rubles_amount = State()    # сумма в рублях
    rubles_receipt = State()   # чек после перевода
    refund_reason = State()    # причина запроса возврата


class GiftStates(StatesGroup):
    recipient = State()


class TransferStates(StatesGroup):
    amount = State()
    recipient = State()


class LolzStates(StatesGroup):
    token = State()
    import_service = State()
    import_price = State()
