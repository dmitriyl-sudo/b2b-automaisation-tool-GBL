#!/usr/bin/env python3
"""
Telegram бот с исправлением event loop проблемы и массовыми уведомлениями
"""

import asyncio
import logging
import nest_asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
from telegram_config import TelegramConfig
from export_logger import ExportLogger
from user_manager import get_user_manager, add_user_from_update
from datetime import datetime

# Исправляем проблему с event loop
nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальный экземпляр бота для массовых уведомлений
_bot_instance: Bot = None

def init_bot_instance(bot_token: str):
    """Инициализирует глобальный экземпляр бота"""
    global _bot_instance
    _bot_instance = Bot(token=bot_token)
    return _bot_instance

def get_bot_instance() -> Bot:
    """Возвращает глобальный экземпляр бота"""
    return _bot_instance

async def send_notification_to_all_users(message: str, parse_mode: str = 'HTML'):
    """
    Отправляет уведомление всем активным пользователям
    
    Args:
        message: Текст сообщения
        parse_mode: Режим парсинга (HTML/Markdown)
    """
    if not _bot_instance:
        logger.error("❌ Бот не инициализирован для массовых уведомлений")
        return
    
    user_manager = get_user_manager()
    active_users = user_manager.get_all_active_users()
    
    if not active_users:
        logger.warning("⚠️ Нет активных пользователей для уведомлений")
        return
    
    success_count = 0
    error_count = 0
    
    for user_id in active_users:
        try:
            await _bot_instance.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=False
            )
            success_count += 1
            logger.debug(f"✅ Уведомление отправлено пользователю {user_id}")
            
        except TelegramError as e:
            error_count += 1
            if "bot was blocked by the user" in str(e).lower():
                logger.info(f"🔇 Пользователь {user_id} заблокировал бота")
                user_manager.deactivate_user(user_id)
            elif "chat not found" in str(e).lower():
                logger.info(f"👻 Чат {user_id} не найден")
                user_manager.deactivate_user(user_id)
            else:
                logger.error(f"❌ Ошибка отправки пользователю {user_id}: {e}")
        
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Неожиданная ошибка при отправке пользователю {user_id}: {e}")
        
        # Небольшая задержка чтобы не превысить лимиты Telegram
        await asyncio.sleep(0.1)
    
    logger.info(f"📊 Массовая рассылка завершена: ✅{success_count} успешно, ❌{error_count} ошибок")

async def send_sheet_notification_to_all(
    sheet_url: str, 
    project: str, 
    geo: str = None, 
    env: str = "prod",
    export_type: str = "single"
):
    """
    Отправляет уведомление о новом Google Sheets файле всем пользователям
    
    Args:
        sheet_url: Ссылка на Google Sheets файл
        project: Название проекта
        geo: GEO код (для одиночного экспорта)
        env: Окружение (prod/stage)
        export_type: Тип экспорта (single/multi/full)
    """
    # Формируем сообщение
    message = f"""🚀 <b>Новый Google Sheets файл создан!</b>

📋 <b>Детали:</b>
• <b>Проект:</b> {project}
• <b>Тип:</b> {export_type.title()} Export
• <b>Окружение:</b> {env.upper()}
{f'• <b>GEO:</b> {geo}' if geo else ''}
• <b>Время:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔗 <b>Ссылка:</b> <a href="{sheet_url}">Открыть Google Sheets</a>

✅ Файл готов к использованию!
🔒 Права доступа настроены автоматически"""
    
    # Отправляем всем пользователям
    await send_notification_to_all_users(message)

# Команды бота
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    # Добавляем пользователя в список
    add_user_from_update(update)
    
    user_manager = get_user_manager()
    stats = user_manager.get_users_count()
    
    welcome_message = f"""🤖 <b>B2B Automation Tool Bot</b>

Привет! Я бот для мониторинга экспортов Google Sheets.

📋 <b>Доступные команды:</b>
/today - Статистика экспортов за сегодня
/projects - Детальный список проектов
/users - Информация о пользователях (только для админов)
/help - Справка по командам

🔔 <b>Автоматические уведомления:</b>
Я автоматически уведомляю о каждом новом экспорте всех {stats['active']} активных пользователей!

✅ Вы добавлены в список для получения уведомлений!"""
    
    await update.message.reply_text(welcome_message, parse_mode='HTML')

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /today - статистика экспортов за сегодня"""
    # Добавляем пользователя в список
    add_user_from_update(update)
    
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
    # Добавляем пользователя в список
    add_user_from_update(update)
    
    try:
        export_logger = ExportLogger()
        latest_sheets = export_logger.get_latest_sheets_by_project()
        
        if not latest_sheets:
            message = "🏢 <b>Все проекты</b>\n\n❌ Экспортов еще не было"
        else:
            message = f"🏢 <b>Все проекты с последними Google Sheets</b>\n\n"
            
            for project, sheet_info in latest_sheets.items():
                sheet_url = sheet_info["sheet_url"]
                geo = sheet_info.get("geo", "N/A")
                env = sheet_info.get("env", "N/A")
                export_type = sheet_info.get("export_type", "N/A")
                date = sheet_info.get("date", "N/A")
                
                # Создаем короткую ссылку для отображения
                if "spreadsheets/d/" in sheet_url:
                    sheet_id = sheet_url.split("spreadsheets/d/")[1].split("/")[0]
                    short_id = sheet_id[:8] + "..."
                else:
                    short_id = "sheet"
                
                message += f"📁 <b>{project}</b>\n"
                message += f"   🔗 <a href='{sheet_url}'>Последний лист ({short_id})</a>\n"
                message += f"   📊 {geo} | {env} | {export_type}\n"
                message += f"   📅 {date}\n\n"
        
        await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде /projects: {e}")
        await update.message.reply_text("❌ Ошибка получения списка проектов")

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /users - информация о пользователях (только для админов)"""
    # Добавляем пользователя в список
    add_user_from_update(update)
    
    # Проверяем, является ли пользователь админом (по умолчанию - первый пользователь из конфига)
    admin_chat_id = TelegramConfig.get_chat_id()
    user_id = str(update.effective_user.id)
    
    if user_id != admin_chat_id:
        await update.message.reply_text("❌ Эта команда доступна только администраторам")
        return
    
    try:
        user_manager = get_user_manager()
        stats = user_manager.get_users_count()
        users_info = user_manager.get_users_info()
        
        message = f"""👥 <b>Пользователи бота</b>

📊 <b>Статистика:</b>
• Всего пользователей: <b>{stats['total']}</b>
• Активных: <b>{stats['active']}</b>
• Неактивных: <b>{stats['inactive']}</b>

👤 <b>Список пользователей:</b>"""
        
        for i, user in enumerate(users_info[:10], 1):  # Показываем только первых 10
            status = "✅" if user['active'] else "❌"
            last_seen = datetime.fromisoformat(user['last_seen']).strftime('%d.%m %H:%M')
            message += f"\n{i}. {status} {user['display_name']} (последний раз: {last_seen})"
        
        if len(users_info) > 10:
            message += f"\n\n... и еще {len(users_info) - 10} пользователей"
        
        message += "\n\n💡 Неактивные пользователи - те, кто заблокировал бота"
        
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде /users: {e}")
        await update.message.reply_text("❌ Ошибка получения информации о пользователях")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    # Добавляем пользователя в список
    add_user_from_update(update)
    
    user_manager = get_user_manager()
    stats = user_manager.get_users_count()
    
    help_message = f"""🆘 <b>Справка по боту</b>

📋 <b>Команды:</b>
/start - Приветствие и информация о боте
/today - Статистика экспортов за сегодня
/projects - Детальный список проектов
/users - Информация о пользователях (админы)
/help - Эта справка

🔔 <b>Автоматические уведомления:</b>
Бот автоматически отправляет уведомления о новых Google Sheets файлах всем {stats['active']} активным пользователям.

📊 <b>Статистика включает:</b>
• Общее количество экспортов
• Список проектов
• Типы экспортов (single/multi/full)
• Окружения (prod/stage)

✨ <b>Массовые уведомления:</b>
• Каждый новый экспорт отправляется всем пользователям
• Автоматическое управление заблокированными пользователями
• Работает 24/7 в реальном времени

💡 Чтобы получать уведомления, просто напишите боту любую команду!"""
    
    await update.message.reply_text(help_message, parse_mode='HTML')

def send_sheet_notification_to_all_sync(
    sheet_url: str, 
    project: str, 
    geo: str = None, 
    env: str = "prod",
    export_type: str = "single"
) -> bool:
    """
    Синхронная обертка для отправки уведомления всем пользователям
    """
    try:
        # Создаем новый event loop если его нет
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Выполняем асинхронную функцию
        return loop.run_until_complete(
            send_sheet_notification_to_all(
                sheet_url=sheet_url,
                project=project,
                geo=geo,
                env=env,
                export_type=export_type
            )
        )
    except Exception as e:
        logger.error(f"❌ Ошибка синхронной отправки всем пользователям: {e}")
        return False

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
        # Инициализируем глобальный экземпляр бота для массовых уведомлений
        init_bot_instance(bot_token)
        
        # Создаем приложение
        application = Application.builder().token(bot_token).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("today", today_command))
        application.add_handler(CommandHandler("projects", projects_command))
        application.add_handler(CommandHandler("users", users_command))
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
