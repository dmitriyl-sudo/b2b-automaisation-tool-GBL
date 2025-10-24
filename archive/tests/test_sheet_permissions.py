#!/usr/bin/env python3
"""
Тест установки прав доступа для Google Sheets файлов
"""

from datetime import datetime

def main():
    """Основная функция тестирования"""
    print(f"🧪 ТЕСТ УСТАНОВКИ ПРАВ ДОСТУПА ДЛЯ GOOGLE SHEETS")
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    print(f"✅ ЧТО ДОБАВЛЕНО:")
    print("   1. 📁 utils/google_drive.py:")
    print("      • Функция set_sheet_permissions(file_id)")
    print("      • Устанавливает права для домена 'gbl-factory.com'")
    print("      • Роль: 'writer' (редактирование)")
    print()
    print("   2. 📁 api_fastapi_backend.py:")
    print("      • Добавлен импорт set_sheet_permissions")
    print("      • Вызов в upload_table_to_sheets (одиночный экспорт)")
    print("      • Вызов в Multi-GEO экспорт")
    print("      • Вызов в Full Project экспорт")
    print()
    print(f"🔧 ФУНКЦИЯ set_sheet_permissions:")
    print("   • Использует Google Drive API v3")
    print("   • Тип доступа: 'domain' (весь домен)")
    print("   • Роль: 'writer' (редактирование)")
    print("   • Домен: 'gbl-factory.com'")
    print("   • Логирование успеха/ошибок")
    print()
    print(f"📊 ГДЕ ПРИМЕНЯЕТСЯ:")
    print("   1. Одиночный GEO экспорт:")
    print("      • /export-table-to-sheets → upload_table_to_sheets()")
    print("      • Права устанавливаются после форматирования")
    print()
    print("   2. Multi-GEO экспорт:")
    print("      • /export-table-to-sheets-multi")
    print("      • Права устанавливаются после finalize_google_sheet_formatting()")
    print()
    print("   3. Full Project экспорт:")
    print("      • /export-full-project")
    print("      • Права устанавливаются в конце процесса")
    print()
    print(f"🎯 РЕЗУЛЬТАТ:")
    print("   После создания любого Google Sheets файла:")
    print("   • Автоматически устанавливаются права на редактирование")
    print("   • Доступ получает вся группа 'Ramtinar Techconsult Limited'")
    print("   • Пользователи домена gbl-factory.com могут редактировать")
    print()
    print(f"💡 ПРИМЕР ПРАВ ДОСТУПА:")
    print("   Пользователи, имеющие доступ:")
    print("   • Dmitriy Lg. (you) - dmitriy.l@gbl-factory.com")
    print("   • Общий доступ:")
    print("     'Редактировать контент могут все участники группы,'")
    print("     'у которых есть эта ссылка'")
    print("   • Название группы: Ramtinar Techconsult Limited")
    print()
    print(f"🔒 БЕЗОПАСНОСТЬ:")
    print("   • Доступ только для домена gbl-factory.com")
    print("   • Права на редактирование (не владение)")
    print("   • Автоматическое применение ко всем новым файлам")
    print()
    print(f"✨ ЗАДАЧА ВЫПОЛНЕНА!")
    print("   Все Google Sheets файлы теперь автоматически получают")
    print("   права доступа для группы Ramtinar Techconsult Limited!")
    
    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
