import asyncio
import os
import shutil

print("🤖 ПЕРЕНОС ГОТОВОЙ СЕССИИ ИЗ TELEGRAM DESKTOP")
print("-" * 50)

# Просим пользователя указать номер телефона
phone = input("Введите номер вашего ненужного аккаунта (только цифры, например 79991112233): ").strip()

# Официальный Telegram Desktop при входе на Windows сам создает файл сессии. 
# Он лежит в папке: C:\Users\ИМЯ_ПОЛЬЗОВАТЕЛЯ\AppData\Roaming\Telegram Desktop\tdata
# Нам нужно просто скопировать этот готовый файл к нашему боту!

appdata = os.getenv("APPDATA")
source_session = os.path.join(appdata, "Telegram Desktop", "tdata", "key_datas")

if os.path.exists(source_session):
    if not os.path.exists("accounts"):
        os.makedirs("accounts")
    
    # Копируем файл сессии прямо в папку вашего бота
    shutil.copy(source_session, f"accounts/{phone}.session")
    print(f"\n🎉 ПУШКА! Файл accounts/{phone}.session успешно создан вообще БЕЗ кода, VPN и капчи!")
else:
    print("\n❌ Ошибка: Вы не вошли в этот аккаунт через официальный Telegram Desktop на этом ПК!")
    print("💡 Решение: Скачайте официальный Telegram Desktop, войдите в этот ненужный аккаунт, а потом запустите этот скрипт заново.")

input("\nНажмите Enter для завершения...")
