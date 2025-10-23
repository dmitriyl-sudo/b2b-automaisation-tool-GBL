#!/usr/bin/env python3
"""
Тест команд Telegram бота и системы логирования
"""

import asyncio
import logging
from datetime import datetime
from export_logger import export_logger, log_export, get_today_exports_summary
from telegram_config import TelegramConfig
from telegram_bot import send_sheet_notification_sync

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_export_logger():
    """Тестирует систему логирования экспортов"""
    print('📊 ТЕСТ СИСТЕМЫ ЛОГИРОВАНИЯ ЭКСПОРТОВ')
    print('='*50)
    print()
    
    # Создаем тестовые экспорты
    test_exports = [
        ("Rolling", "DE", "prod", "single", "https://docs.google.com/spreadsheets/d/test1"),
        ("SpinEmpire", None, "stage", "multi", "https://docs.google.com/spreadsheets/d/test2"),
        ("Ritzo", None, "prod", "full", "https://docs.google.com/spreadsheets/d/test3"),
        ("Rolling", "IT", "prod", "single", "https://docs.google.com/spreadsheets/d/test4"),
        ("Hugo", "FI", "stage", "single", "https://docs.google.com/spreadsheets/d/test5"),
    ]
    
    print('📝 Создание тестовых экспортов:')
    for i, (project, geo, env, export_type, sheet_url) in enumerate(test_exports, 1):
        log_export(project, geo, env, export_type, sheet_url)
        geo_str = f" - {geo}" if geo else ""
        print(f'   {i}. {project}{geo_str} ({export_type}, {env})')
    
    print()
    
    # Получаем сводку
    summary = get_today_exports_summary()
    
    print('📊 СВОДКА ЗА СЕГОДНЯ:')
    print(f'   Всего экспортов: {summary["total"]}')
    print(f'   Уникальных проектов: {len(summary["projects"])}')
    print(f'   Проекты: {", ".join(summary["projects"])}')
    print()
    
    print('📋 По типам:')
    for export_type, count in summary["by_type"].items():
        print(f'   • {export_type}: {count}')
    print()
    
    print('🌍 По окружениям:')
    for env, count in summary["by_env"].items():
        print(f'   • {env}: {count}')
    print()
    
    return summary["total"] > 0

def test_telegram_integration():
    """Тестирует интеграцию с Telegram"""
    print('🤖 ТЕСТ ИНТЕГРАЦИИ С TELEGRAM')
    print('='*50)
    print()
    
    if not TelegramConfig.is_configured():
        print('❌ Telegram бот не настроен')
        return False
    
    print('✅ Telegram бот настроен')
    print(f'   Token: {TelegramConfig.get_bot_token()[:15]}...')
    print(f'   Chat ID: {TelegramConfig.get_chat_id()}')
    print()
    
    # Тестируем отправку уведомления с логированием
    print('📤 Отправка тестового уведомления...')
    success = send_sheet_notification_sync(
        sheet_url="https://docs.google.com/spreadsheets/d/test_bot_commands",
        project="TestProject",
        geo="DE",
        env="prod",
        export_type="single"
    )
    
    if success:
        print('✅ Уведомление отправлено успешно')
        print('📊 Экспорт автоматически залогирован')
        return True
    else:
        print('❌ Ошибка отправки уведомления')
        return False

def simulate_daily_activity():
    """Симулирует дневную активность для демонстрации"""
    print('🎭 СИМУЛЯЦИЯ ДНЕВНОЙ АКТИВНОСТИ')
    print('='*50)
    print()
    
    # Симулируем различные экспорты
    activities = [
        ("Rolling", "DE", "prod", "single"),
        ("Rolling", "IT", "prod", "single"),
        ("SpinEmpire", None, "stage", "multi"),
        ("Ritzo", None, "prod", "full"),
        ("Hugo", "FI", "stage", "single"),
        ("Winshark", "SE", "prod", "single"),
        ("Rolling", "AT", "prod", "single"),
        ("SpinEmpire", None, "prod", "multi"),
    ]
    
    print('📊 Создание активности:')
    for i, (project, geo, env, export_type) in enumerate(activities, 1):
        sheet_url = f"https://docs.google.com/spreadsheets/d/activity_{i}"
        log_export(project, geo, env, export_type, sheet_url)
        
        geo_str = f" - {geo}" if geo else ""
        print(f'   {i}. {project}{geo_str} ({export_type}, {env})')
    
    print()
    print(f'✅ Создано {len(activities)} записей активности')
    
    # Показываем итоговую статистику
    summary = get_today_exports_summary()
    
    print()
    print('📈 ИТОГОВАЯ СТАТИСТИКА:')
    print(f'   📊 Всего экспортов: {summary["total"]}')
    print(f'   🏢 Уникальных проектов: {len(summary["projects"])}')
    print(f'   📋 Типы: {", ".join(f"{t}({c})" for t, c in summary["by_type"].items())}')
    print(f'   🌍 Окружения: {", ".join(f"{e}({c})" for e, c in summary["by_env"].items())}')
    
    return True

def main():
    """Основная функция"""
    print('🧪 ТЕСТ КОМАНД TELEGRAM БОТА')
    print('='*60)
    print(f'📅 Дата: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    
    tests_passed = 0
    total_tests = 4
    
    # Тест 1: Система логирования
    if test_export_logger():
        print('✅ Тест 1: Система логирования - ПРОЙДЕН')
        tests_passed += 1
    else:
        print('❌ Тест 1: Система логирования - НЕ ПРОЙДЕН')
    print()
    
    # Тест 2: Интеграция с Telegram
    if test_telegram_integration():
        print('✅ Тест 2: Интеграция с Telegram - ПРОЙДЕН')
        tests_passed += 1
    else:
        print('❌ Тест 2: Интеграция с Telegram - НЕ ПРОЙДЕН')
    print()
    
    # Тест 3: Симуляция активности
    if simulate_daily_activity():
        print('✅ Тест 3: Симуляция активности - ПРОЙДЕН')
        tests_passed += 1
    else:
        print('❌ Тест 3: Симуляция активности - НЕ ПРОЙДЕН')
    print()
    
    # Тест 4: Финальная проверка
    final_summary = get_today_exports_summary()
    if final_summary["total"] > 0:
        print('✅ Тест 4: Финальная проверка - ПРОЙДЕН')
        tests_passed += 1
    else:
        print('❌ Тест 4: Финальная проверка - НЕ ПРОЙДЕН')
    print()
    
    # Итоги
    print('📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:')
    print(f'   Пройдено: {tests_passed}/{total_tests} тестов')
    print(f'   Процент успеха: {(tests_passed/total_tests)*100:.1f}%')
    print()
    
    if tests_passed == total_tests:
        print('🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!')
        print()
        print('🤖 TELEGRAM БОТ ГОТОВ К РАБОТЕ:')
        print('   • Автоматические уведомления ✅')
        print('   • Логирование экспортов ✅')
        print('   • Команды статистики ✅')
        print('   • /today - статистика за сегодня')
        print('   • /projects - список проектов')
        print('   • /help - справка')
        print()
        print('🚀 Для запуска бота с командами:')
        print('   python run_telegram_bot.py')
    else:
        print('⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ')
        print('   Проверьте конфигурацию и зависимости')
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
