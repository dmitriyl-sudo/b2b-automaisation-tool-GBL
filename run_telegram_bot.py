#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота с командами
"""

import asyncio
import logging
from telegram_config import TelegramConfig
from telegram_bot import run_bot_with_commands

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция"""
    print('🤖 ЗАПУСК TELEGRAM БОТА С КОМАНДАМИ')
    print('='*50)
    print()
    
    # Проверяем конфигурацию
    if not TelegramConfig.is_configured():
        print('❌ Telegram бот не настроен!')
        print()
        print('📋 Для настройки:')
        print('1. Установите переменные окружения:')
        print('   export TELEGRAM_BOT_TOKEN="your_token"')
        print('   export TELEGRAM_CHAT_ID="your_chat_id"')
        print()
        print('2. Или обновите telegram_config.py')
        print()
        return
    
    bot_token = TelegramConfig.get_bot_token()
    chat_id = TelegramConfig.get_chat_id()
    
    print('✅ Конфигурация найдена:')
    print(f'   Bot Token: {bot_token[:15]}...')
    print(f'   Chat ID: {chat_id}')
    print()
    
    print('🚀 Запуск бота...')
    print()
    print('📋 Доступные команды:')
    print('   /start - Приветствие')
    print('   /today - Статистика экспортов за сегодня')
    print('   /projects - Список проектов за сегодня')
    print('   /help - Справка')
    print()
    print('🔔 Бот также отправляет автоматические уведомления')
    print('   при создании Google Sheets файлов')
    print()
    print('⏹️  Для остановки нажмите Ctrl+C')
    print()
    
    try:
        # Запускаем бота
        await run_bot_with_commands(bot_token, chat_id)
    except KeyboardInterrupt:
        print('\n⏹️  Бот остановлен пользователем')
    except Exception as e:
        print(f'\n❌ Ошибка запуска бота: {e}')

if __name__ == "__main__":
    asyncio.run(main())
