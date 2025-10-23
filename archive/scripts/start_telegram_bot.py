#!/usr/bin/env python3
"""
Простой запуск Telegram бота с командами (без конфликтов event loop)
"""

import subprocess
import sys
import os
from telegram_config import TelegramConfig

def start_telegram_bot():
    """Запускает Telegram бота в отдельном процессе"""
    print('🤖 ЗАПУСК TELEGRAM БОТА С КОМАНДАМИ')
    print('='*50)
    print()
    
    # Проверяем конфигурацию
    if not TelegramConfig.is_configured():
        print('❌ Telegram бот не настроен!')
        print()
        print('📋 Для настройки обновите telegram_config.py')
        return False
    
    bot_token = TelegramConfig.get_bot_token()
    chat_id = TelegramConfig.get_chat_id()
    
    print('✅ Конфигурация найдена:')
    print(f'   Bot Token: {bot_token[:15]}...')
    print(f'   Chat ID: {chat_id}')
    print()
    
    print('🚀 Запуск бота в фоновом режиме...')
    
    # Создаем простой скрипт для запуска
    bot_script = f'''
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from export_logger import ExportLogger

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Команды бота
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    welcome_message = """
🤖 <b>B2B Automation Tool Bot</b>

Привет! Я бот для мониторинга экспортов Google Sheets.

📋 <b>Доступные команды:</b>
/today - Статистика экспортов за сегодня
/projects - Детальный список проектов
/help - Справка по командам

🔔 Я автоматически уведомляю о каждом новом экспорте!
"""
    await update.message.reply_text(welcome_message, parse_mode='HTML')

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /today - статистика экспортов за сегодня"""
    try:
        logger = ExportLogger()
        stats = logger.get_today_summary()
        
        if stats["total"] == 0:
            message = "📊 <b>Статистика за сегодня</b>\\n\\n❌ Сегодня экспортов не было"
        else:
            message = f"""📊 <b>Статистика за сегодня</b>

📈 Всего экспортов: <b>{{stats["total"]}}</b>
🏢 Уникальных проектов: <b>{{len(stats["projects"])}}</b>

📋 <b>Типы экспортов:</b>"""
            
            for export_type, count in stats["by_type"].items():
                message += f"\\n   • {{export_type}}: {{count}}"
            
            message += "\\n\\n🌍 <b>Окружения:</b>"
            for env, count in stats["by_env"].items():
                message += f"\\n   • {{env}}: {{count}}"
            
            if stats["projects"]:
                message += "\\n\\n🏢 <b>Проекты:</b>"
                for project in stats["projects"][:5]:
                    count = sum(1 for exp in stats["exports"] if exp["project"] == project)
                    message += f"\\n   • {{project}}: {{count}}"
        
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде /today: {{e}}")
        await update.message.reply_text("❌ Ошибка получения статистики")

async def projects_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /projects - список проектов"""
    try:
        logger = ExportLogger()
        stats = logger.get_today_summary()
        
        if stats["total"] == 0:
            message = "🏢 <b>Проекты за сегодня</b>\\n\\n❌ Сегодня экспортов не было"
        else:
            message = f"🏢 <b>Проекты за сегодня</b>\\n\\n"
            
            for project in stats["projects"]:
                project_exports = [exp for exp in stats["exports"] if exp["project"] == project]
                count = len(project_exports)
                
                # Типы экспортов для проекта
                types = {{}}
                envs = {{}}
                
                for exp in project_exports:
                    exp_type = exp.get("export_type", "unknown")
                    env = exp.get("env", "unknown")
                    types[exp_type] = types.get(exp_type, 0) + 1
                    envs[env] = envs.get(env, 0) + 1
                
                message += f"📁 <b>{{project}}</b> ({{count}} экспортов)\\n"
                
                if types:
                    type_str = ", ".join([f"{{k}}({{v}})" for k, v in types.items()])
                    message += f"   📋 Типы: {{type_str}}\\n"
                
                if envs:
                    env_str = ", ".join([f"{{k}}({{v}})" for k, v in envs.items()])
                    message += f"   🌍 Окружения: {{env_str}}\\n"
                
                message += "\\n"
        
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде /projects: {{e}}")
        await update.message.reply_text("❌ Ошибка получения списка проектов")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_message = """
🆘 <b>Справка по боту</b>

📋 <b>Команды:</b>
/start - Приветствие и информация о боте
/today - Статистика экспортов за сегодня
/projects - Детальный список проектов за сегодня
/help - Эта справка

🔔 <b>Автоматические уведомления:</b>
Бот автоматически отправляет уведомления при каждом экспорте в Google Sheets.

📊 <b>Статистика включает:</b>
• Общее количество экспортов
• Список проектов
• Типы экспортов (single/multi/full)
• Окружения (prod/stage)

✨ Бот работает 24/7 и отслеживает все экспорты!
"""
    await update.message.reply_text(help_message, parse_mode='HTML')

async def main():
    """Основная функция бота"""
    # Создаем приложение
    application = Application.builder().token("{bot_token}").build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("projects", projects_command))
    application.add_handler(CommandHandler("help", help_command))
    
    print("🤖 Telegram бот запущен и готов к работе!")
    print("📋 Доступные команды: /start, /today, /projects, /help")
    print("⏹️  Для остановки нажмите Ctrl+C")
    
    # Запускаем бота
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Записываем скрипт во временный файл
    script_path = "temp_telegram_bot.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(bot_script)
    
    print('📋 Доступные команды:')
    print('   /start - Приветствие')
    print('   /today - Статистика экспортов за сегодня')
    print('   /projects - Список проектов за сегодня')
    print('   /help - Справка')
    print()
    print('🔔 Бот также отправляет автоматические уведомления')
    print('   при создании Google Sheets файлов')
    print()
    
    try:
        # Запускаем скрипт
        result = subprocess.run([
            sys.executable, script_path
        ], cwd=os.getcwd())
        
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print('\\n⏹️  Бот остановлен пользователем')
        return True
    except Exception as e:
        print(f'\\n❌ Ошибка запуска: {e}')
        return False
    finally:
        # Удаляем временный файл
        if os.path.exists(script_path):
            os.remove(script_path)

if __name__ == "__main__":
    success = start_telegram_bot()
    sys.exit(0 if success else 1)
