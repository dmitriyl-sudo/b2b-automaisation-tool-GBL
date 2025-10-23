#!/usr/bin/env python3
"""
Автоматическое получение Chat ID для Telegram бота
"""

import requests
import time
import json

def get_chat_id_automatically():
    """Автоматически получает Chat ID из обновлений бота"""
    token = '8333234023:AAH2qzAbiVPxAuHGD1O1cL1YUQ3vjKmpe_Q'
    
    print('🤖 АВТОМАТИЧЕСКОЕ ПОЛУЧЕНИЕ CHAT ID')
    print('='*50)
    print()
    print('📱 ИНСТРУКЦИЯ:')
    print('1. Найдите бота: @autofile_psp_bot')
    print('2. Отправьте боту сообщение: /start')
    print('3. Скрипт автоматически получит ваш Chat ID')
    print()
    print('⏳ Ожидание сообщения...')
    print('   (Нажмите Ctrl+C для отмены)')
    print()
    
    last_update_id = 0
    
    try:
        while True:
            # Получаем новые обновления
            response = requests.get(
                f'https://api.telegram.org/bot{token}/getUpdates',
                params={'offset': last_update_id + 1, 'timeout': 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    updates = data.get('result', [])
                    
                    for update in updates:
                        last_update_id = update['update_id']
                        
                        if 'message' in update:
                            message = update['message']
                            chat = message['chat']
                            chat_id = chat['id']
                            chat_type = chat['type']
                            user_name = chat.get('first_name', 'Unknown')
                            username = chat.get('username', 'No username')
                            
                            print(f'✅ ПОЛУЧЕНО СООБЩЕНИЕ!')
                            print(f'   От: {user_name} (@{username})')
                            print(f'   Chat ID: {chat_id}')
                            print(f'   Тип чата: {chat_type}')
                            print(f'   Текст: {message.get("text", "No text")}')
                            
                            return chat_id
            else:
                print(f'❌ Ошибка HTTP: {response.status_code}')
                time.sleep(5)
                
    except KeyboardInterrupt:
        print('\n⏹️  Отменено пользователем')
        return None
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        return None

def update_config_with_chat_id(chat_id):
    """Обновляет конфигурацию с полученным Chat ID"""
    try:
        # Читаем текущий файл
        with open('telegram_config.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем DEFAULT_CHAT_ID
        updated_content = content.replace(
            'DEFAULT_CHAT_ID = None',
            f'DEFAULT_CHAT_ID = "{chat_id}"'
        )
        
        # Записываем обновленный файл
        with open('telegram_config.py', 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f'✅ Chat ID {chat_id} добавлен в telegram_config.py')
        return True
        
    except Exception as e:
        print(f'❌ Ошибка обновления конфигурации: {e}')
        return False

def test_bot_configuration():
    """Тестирует конфигурацию бота"""
    try:
        from telegram_config import TelegramConfig
        
        print('\n🧪 ТЕСТ КОНФИГУРАЦИИ:')
        print(f'   Token: {TelegramConfig.get_bot_token()[:15]}...')
        print(f'   Chat ID: {TelegramConfig.get_chat_id()}')
        print(f'   Настроен: {TelegramConfig.is_configured()}')
        
        if TelegramConfig.is_configured():
            print('\n🎉 БОТ ПОЛНОСТЬЮ НАСТРОЕН!')
            return True
        else:
            print('\n❌ Бот не настроен')
            return False
            
    except Exception as e:
        print(f'❌ Ошибка тестирования: {e}')
        return False

def main():
    """Основная функция"""
    print('🚀 АВТОМАТИЧЕСКАЯ НАСТРОЙКА TELEGRAM БОТА')
    print('='*60)
    
    # Получаем Chat ID
    chat_id = get_chat_id_automatically()
    
    if chat_id:
        print(f'\n📋 НАЙДЕН CHAT ID: {chat_id}')
        
        # Обновляем конфигурацию
        if update_config_with_chat_id(chat_id):
            # Тестируем конфигурацию
            if test_bot_configuration():
                print('\n✨ НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!')
                print('   Telegram бот готов к отправке уведомлений!')
                return True
    
    print('\n❌ Настройка не завершена')
    return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
