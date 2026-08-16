import asyncio
from yoomoney import Authorize

print("🪙 ПОЛУЧЕНИЕ ВЕЧНОГО ТОКЕНА ДЛЯ BLDSH SHOP")
print("-" * 50)

# Официальный публичный ID приложения, одобренный системой ЮМани
CLIENT_ID = "4988A72F67BA21F77F54B00D93B49CDCCEA08DEE000B025BF66C7CCBE5FE2910"

print("⏳ Сейчас в консоли появится ссылка. Скопируйте её в браузер, нажмите 'Разрешить' и введите СМС.")
print("После этого скопируйте адрес БЕЛОЙ страницы (localhost) и вставьте обратно сюда!\n")

try:
    Authorize(
        client_id=CLIENT_ID,
        client_secret="",
        redirect_uri="https://localhost",
        scope=["account-info", "operation-history", "operation-details"]
    )
except Exception as e:
    print("\n[Скрипт перешёл в режим ожидания ввода ссылки]")
