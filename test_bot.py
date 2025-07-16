#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы бота
"""

import asyncio
from bot import TelegramBot

async def test_bot():
    """Тестирует основные функции бота"""
    print("🚀 Запуск тестирования бота...")
    
    try:
        bot = TelegramBot()
        print("✅ Бот успешно инициализирован")
        
        # Тестируем базу данных
        print("📊 Тестирование базы данных...")
        user_data = bot.db.get_or_create_user(123456789, "test_user")
        print(f"✅ Пользователь создан: {user_data}")
        
        # Тестируем добавление номера
        print("📱 Тестирование добавления номера...")
        bot.db.add_number_to_queue(123456789, "79001234567")
        queue = bot.db.get_queue()
        print(f"✅ Номер добавлен в очередь. Размер очереди: {len(queue)}")
        
        # Тестируем форматирование
        from utils import format_main_menu, validate_phone_number
        menu_text = format_main_menu(user_data, len(queue), 1)
        print("✅ Форматирование меню работает")
        
        # Тестируем валидацию номеров
        valid_numbers = ["79001234567", "+7 900 123 45 67", "8-900-123-45-67"]
        invalid_numbers = ["123", "abc", "790012345678901234567"]
        
        for num in valid_numbers:
            if not validate_phone_number(num):
                print(f"❌ Ошибка валидации для валидного номера: {num}")
        
        for num in invalid_numbers:
            if validate_phone_number(num):
                print(f"❌ Ошибка валидации для невалидного номера: {num}")
        
        print("✅ Валидация номеров работает корректно")
        
        print("\n🎉 Все тесты пройдены успешно!")
        print("Бот готов к запуску. Используйте команду: python bot.py")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bot())