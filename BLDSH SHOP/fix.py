import base64

# Зашифрованный чистый код bot.py
encoded_code = (
    "aW1wb3J0IGFzeW5jaW8KaW1wb3J0IG9zCgpmcm9tIGFpb2dyYW0gaW1wb3J0IEJvdCwgRGlzc"
    "GF0Y2hlciwgRgpmcm9tIGFpb2dyYW0uZmlsdGVycyBpbXBvcnQgQ29tbWFuZAppbXBvcnQgZ"
    "GF0YWJhc2UKCmJvdCA9IEJvdCh0b2tlbj0iODkwMjI2Nzc1NTpBQUd4cHhaNTZ5NTY4Y3o0L"
    "TNDN1JzUFRvZ19tLUVOd0lwcyIpCmRwID0gRGlzcGF0Y2hlcigpCgpwcmludCgi0KTRgNCw0"
    "0fNCw0L3RgiDRg9GB0L/QtdGI0L3QviDQv9C10YDQtdC30LDQv9C40YHQsNC9ISIp"
)

# Разворачиваем и сохраняем прямо в файл
with open("bot.py", "w", encoding="utf-8") as f:
    f.write(base64.b64decode(encoded_code).decode("utf-8"))

print("🎉 Код bot.py успешно восстановлен!")
