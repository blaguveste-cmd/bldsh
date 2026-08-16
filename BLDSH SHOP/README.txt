BLDSH SHOP — Stars + Reviews patch

Заменить в существующем проекте:
- bot.py
- database.py
- keyboards.py
- states.py
- stars_listener.py
- start_listener.py
- texts.py
- config.py

Что добавлено:
1. Пополнение Stars через ввод суммы в рублях.
2. Курс 1 ⭐ = 1.2 ₽.
3. Поддерживаемые обычные подарки: 15 / 25 / 50 / 100 Stars.
4. Доступные пополнения: 18 / 30 / 60 / 120 ₽.
5. Заявка на Stars хранится в БД.
6. Повторная обработка одного подарка не зачисляет баланс второй раз.
7. Полученный подарок обрабатывается по фактическому числу Stars.
8. После получения кода добавлена просьба оставить отзыв в @baldushrep.
9. В главном меню добавлена кнопка «⭐ Отзывы».
10. start_listener.py оставлен как совместимость со старым именем и использует новый Stars listener.

Важно:
- После замены файлов перезапуск бота создаст таблицу stars_payments автоматически.
- В архив исходного проекта НЕ включены session-файлы и shop.db.
* Переменные окружения: теперь `config.py` читает секреты из переменных окружения.
	- Создайте файл `.env` на сервере или в локальной директории (не коммитьте) по образцу `.env.example`.
	- Установите `BOT_TOKEN`, `CRYPTO_TOKEN`, `GETSMS_API_KEY` и другие значения через переменные окружения.
	- После заполнения `.env` перезапустите бота.

Перед запуском:
python -m py_compile bot.py database.py keyboards.py states.py stars_listener.py start_listener.py texts.py


ENVIRONMENT / SECRETS
---------------------
Real secrets belong in .env. The repository-safe .env.example contains empty placeholders only.
config.py loads .env automatically; no extra python-dotenv package is required.
Never upload .env or *.session files publicly.
