#!/usr/bin/env python3
"""
Тест функционала автоматического добавления GooglePay к ApplePay
"""

import requests
import json

def test_googlepay_functionality():
    """Тестирует новый функционал GooglePay"""
    print('🧪 ТЕСТ ФУНКЦИОНАЛА АВТОМАТИЧЕСКОГО ДОБАВЛЕНИЯ GOOGLEPAY')
    print('='*70)
    print()
    
    # Тестируем получение методов для проекта с ApplePay
    test_cases = [
        {
            "project": "Rolling",
            "geo": "DE", 
            "env": "prod",
            "description": "Rolling DE - должен содержать ApplePay методы"
        },
        {
            "project": "SpinEmpire",
            "geo": "FI",
            "env": "prod", 
            "description": "SpinEmpire FI - тест с Финляндией"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f'{i}. 🔍 ТЕСТ: {test_case["description"]}')
        print('-' * 50)
        
        try:
            # Получаем методы
            response = requests.post(
                "http://localhost:8000/get-all-methods-for-geo",
                json=test_case,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Ищем ApplePay методы
                applepay_methods = []
                all_methods = (data.get('deposit_methods', []) + 
                             data.get('withdraw_methods', []))
                
                for title, name in all_methods:
                    if 'applepay' in title.lower() or 'applepay' in name.lower():
                        applepay_methods.append((title, name))
                
                print(f'📊 Всего методов: {len(all_methods)}')
                print(f'🍎 ApplePay методов найдено: {len(applepay_methods)}')
                
                if applepay_methods:
                    print('🍎 ApplePay методы:')
                    for title, name in applepay_methods:
                        has_colibrix = 'colibrix' in name.lower()
                        status = '❌ (colibrix - GooglePay НЕ будет создан)' if has_colibrix else '✅ (GooglePay будет создан)'
                        print(f'   • {title} | {name} {status}')
                else:
                    print('⚠️  ApplePay методы не найдены')
                
                print()
                
            else:
                print(f'❌ Ошибка API: {response.status_code}')
                print(response.text)
                
        except Exception as e:
            print(f'❌ Ошибка: {e}')
        
        print()
    
    print('📋 ИНСТРУКЦИИ ДЛЯ ТЕСТИРОВАНИЯ В UI:')
    print('='*50)
    print()
    print('1. 🌐 Откройте фронтенд: http://localhost:3000')
    print('2. 📋 Перейдите на вкладку "GEO Methods"')
    print('3. 🔧 Выберите проект (например, Rolling)')
    print('4. 🌍 Выберите GEO (например, DE)')
    print('5. 🏭 Выберите окружение: prod')
    print('6. ✅ ВКЛЮЧИТЕ чекбокс "Add hardcoded methods"')
    print('7. 🚀 Нажмите "Load GEO Methods"')
    print()
    print('🔍 ЧТО ОЖИДАТЬ:')
    print('   • Рядом с каждым ApplePay должен появиться GooglePay')
    print('   • GooglePay НЕ должен создаваться для методов с "colibrix"')
    print('   • ID (Payment Name) у GooglePay = ApplePay ID с заменой applepay→googlepay')
    print('   • Title у GooglePay = ApplePay Title с заменой Applepay→Googlepay')
    print()
    print('📊 ПРИМЕР ОЖИДАЕМОГО РЕЗУЛЬТАТА:')
    print('   ApplePay Visa | Applepay_Gumballpay_Cards_1DEP')
    print('   Googlepay Visa | Googlepay_Gumballpay_Cards_1DEP  ← автоматически создан')
    print()
    print('❌ НЕ ДОЛЖНО СОЗДАВАТЬСЯ:')
    print('   ApplePay Colibrix | Applepay_Colibrix_Cards_1DEP')
    print('   (GooglePay НЕ создается для colibrix)')
    print()
    print('🧪 ДОПОЛНИТЕЛЬНОЕ ТЕСТИРОВАНИЕ:')
    print('   • Попробуйте режим "Full project mode" (галочка)')
    print('   • Проверьте экспорт в Google Sheets')
    print('   • GooglePay должен появиться в экспортированной таблице')
    print()
    print('✨ ФУНКЦИОНАЛ ГОТОВ К ТЕСТИРОВАНИЮ!')

def main():
    """Основная функция"""
    test_googlepay_functionality()
    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
