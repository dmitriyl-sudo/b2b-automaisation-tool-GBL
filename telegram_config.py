#!/usr/bin/env python3
"""
Конфигурация для Telegram бота
"""

import os
from typing import Optional

class TelegramConfig:
    """Класс для управления конфигурацией Telegram бота"""
    
    # Настройки по умолчанию
    DEFAULT_BOT_TOKEN = "8333234023:AAH2qzAbiVPxAuHGD1O1cL1YUQ3vjKmpe_Q"
    DEFAULT_CHAT_ID = "1445413168"
    
    @classmethod
    def get_bot_token(cls) -> Optional[str]:
        """
        Получает токен бота из переменных окружения или конфигурации
        
        Returns:
            str: Токен бота или None
        """
        return (
            os.getenv('TELEGRAM_BOT_TOKEN') or 
            cls.DEFAULT_BOT_TOKEN
        )
    
    @classmethod
    def get_chat_id(cls) -> Optional[str]:
        """
        Получает ID чата из переменных окружения или конфигурации
        
        Returns:
            str: ID чата или None
        """
        return (
            os.getenv('TELEGRAM_CHAT_ID') or 
            cls.DEFAULT_CHAT_ID
        )
    
    @classmethod
    def is_configured(cls) -> bool:
        """
        Проверяет, настроен ли Telegram бот
        
        Returns:
            bool: True если настроен
        """
        return bool(cls.get_bot_token() and cls.get_chat_id())
    
    @classmethod
    def set_credentials(cls, bot_token: str, chat_id: str):
        """
        Устанавливает учетные данные бота
        
        Args:
            bot_token: Токен бота
            chat_id: ID чата
        """
        cls.DEFAULT_BOT_TOKEN = bot_token
        cls.DEFAULT_CHAT_ID = chat_id
    
    @classmethod
    def get_setup_instructions(cls) -> str:
        """
        Возвращает инструкции по настройке бота
        
        Returns:
            str: Инструкции
        """
        return """
🤖 НАСТРОЙКА TELEGRAM БОТА

1. Создание бота:
   • Откройте @BotFather в Telegram
   • Отправьте /newbot
   • Выберите имя и username для бота
   • Скопируйте токен бота

2. Получение Chat ID:
   • Добавьте бота в группу или напишите ему лично
   • Отправьте любое сообщение боту
   • Откройте: https://api.telegram.org/bot<TOKEN>/getUpdates
   • Найдите "chat":{"id": ВАШЕ_ID}

3. Настройка переменных окружения:
   export TELEGRAM_BOT_TOKEN='1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ'
   export TELEGRAM_CHAT_ID='-1001234567890'

4. Или установите в коде:
   from telegram_config import TelegramConfig
   TelegramConfig.set_credentials('BOT_TOKEN', 'CHAT_ID')

✅ После настройки бот будет автоматически отправлять уведомления!
"""

# Пример использования
if __name__ == "__main__":
    print("🔧 КОНФИГУРАЦИЯ TELEGRAM БОТА")
    print("=" * 50)
    
    if TelegramConfig.is_configured():
        print("✅ Telegram бот настроен!")
        print(f"   Bot Token: {TelegramConfig.get_bot_token()[:10]}...")
        print(f"   Chat ID: {TelegramConfig.get_chat_id()}")
    else:
        print("❌ Telegram бот НЕ настроен")
        print(TelegramConfig.get_setup_instructions())
