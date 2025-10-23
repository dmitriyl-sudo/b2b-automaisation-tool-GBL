#!/bin/bash
# Скрипт для запуска Telegram бота с командами

echo "🤖 ЗАПУСК TELEGRAM БОТА С КОМАНДАМИ"
echo "=================================="
echo ""

# Переходим в папку проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение
source myvenv/bin/activate

# Запускаем бота
python3 -c "
import asyncio
import logging
from telegram_bot import run_bot_with_commands
from telegram_config import TelegramConfig

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    print('🚀 Запуск Telegram бота...')
    
    if not TelegramConfig.is_configured():
        print('❌ Telegram бот не настроен!')
        return
    
    bot_token = TelegramConfig.get_bot_token()
    chat_id = TelegramConfig.get_chat_id()
    
    print(f'✅ Конфигурация: {bot_token[:10]}... -> {chat_id}')
    print('📋 Команды: /start, /today, /projects, /help')
    print('⏹️  Для остановки нажмите Ctrl+C')
    print('')
    
    try:
        await run_bot_with_commands(bot_token, chat_id)
    except KeyboardInterrupt:
        print('\\n⏹️  Бот остановлен')
    except Exception as e:
        print(f'\\n❌ Ошибка: {e}')

if __name__ == '__main__':
    asyncio.run(main())
"
