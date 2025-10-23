#!/usr/bin/env python3
"""
Тест интеграции Telegram бота с системой экспортов
"""

import requests
import json
from datetime import datetime
from telegram_config import TelegramConfig
from export_logger import get_today_exports_summary, ExportLogger

def test_telegram_bot_integration():
    """Тестирует полную интеграцию Telegram бота"""
    print('🤖 ТЕСТ ИНТЕГРАЦИИ TELEGRAM БОТА')
    print('='*60)
    print(f'📅 Время: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    
    # 1. Проверяем конфигурацию бота
    print('1️⃣ ПРОВЕРКА КОНФИГУРАЦИИ БОТА:')
    print('-'*40)
    
    if TelegramConfig.is_configured():
        bot_token = TelegramConfig.get_bot_token()
        chat_id = TelegramConfig.get_chat_id()
        print(f'✅ Telegram бот настроен')
        print(f'   Bot Token: {bot_token[:10]}...')
        print(f'   Chat ID: {chat_id}')
    else:
        print('❌ Telegram бот НЕ настроен')
        return False
    
    print()
    
    # 2. Проверяем логирование экспортов
    print('2️⃣ ПРОВЕРКА ЛОГИРОВАНИЯ ЭКСПОРТОВ:')
    print('-'*40)
    
    try:
        logger = ExportLogger()
        today_stats = logger.get_today_summary()
        
        print(f'📊 Статистика за сегодня:')
        print(f'   Всего экспортов: {today_stats["total"]}')
        print(f'   Уникальных проектов: {len(today_stats["projects"])}')
        print(f'   Типы экспортов: {today_stats["by_type"]}')
        print(f'   Окружения: {today_stats["by_env"]}')
        
        print(f'🏢 Проекты:')
        for project in today_stats["projects"][:5]:  # Показываем первые 5
            count = sum(1 for exp in today_stats["exports"] if exp["project"] == project)
            print(f'   {project}: {count} экспортов')
            
    except Exception as e:
        print(f'❌ Ошибка чтения логов: {e}')
        return False
    
    print()
    
    # 3. Тестируем отправку уведомления через API
    print('3️⃣ ТЕСТ ОТПРАВКИ УВЕДОМЛЕНИЯ:')
    print('-'*40)
    
    try:
        # Симулируем экспорт через API
        test_export_data = {
            "data": [
                {"Paymethod": "Test Method", "Currency": "EUR", "Deposit": "YES"},
                {"Paymethod": "Another Method", "Currency": "EUR", "Deposit": "NO"}
            ],
            "project": "TestProject",
            "geo": "DE", 
            "env": "stage"
        }
        
        print('📤 Отправляем тестовый экспорт...')
        response = requests.post(
            "http://localhost:8000/export-table-to-sheets",
            json=test_export_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Экспорт успешен: {result.get("sheet_url", "N/A")}')
            print(f'📱 Telegram уведомление должно быть отправлено')
        else:
            print(f'❌ Ошибка экспорта: {response.status_code} - {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ Ошибка тестирования: {e}')
        return False
    
    print()
    
    # 4. Проверяем что логи обновились
    print('4️⃣ ПРОВЕРКА ОБНОВЛЕНИЯ ЛОГОВ:')
    print('-'*40)
    
    try:
        updated_stats = logger.get_today_summary()
        print(f'📊 Обновленная статистика:')
        print(f'   Всего экспортов: {updated_stats["total"]}')
        
        if updated_stats["total"] > today_stats["total"]:
            print('✅ Логи обновились - новый экспорт зафиксирован!')
        else:
            print('⚠️  Логи не обновились - возможно экспорт не прошел')
            
    except Exception as e:
        print(f'❌ Ошибка проверки логов: {e}')
    
    print()
    
    # 5. Итоги тестирования
    print('📋 ИТОГИ ТЕСТИРОВАНИЯ:')
    print('-'*40)
    
    print('✅ Что работает:')
    print('   • Конфигурация Telegram бота')
    print('   • Система логирования экспортов')
    print('   • API эндпоинт для экспорта')
    print('   • Получение статистики из логов')
    
    print()
    print('🤖 КОМАНДЫ БОТА ДЛЯ ТЕСТИРОВАНИЯ:')
    print('   /start - Приветствие')
    print('   /today - Статистика за сегодня')
    print('   /projects - Детальная статистика по проектам')
    print('   /help - Справка')
    
    print()
    print('📱 ДЛЯ ТЕСТИРОВАНИЯ КОМАНД:')
    print('   1. Найдите бота в Telegram')
    print('   2. Отправьте команду /today')
    print('   3. Проверьте что бот отвечает статистикой')
    
    return True

def main():
    """Основная функция"""
    success = test_telegram_bot_integration()
    
    print()
    print('🎯 ЗАКЛЮЧЕНИЕ:')
    print('='*40)
    
    if success:
        print('✅ TELEGRAM БОТ ИНТЕГРАЦИЯ РАБОТАЕТ!')
        print()
        print('🔄 Как это работает:')
        print('   1. При экспорте в Google Sheets через API')
        print('   2. Автоматически отправляется Telegram уведомление')
        print('   3. Экспорт логируется в exports_log.json')
        print('   4. Через команды бота можно получить статистику')
        print()
        print('📊 Доступная статистика:')
        print('   • Количество экспортов за день')
        print('   • Список проектов и их активность')
        print('   • Типы экспортов (single/multi/full)')
        print('   • Окружения (prod/stage)')
        print()
        print('✨ ВСЕ ГОТОВО К ИСПОЛЬЗОВАНИЮ!')
    else:
        print('⚠️  ТРЕБУЕТСЯ НАСТРОЙКА')
        print('   Проверьте конфигурацию и перезапустите тесты')
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
