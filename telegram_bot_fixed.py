#!/usr/bin/env python3
"""
Telegram бот с исправлением event loop проблемы
"""

import asyncio
import logging
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram_config import TelegramConfig
from export_logger import ExportLogger

# Исправляем проблему с event loop
nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        export_logger = ExportLogger()
        stats = export_logger.get_today_summary()
        
        if stats["total"] == 0:
            message = "📊 <b>Статистика за сегодня</b>\n\n❌ Сегодня экспортов не было"
        else:
            message = f"""📊 <b>Статистика за сегодня</b>

📈 Всего экспортов: <b>{stats["total"]}</b>
🏢 Уникальных проектов: <b>{len(stats["projects"])}</b>

📋 <b>Типы экспортов:</b>"""
            
            for export_type, count in stats["by_type"].items():
                message += f"\n   • {export_type}: {count}"
            
            message += "\n\n🌍 <b>Окружения:</b>"
            for env, count in stats["by_env"].items():
                message += f"\n   • {env}: {count}"
            
            if stats["projects"]:
                message += "\n\n🏢 <b>Проекты:</b>"
                for project in stats["projects"][:5]:
                    count = sum(1 for exp in stats["exports"] if exp["project"] == project)
                    message += f"\n   • {project}: {count}"
        
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде /today: {e}")
        await update.message.reply_text("❌ Ошибка получения статистики")

async def projects_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /projects - список проектов с последними ссылками на Google Sheets"""
    try:
        export_logger = ExportLogger()
        stats = export_logger.get_today_summary()
        latest_sheets = export_logger.get_latest_sheets_by_project()
        
        if stats["total"] == 0:
            message = "🏢 <b>Проекты за сегодня</b>\n\n❌ Сегодня экспортов не было"
        else:
            message = f"🏢 <b>Проекты с последними Google Sheets</b>\n\n"
            
            for project in stats["projects"]:
                project_exports = [exp for exp in stats["exports"] if exp["project"] == project]
                count = len(project_exports)
                
                # Типы экспортов для проекта
                types = {}
                envs = {}
                
                for exp in project_exports:
                    exp_type = exp.get("export_type", "unknown")
                    env = exp.get("env", "unknown")
                    types[exp_type] = types.get(exp_type, 0) + 1
                    envs[env] = envs.get(env, 0) + 1
                
                message += f"📁 <b>{project}</b> ({count} экспортов)\n"
                
                # Добавляем ссылку на последний Google Sheets
                if project in latest_sheets:
                    sheet_info = latest_sheets[project]
                    sheet_url = sheet_info["sheet_url"]
                    geo = sheet_info.get("geo", "N/A")
                    env = sheet_info.get("env", "N/A")
                    export_type = sheet_info.get("export_type", "N/A")
                    
                    # Создаем короткую ссылку для отображения
                    if "spreadsheets/d/" in sheet_url:
                        sheet_id = sheet_url.split("spreadsheets/d/")[1].split("/")[0]
                        short_id = sheet_id[:8] + "..."
                    else:
                        short_id = "sheet"
                    
                    message += f"   🔗 <a href='{sheet_url}'>Последний лист ({short_id})</a>\n"
                    message += f"   📊 {geo} | {env} | {export_type}\n"
                else:
                    message += f"   ❌ Нет ссылок на Google Sheets\n"
                
                if types:
                    type_str = ", ".join([f"{k}({v})" for k, v in types.items()])
                    message += f"   📋 Типы: {type_str}\n"
                
                if envs:
                    env_str = ", ".join([f"{k}({v})" for k, v in envs.items()])
                    message += f"   🌍 Окружения: {env_str}\n"
                
                message += "\n"
        
        await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде /projects: {e}")
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

def run_bot():
    """Запуск бота с исправлением event loop"""
    print("🤖 ЗАПУСК TELEGRAM БОТА (ИСПРАВЛЕННАЯ ВЕРСИЯ)")
    print("=" * 60)
    
    # Проверяем конфигурацию
    if not TelegramConfig.is_configured():
        print("❌ Telegram бот не настроен!")
        return
    
    bot_token = TelegramConfig.get_bot_token()
    chat_id = TelegramConfig.get_chat_id()
    
    print(f"✅ Конфигурация: {bot_token[:10]}... -> {chat_id}")
    print("📋 Команды: /start, /today, /projects, /help")
    print("⏹️  Для остановки нажмите Ctrl+C")
    print()
    
    try:
        # Создаем приложение
        application = Application.builder().token(bot_token).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("today", today_command))
        application.add_handler(CommandHandler("projects", projects_command))
        application.add_handler(CommandHandler("help", help_command))
        
        print("🚀 Telegram бот запущен и готов к работе!")
        
        # Запускаем бота с исправлением event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Если loop уже запущен, создаем задачу
            task = loop.create_task(application.run_polling())
            print("✅ Бот запущен в существующем event loop")
            return task
        else:
            # Если loop не запущен, запускаем обычным способом
            loop.run_until_complete(application.run_polling())
            
    except KeyboardInterrupt:
        print("\n⏹️  Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        logger.error(f"Ошибка запуска бота: {e}")

if __name__ == "__main__":
    # Устанавливаем nest_asyncio для исправления event loop
    try:
        import nest_asyncio
        nest_asyncio.apply()
        print("✅ nest_asyncio применен")
    except ImportError:
        print("⚠️  nest_asyncio не установлен, устанавливаем...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "nest-asyncio"])
        import nest_asyncio
        nest_asyncio.apply()
        print("✅ nest_asyncio установлен и применен")
    
    run_bot()
