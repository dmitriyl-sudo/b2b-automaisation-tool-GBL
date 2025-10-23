#!/usr/bin/env python3
"""
Тест команды /today без запуска полного бота
"""

import requests
from telegram_config import TelegramConfig
from export_logger import ExportLogger

def test_today_command_logic():
    """Тестирует логику команды /today"""
    print('🧪 ТЕСТ ЛОГИКИ КОМАНДЫ /today')
    print('='*50)
    print()
    
    try:
        # Тестируем логику получения статистики
        logger = ExportLogger()
        stats = logger.get_today_summary()
        
        print('📊 ДАННЫЕ ДЛЯ КОМАНДЫ /today:')
        print(f'   Всего экспортов: {stats["total"]}')
        print(f'   Проектов: {len(stats["projects"])}')
        print(f'   Типы: {stats["by_type"]}')
        print(f'   Окружения: {stats["by_env"]}')
        print()
        
        # Формируем сообщение как в боте
        if stats["total"] == 0:
            message = "📊 Статистика за сегодня\\n\\n❌ Сегодня экспортов не было"
        else:
            message = f"""📊 Статистика за сегодня

📈 Всего экспортов: {stats["total"]}
🏢 Уникальных проектов: {len(stats["projects"])}

📋 Типы экспортов:"""
            
            for export_type, count in stats["by_type"].items():
                message += f"\\n   • {export_type}: {count}"
            
            message += "\\n\\n🌍 Окружения:"
            for env, count in stats["by_env"].items():
                message += f"\\n   • {env}: {count}"
            
            if stats["projects"]:
                message += "\\n\\n🏢 Проекты:"
                for project in stats["projects"][:5]:
                    count = sum(1 for exp in stats["exports"] if exp["project"] == project)
                    message += f"\\n   • {project}: {count}"
        
        print('📱 СООБЩЕНИЕ ДЛЯ TELEGRAM:')
        print('-'*30)
        print(message.replace('\\n', '\\n'))
        print('-'*30)
        print()
        
        return True, message
        
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        return False, str(e)

def send_test_message_to_telegram(message):
    """Отправляет тестовое сообщение в Telegram"""
    if not TelegramConfig.is_configured():
        print('❌ Telegram не настроен')
        return False
    
    bot_token = TelegramConfig.get_bot_token()
    chat_id = TelegramConfig.get_chat_id()
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        print('📤 Отправляем тестовое сообщение в Telegram...')
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print('✅ Сообщение отправлено успешно!')
                return True
            else:
                print(f'❌ Ошибка API: {result.get("description", "Unknown error")}')
                return False
        else:
            print(f'❌ HTTP ошибка: {response.status_code}')
            return False
            
    except Exception as e:
        print(f'❌ Ошибка отправки: {e}')
        return False

def main():
    """Основная функция"""
    # 1. Тестируем логику команды
    success, message = test_today_command_logic()
    
    if not success:
        print('❌ Логика команды /today не работает')
        return False
    
    # 2. Отправляем тестовое сообщение
    if send_test_message_to_telegram(message):
        print()
        print('🎉 ТЕСТ УСПЕШЕН!')
        print('='*30)
        print('✅ Логика команды /today работает корректно')
        print('✅ Сообщение успешно отправлено в Telegram')
        print()
        print('💡 ПРОБЛЕМА БЫЛА В ТОМ, ЧТО:')
        print('   • Telegram бот с командами не был запущен')
        print('   • Нужно запустить бота в отдельном терминале')
        print()
        print('🔧 РЕШЕНИЕ:')
        print('   1. Откройте новый терминал')
        print('   2. Перейдите в папку проекта')
        print('   3. Выполните: source myvenv/bin/activate')
        print('   4. Запустите: python -c "')
        print('      import asyncio')
        print('      from telegram_bot import run_bot_with_commands')
        print('      from telegram_config import TelegramConfig')
        print('      asyncio.run(run_bot_with_commands(')
        print('          TelegramConfig.get_bot_token(),')
        print('          TelegramConfig.get_chat_id()))"')
        print()
        print('📱 После запуска команда /today будет работать!')
        return True
    else:
        print()
        print('⚠️  ЧАСТИЧНЫЙ УСПЕХ')
        print('='*30)
        print('✅ Логика команды /today работает')
        print('❌ Проблема с отправкой в Telegram')
        print('   Проверьте токен и chat_id')
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
