from vk_bot import VKBot

# Прямое тестирование
vk = VKBot("vk1.a.K_Sth5UQhK8Qu5fzlHnmCnMEVt_CbOzhQYNhl93BIzypJ1RZuiGE5pLJ6-Sae2ghchmMA9Ulq7VhNkHoGkvzHlUCX-nY4JfjvPeH-L3l9lzZGL09iYwz-XTAPUXToLZpZMZrRNdVrmD4Mwj2is05CJrhyBznBVaWDtHUviyM71bslN7WXWm4Z5QTOBtVkplaGrt9RrmkjIiI6Lld0h2m-Q")

print("🔧 Тестируем обработку сообщения...")
response = vk.handle_message(822018853, "привет")
print(f"Ответ: {response}")

print("🔧 Тестируем отправку сообщения...")
result = vk.send_message(822018853, "Тест из Python!")
print(f"Результат отправки: {result}")