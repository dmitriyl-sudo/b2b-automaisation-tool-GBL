#!/usr/bin/env python3
"""
Тест интеграции Telegram бота с системой уведомлений
"""

import asyncio
import logging
from datetime import datetime
from telegram_bot import init_telegram_bot, send_sheet_notification_sync
from telegram_config import TelegramConfig

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_telegram_integration():
    """Тестирует интеграцию Telegram бота"""
    print("🧪 ТЕСТ ИНТЕГРАЦИИ TELEGRAM БОТА")
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 1. Проверяем конфигурацию
    print("\n1️⃣ ПРОВЕРКА КОНФИГУРАЦИИ")
    print("-" * 50)
    
    if TelegramConfig.is_configured():
        bot_token = TelegramConfig.get_bot_token()
        chat_id = TelegramConfig.get_chat_id()
        print(f"✅ Telegram бот настроен")
        print(f"   Bot Token: {bot_token[:10]}...")
        print(f"   Chat ID: {chat_id}")
    else:
        print("❌ Telegram бот НЕ настроен")
        print("\n📋 Инструкции по настройке:")
        print(TelegramConfig.get_setup_instructions())
        return False
    
    # 2. Инициализируем бота
    print("\n2️⃣ ИНИЦИАЛИЗАЦИЯ БОТА")
    print("-" * 50)
    
    try:
        notifier = init_telegram_bot(bot_token, chat_id)
        print("✅ Бот инициализирован успешно")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False
    
    # 3. Тестируем отправку уведомлений
    print("\n3️⃣ ТЕСТ УВЕДОМЛЕНИЙ")
    print("-" * 50)
    
    test_cases = [
        {
            "name": "Одиночный GEO экспорт",
            "params": {
                "sheet_url": "https://docs.google.com/spreadsheets/d/test_single_123",
                "project": "Rolling",
                "geo": "DE",
                "env": "prod",
                "export_type": "single"
            }
        },
        {
            "name": "Multi-GEO экспорт",
            "params": {
                "sheet_url": "https://docs.google.com/spreadsheets/d/test_multi_456",
                "project": "SpinEmpire",
                "env": "stage",
                "export_type": "multi"
            }
        },
        {
            "name": "Full Project экспорт",
            "params": {
                "sheet_url": "https://docs.google.com/spreadsheets/d/test_full_789",
                "project": "Ritzo",
                "env": "prod",
                "export_type": "full"
            }
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Тест {i}: {test_case['name']}")
        
        try:
            success = send_sheet_notification_sync(**test_case['params'])
            if success:
                print(f"   ✅ Уведомление отправлено успешно")
                success_count += 1
            else:
                print(f"   ❌ Ошибка отправки уведомления")
        except Exception as e:
            print(f"   ❌ Исключение: {e}")
    
    # 4. Итоги тестирования
    print(f"\n4️⃣ ИТОГИ ТЕСТИРОВАНИЯ")
    print("-" * 50)
    
    total_tests = len(test_cases)
    print(f"📊 Результаты: {success_count}/{total_tests} тестов прошли успешно")
    
    if success_count == total_tests:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ Telegram бот готов к работе")
        return True
    else:
        print(f"⚠️  {total_tests - success_count} тестов не прошли")
        print("❌ Требуется дополнительная настройка")
        return False

def main():
    """Основная функция"""
    success = test_telegram_integration()
    
    print(f"\n📋 ЧТО БЫЛО ПРОТЕСТИРОВАНО:")
    print("   1. Конфигурация Telegram бота")
    print("   2. Инициализация бота")
    print("   3. Отправка уведомлений всех типов")
    print("   4. Обработка ошибок")
    
    print(f"\n🔧 ИНТЕГРАЦИЯ В СИСТЕМУ:")
    print("   • api_fastapi_backend.py - добавлены вызовы уведомлений")
    print("   • Все типы экспорта поддерживают Telegram")
    print("   • Автоматическая инициализация при запуске")
    print("   • Graceful handling ошибок")
    
    if success:
        print(f"\n✨ TELEGRAM БОТ ПОЛНОСТЬЮ ИНТЕГРИРОВАН!")
        print("   Теперь все Google Sheets экспорты будут")
        print("   автоматически отправлять уведомления в Telegram!")
    else:
        print(f"\n⚠️  ТРЕБУЕТСЯ НАСТРОЙКА")
        print("   Следуйте инструкциям в telegram_setup.md")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
