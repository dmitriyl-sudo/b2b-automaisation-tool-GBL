#!/usr/bin/env python3
"""
Тест нового SpinEmpire экстрактора с обязательным Binance Pay
"""

import requests
import json
from datetime import datetime

def test_spinempire_binance():
    """Тестирует что SpinEmpire всегда возвращает Binance Pay"""
    print('🧪 ТЕСТ SPINEMPIRE ЭКСТРАКТОРА С BINANCE PAY')
    print('='*60)
    print(f'📅 Время: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    
    # Тестовые случаи
    test_cases = [
        {"geo": "DE", "env": "stage", "description": "🇩🇪 Германия Stage"},
        {"geo": "IT", "env": "stage", "description": "🇮🇹 Италия Stage"},
        {"geo": "FI", "env": "prod", "description": "🇫🇮 Финляндия Prod"},
        {"geo": "PL_PLN", "env": "stage", "description": "🇵🇱 Польша PLN Stage"},
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f'{i}. {test_case["description"]}')
        
        try:
            # Запрос к API
            response = requests.post(
                "http://localhost:8000/get-methods-only",
                json={
                    "project": "SpinEmpire",
                    "geo": test_case["geo"],
                    "login": "test",
                    "env": test_case["env"]
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f'   ❌ HTTP {response.status_code}: {response.text}')
                continue
            
            data = response.json()
            methods = data.get('methods', [])
            
            # Ищем Binance Pay
            binance_methods = [
                m for m in methods 
                if 'binance' in m.get('title', '').lower() or 
                   'binance' in m.get('name', '').lower()
            ]
            
            print(f'   📊 Всего методов: {len(methods)}')
            print(f'   🎯 Binance Pay методов: {len(binance_methods)}')
            
            if binance_methods:
                print(f'   ✅ Binance Pay найден!')
                for method in binance_methods:
                    title = method.get('title', 'N/A')
                    name = method.get('name', 'N/A')
                    is_test = method.get('is_test_method', False)
                    print(f'      - {title} ({name}) {"[ТЕСТ]" if is_test else "[API]"}')
                success_count += 1
            else:
                print(f'   ❌ Binance Pay НЕ найден!')
            
            # Показываем первые методы
            print(f'   📋 Первые 3 метода:')
            for j, method in enumerate(methods[:3]):
                title = method.get('title', 'N/A')
                name = method.get('name', 'N/A')
                print(f'      {j+1}. {title} ({name})')
                
        except Exception as e:
            print(f'   ❌ Ошибка: {e}')
        
        print()
    
    # Итоги
    print('📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:')
    print(f'   Успешных тестов: {success_count}/{total_tests}')
    print(f'   Процент успеха: {(success_count/total_tests)*100:.1f}%')
    print()
    
    if success_count == total_tests:
        print('🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!')
        print('✅ SpinEmpire экстрактор ВСЕГДА возвращает Binance Pay')
        print('✅ Новый экстрактор работает корректно')
        print('✅ Основан на проверенном Rolling экстракторе')
        print()
        print('🔧 ОСОБЕННОСТИ НОВОГО ЭКСТРАКТОРА:')
        print('   • Автоматическое добавление Binance Pay если его нет в API')
        print('   • Сохранение API порядка методов')
        print('   • Правильная группировка криптовалют')
        print('   • Маркировка тестовых методов')
        print('   • Логирование для отладки')
        return True
    else:
        print('⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ')
        print('   Проверьте логи бэкенда для диагностики')
        return False

def main():
    """Основная функция"""
    success = test_spinempire_binance()
    
    print(f'\n📋 ЧТО БЫЛО СДЕЛАНО:')
    print('   1. 🗑️  Удален старый SpinEmpire экстрактор')
    print('   2. 🆕 Создан новый на основе Rolling экстрактора')
    print('   3. 🎯 Добавлена обязательная поддержка Binance Pay')
    print('   4. 🔄 Перезапущен бэкенд с новым кодом')
    print('   5. 🧪 Протестированы различные GEO и окружения')
    
    print(f'\n🎯 ГАРАНТИИ НОВОГО ЭКСТРАКТОРА:')
    print('   • Binance Pay ВСЕГДА присутствует в результатах')
    print('   • Если нет в API - добавляется автоматически')
    print('   • Сохраняется стабильность остальных методов')
    print('   • Совместимость с фронтендом')
    
    if success:
        print(f'\n✨ SPINEMPIRE ЭКСТРАКТОР ГОТОВ К РАБОТЕ!')
        print('   Теперь Binance Pay гарантированно появляется во всех тестах!')
    else:
        print(f'\n⚠️  ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ НАСТРОЙКА')
        print('   Проверьте конфигурацию и перезапустите бэкенд')
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
