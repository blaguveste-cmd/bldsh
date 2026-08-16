GetSMS Integration Plan
=======================

1. API key storage
   - `config.py` stores `GETSMS_API_KEY` and base URL.

2. GetSMS API client
   - `getsms_api.py` with methods:
     - `find_service_id`
     - `get_service_price`
     - `create_order`
     - `get_order`
     - `request_another_code`
     - `finish_order`

3. DB schema
   - new `getsms_orders` table for user orders.
   - store order_id, user_id, status, price, phone_number, last_code.

4. Bot UI
   - add hook `📱 Сменить номер` in main menu and balance menu.
   - show price and create order from balance.
   - display order status and codes.

5. Flow
   - user нажал кнопку → `GET /orders/price/:service_id`
   - бот показывает цену → пользователь подтверждает
   - бот списывает баланс и вызывает `POST /orders`
   - на выходе даёт номер + статус
   - бот проверяет код через `GET /orders/:id`
   - при новом коде отправляет пользователю

6. Notes
   - если последняя часть с номером приходит позже, нужна длительная проверка или повторный запрос статуса.
   - если заказ не подтверждён, можно предусмотреть повторный запрос кода и статус.
