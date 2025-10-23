#!/usr/bin/env python3
"""
Telegram бот для уведомлений о Google Sheets экспортах
"""

import asyncio
import logging
import os
from datetime import datetime, date
from typing import Optional
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импортируем логгер экспортов
try:
    from export_logger import get_today_exports_summary, export_logger
    EXPORT_LOGGER_AVAILABLE = True
except ImportError:
    EXPORT_LOGGER_AVAILABLE = False
    logger.warning("⚠️ Export logger не найден. Команды статистики недоступны.")

class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Инициализация Telegram бота
        
        Args:
            bot_token: Токен бота от @BotFather
            chat_id: ID чата или канала для отправки уведомлений
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token)
        
    async def send_sheet_notification(
        self, 
        sheet_url: str, 
        project: str, 
        geo: str = None, 
        env: str = "prod",
        export_type: str = "single"
    ) -> bool:
        """
        Отправляет уведомление о созданном Google Sheets файле
        
        Args:
            sheet_url: Ссылка на Google Sheets файл
            project: Название проекта
            geo: GEO код (для одиночного экспорта)
            env: Окружение (prod/stage)
            export_type: Тип экспорта (single/multi/full)
            
        Returns:
            bool: True если отправлено успешно, False если ошибка
        """
        try:
            # Формируем сообщение в зависимости от типа экспорта
            if export_type == "single":
                title = f"📊 {project} - {geo} ({env.upper()})"
                description = f"Создан экспорт для {geo} в проекте {project}"
            elif export_type == "multi":
                title = f"📊 {project} - Multi-GEO ({env.upper()})"
                description = f"Создан Multi-GEO экспорт для проекта {project}"
            elif export_type == "full":
                title = f"📊 {project} - Full Export ({env.upper()})"
                description = f"Создан полный экспорт проекта {project}"
            else:
                title = f"📊 {project} - Export ({env.upper()})"
                description = f"Создан экспорт для проекта {project}"
            
            # Формируем текст сообщения
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

            # Отправляем сообщение
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
            
            # Логируем экспорт
            if EXPORT_LOGGER_AVAILABLE:
                try:
                    from export_logger import log_export
                    log_export(project, geo, env, export_type, sheet_url)
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка логирования экспорта: {e}")
            
            logger.info(f"✅ Уведомление отправлено: {title}")
            return True
            
        except TelegramError as e:
            logger.error(f"❌ Ошибка отправки в Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Тестирует подключение к Telegram боту
        
        Returns:
            bool: True если подключение успешно
        """
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Бот подключен: @{bot_info.username}")
            
            # Отправляем тестовое сообщение
            test_message = f"""🤖 <b>Telegram Bot активирован!</b>

📋 <b>Информация о боте:</b>
• <b>Имя:</b> {bot_info.first_name}
• <b>Username:</b> @{bot_info.username}
• <b>ID:</b> {bot_info.id}
• <b>Время:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ Бот готов к отправке уведомлений о Google Sheets!"""

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=test_message,
                parse_mode='HTML'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к боту: {e}")
            return False

# Глобальный экземпляр уведомителя
_telegram_notifier: Optional[TelegramNotifier] = None

def init_telegram_bot(bot_token: str, chat_id: str) -> TelegramNotifier:
    """
    Инициализирует Telegram бота
    
    Args:
        bot_token: Токен бота
        chat_id: ID чата
        
    Returns:
        TelegramNotifier: Экземпляр уведомителя
    """
    global _telegram_notifier
    _telegram_notifier = TelegramNotifier(bot_token, chat_id)
    return _telegram_notifier

def get_telegram_notifier() -> Optional[TelegramNotifier]:
    """
    Возвращает глобальный экземпляр уведомителя
    
    Returns:
        TelegramNotifier или None если не инициализирован
    """
    return _telegram_notifier

async def send_sheet_notification_async(
    sheet_url: str, 
    project: str, 
    geo: str = None, 
    env: str = "prod",
    export_type: str = "single"
) -> bool:
    """
    Асинхронная функция для отправки уведомления
    """
    notifier = get_telegram_notifier()
    if not notifier:
        logger.warning("⚠️ Telegram бот не инициализирован")
        return False
    
    return await notifier.send_sheet_notification(
        sheet_url=sheet_url,
        project=project,
        geo=geo,
        env=env,
        export_type=export_type
    )

def send_sheet_notification_sync(
    sheet_url: str, 
    project: str, 
    geo: str = None, 
    env: str = "prod",
    export_type: str = "single"
) -> bool:
    """
    Синхронная обертка для отправки уведомления
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
            send_sheet_notification_async(
                sheet_url=sheet_url,
                project=project,
                geo=geo,
                env=env,
                export_type=export_type
            )
        )
    except Exception as e:
        logger.error(f"❌ Ошибка синхронной отправки: {e}")
        return False

# Команды для Telegram бота
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    welcome_message = """
🤖 <b>B2B Automation Tool Bot</b>

Привет! Я бот для уведомлений о Google Sheets экспортах.

📋 <b>Доступные команды:</b>
• /start - Показать это сообщение
• /today - Статистика экспортов за сегодня
• /projects - Список проектов за сегодня
• /help - Справка

🔔 <b>Автоматические уведомления:</b>
Я автоматически отправляю уведомления при создании новых Google Sheets файлов через систему экспорта.

✨ Готов к работе!
"""
    await update.message.reply_text(welcome_message, parse_mode='HTML')

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /today - статистика экспортов за сегодня"""
    if not EXPORT_LOGGER_AVAILABLE:
        await update.message.reply_text("❌ Система логирования экспортов недоступна")
        return
    
    try:
        summary = get_today_exports_summary()
        
        if summary["total"] == 0:
            message = f"""
📊 <b>Статистика экспортов за сегодня</b>
📅 {date.today().strftime('%d.%m.%Y')}

🔍 Экспортов не найдено
"""
        else:
            # Формируем сообщение со статистикой
            projects_list = "\n".join([f"   • {project}" for project in summary["projects"]])
            
            types_list = "\n".join([
                f"   • {export_type}: {count}" 
                for export_type, count in summary["by_type"].items()
            ])
            
            envs_list = "\n".join([
                f"   • {env}: {count}" 
                for env, count in summary["by_env"].items()
            ])
            
            message = f"""
📊 <b>Статистика экспортов за сегодня</b>
📅 {date.today().strftime('%d.%m.%Y')}

📈 <b>Общая статистика:</b>
   • Всего экспортов: {summary["total"]}
   • Уникальных проектов: {len(summary["projects"])}

🏢 <b>Проекты ({len(summary["projects"])}):</b>
{projects_list}

📋 <b>По типам:</b>
{types_list}

🌍 <b>По окружениям:</b>
{envs_list}
"""
        
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде /today: {e}")
        await update.message.reply_text("❌ Ошибка получения статистики")

async def projects_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /projects - список проектов за сегодня с деталями"""
    if not EXPORT_LOGGER_AVAILABLE:
        await update.message.reply_text("❌ Система логирования экспортов недоступна")
        return
    
    try:
        summary = get_today_exports_summary()
        
        if summary["total"] == 0:
            message = f"""
🏢 <b>Проекты за сегодня</b>
📅 {date.today().strftime('%d.%m.%Y')}

🔍 Экспортов не найдено
"""
        else:
            # Группируем экспорты по проектам
            projects_data = {}
            for export in summary["exports"]:
                project = export["project"]
                if project not in projects_data:
                    projects_data[project] = []
                projects_data[project].append(export)
            
            # Формируем детальный список
            projects_details = []
            for project, exports in sorted(projects_data.items()):
                export_count = len(exports)
                latest_export = max(exports, key=lambda x: x["timestamp"])
                latest_time = datetime.fromisoformat(latest_export["timestamp"]).strftime('%H:%M')
                
                # Подсчитываем типы экспортов для проекта
                types = {}
                for export in exports:
                    export_type = export.get("export_type", "unknown")
                    types[export_type] = types.get(export_type, 0) + 1
                
                types_str = ", ".join([f"{t}({c})" for t, c in types.items()])
                
                projects_details.append(
                    f"   • <b>{project}</b> - {export_count} экспорт(ов)\n"
                    f"     Типы: {types_str}\n"
                    f"     Последний: {latest_time}"
                )
            
            projects_list = "\n\n".join(projects_details)
            
            message = f"""
🏢 <b>Проекты за сегодня</b>
📅 {date.today().strftime('%d.%m.%Y')}

📊 <b>Всего: {len(projects_data)} проектов, {summary["total"]} экспортов</b>

{projects_list}

💡 Используйте /today для общей статистики
"""
        
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде /projects: {e}")
        await update.message.reply_text("❌ Ошибка получения списка проектов")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_message = """
🆘 <b>Справка по боту</b>

📋 <b>Команды:</b>
• /start - Приветствие и основная информация
• /today - Статистика экспортов за сегодня
• /projects - Детальный список проектов за сегодня
• /help - Эта справка

🔔 <b>Автоматические уведомления:</b>
Бот отправляет уведомления при создании Google Sheets файлов:
• Single GEO Export - экспорт одного GEO
• Multi-GEO Export - экспорт нескольких GEO
• Full Project Export - полный экспорт проекта

📊 <b>Статистика:</b>
Бот ведет учет всех экспортов и может показать:
• Количество экспортов за день
• Список проектов
• Типы экспортов (single/multi/full)
• Окружения (prod/stage)

🔧 <b>Техническая информация:</b>
• Бот работает 24/7
• Данные обновляются в реальном времени
• История экспортов сохраняется

❓ <b>Проблемы?</b>
Если бот не отвечает или работает некорректно, обратитесь к администратору.
"""
    await update.message.reply_text(help_message, parse_mode='HTML')

def setup_bot_commands(application: Application):
    """Настройка команд бота"""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("projects", projects_command))
    application.add_handler(CommandHandler("help", help_command))

async def run_bot_with_commands(bot_token: str, chat_id: str):
    """Запускает бота с командами"""
    try:
        # Создаем приложение
        application = Application.builder().token(bot_token).build()
        
        # Настраиваем команды
        setup_bot_commands(application)
        
        # Запускаем бота
        logger.info("🤖 Запуск Telegram бота с командами...")
        await application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")

async def main():
    """Тестирование бота"""
    # Загружаем настройки из переменных окружения
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Установите переменные окружения:")
        print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id'")
        return
    
    # Инициализируем бота
    notifier = init_telegram_bot(bot_token, chat_id)
    
    # Тестируем подключение
    if await notifier.test_connection():
        print("✅ Telegram бот успешно подключен!")
        
        # Тестируем отправку уведомления
        await notifier.send_sheet_notification(
            sheet_url="https://docs.google.com/spreadsheets/d/test123",
            project="Rolling",
            geo="DE",
            env="prod",
            export_type="single"
        )
    else:
        print("❌ Ошибка подключения к Telegram боту")

if __name__ == "__main__":
    asyncio.run(main())
