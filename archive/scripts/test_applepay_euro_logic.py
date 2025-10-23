#!/usr/bin/env python3
"""
Тест логики Apple Pay для EUR GEO
"""

def test_apple_pay_euro_logic():
    """Тестирует логику добавления Apple Pay только для EUR GEO"""
    
    # Симуляция функции getCurrencyFromGeoName
    def get_currency_from_geo_name(geo_name):
        if not geo_name:
            return 'EUR'
        geo_upper = geo_name.upper()
        
        # Проверяем локальные валюты в названии GEO
        if '_PLN' in geo_upper:
            return 'PLN'
        if '_DKK' in geo_upper:
            return 'DKK'
        if '_CHF' in geo_upper:
            return 'CHF'
        if '_NOK' in geo_upper:
            return 'NOK'
        if '_HUF' in geo_upper:
            return 'HUF'
        if '_AUD' in geo_upper:
            return 'AUD'
        if '_CAD' in geo_upper:
            return 'CAD'
        if '_USD' in geo_upper:
            return 'USD'
        
        # Если локальная валюта не указана - EUR по умолчанию
        return 'EUR'
    
    # Симуляция функции проверки EUR GEO
    def is_euro_geo(geo_name, currency):
        geo_upper = (geo_name or '').upper()
        
        return (currency == 'EUR' or 
                ('_EUR' in geo_upper) or
                (any(geo_upper.startswith(geo) for geo in ['FI', 'AT', 'DE', 'IT', 'SE', 'GR', 'IE', 'ES', 'PT']) and '_' not in geo_upper))
    
    print('🧪 ТЕСТ ЛОГИКИ APPLE PAY ДЛЯ EUR GEO')
    print('='*50)
    print()
    
    # Тестовые случаи
    test_cases = [
        # EUR GEO (должны получить Apple Pay)
        ('FI', 'EUR', True, '🇫🇮 Финляндия (EUR по умолчанию)'),
        ('AT', 'EUR', True, '🇦🇹 Австрия (EUR по умолчанию)'),
        ('DE', 'EUR', True, '🇩🇪 Германия (EUR по умолчанию)'),
        ('IT', 'EUR', True, '🇮🇹 Италия (EUR по умолчанию)'),
        ('SE', 'EUR', True, '🇸🇪 Швеция (EUR по умолчанию)'),
        ('PL_EUR', 'EUR', True, '🇵🇱 Польша EUR'),
        ('DK_EUR', 'EUR', True, '🇩🇰 Дания EUR'),
        ('CH_EUR', 'EUR', True, '🇨🇭 Швейцария EUR'),
        ('NO_EUR', 'EUR', True, '🇳🇴 Норвегия EUR'),
        ('HU_EUR', 'EUR', True, '🇭🇺 Венгрия EUR'),
        
        # Локальные валюты (НЕ должны получить Apple Pay)
        ('PL_PLN', 'PLN', False, '🇵🇱 Польша PLN (локальная валюта)'),
        ('DK_DKK', 'DKK', False, '🇩🇰 Дания DKK (локальная валюта)'),
        ('CH_CHF', 'CHF', False, '🇨🇭 Швейцария CHF (локальная валюта)'),
        ('NO_NOK', 'NOK', False, '🇳🇴 Норвегия NOK (локальная валюта)'),
        ('HU_HUF', 'HUF', False, '🇭🇺 Венгрия HUF (локальная валюта)'),
        ('AU_AUD', 'AUD', False, '🇦🇺 Австралия AUD (локальная валюта)'),
        ('CA_CAD', 'CAD', False, '🇨🇦 Канада CAD (локальная валюта)'),
    ]
    
    print('✅ ТЕСТОВЫЕ СЛУЧАИ:')
    print()
    
    success_count = 0
    total_count = len(test_cases)
    
    for geo, expected_currency, should_have_apple_pay, description in test_cases:
        # Получаем валюту
        actual_currency = get_currency_from_geo_name(geo)
        
        # Проверяем логику EUR GEO
        is_euro = is_euro_geo(geo, actual_currency)
        
        # Проверяем результат
        currency_correct = actual_currency == expected_currency
        apple_pay_correct = is_euro == should_have_apple_pay
        
        if currency_correct and apple_pay_correct:
            status = '✅'
            success_count += 1
        else:
            status = '❌'
        
        print(f'{status} {description}')
        print(f'   GEO: {geo} → Валюта: {actual_currency} → Apple Pay: {"ДА" if is_euro else "НЕТ"}')
        
        if not currency_correct:
            print(f'   ⚠️  Ошибка валюты: ожидалось {expected_currency}, получено {actual_currency}')
        if not apple_pay_correct:
            print(f'   ⚠️  Ошибка Apple Pay: ожидалось {"ДА" if should_have_apple_pay else "НЕТ"}, получено {"ДА" if is_euro else "НЕТ"}')
        print()
    
    print('📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:')
    print(f'   Успешных тестов: {success_count}/{total_count}')
    print(f'   Процент успеха: {(success_count/total_count)*100:.1f}%')
    print()
    
    if success_count == total_count:
        print('🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!')
        print('✅ Логика Apple Pay для EUR GEO работает корректно')
        print()
        print('📋 ЛОГИКА:')
        print('   • Apple Pay добавляется ТОЛЬКО для EUR GEO')
        print('   • EUR GEO: FI, AT, DE, IT, SE, GR, IE, ES, PT (без суффикса)')
        print('   • EUR GEO: *_EUR (с суффиксом _EUR)')
        print('   • Локальные валюты исключены: *_PLN, *_DKK, *_CHF, etc.')
        return True
    else:
        print('❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ')
        print('   Требуется исправление логики')
        return False

if __name__ == "__main__":
    import sys
    success = test_apple_pay_euro_logic()
    sys.exit(0 if success else 1)
