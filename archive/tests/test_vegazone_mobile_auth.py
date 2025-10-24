#!/usr/bin/env python3
"""
Тест авторизации и эмуляции мобильного устройства для Vegazone
Проверяем что 0depnoaff*mobi аккаунты правильно авторизуются и эмулируют мобильное устройство
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extractors.vegazone_extractor import VegazoneExtractor
from main import password_data
import logging

# Настройка логирования для детального анализа
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_vegazone_mobile_auth():
    """Тестирует авторизацию и эмуляцию мобильного устройства для Vegazone"""
    print('🧪 ТЕСТ АВТОРИЗАЦИИ И МОБИЛЬНОЙ ЭМУЛЯЦИИ ДЛЯ VEGAZONE')
    print('='*70)
    
    # Тестируем на DE и IT
    test_cases = [
        {
            "geo": "DE",
            "login": "0depnoaffdeeurmobi",
            "expected_methods": [
                "M_Directcorefy_Cards_0DEP//mob//noaff",
                "V/M_Corefy_Cards_0DEP//mob//aff", 
                "V/M_Directcorefy_Cards_0DEP//desktop",
                "V/M_Corefy_Cards_1DEP"
            ]
        },
        {
            "geo": "IT", 
            "login": "0depnoaffiteurmobi",
            "expected_methods": [
                "M_Directcorefy_Cards_0DEP//mob//noaff",  # ← Этот метод теряется!
                "V/M_Corefy_Cards_0DEP//mob//aff",
                "V/M_Directcorefy_Cards_0DEP//desktop", 
                "V/M_Corefy_Cards_1DEP"
            ]
        }
    ]
    
    for case in test_cases:
        print(f"\n📋 ТЕСТИРУЕМ {case['geo']} с логином {case['login']}")
        print("-" * 50)
        
        # Создаем экстрактор
        extractor = VegazoneExtractor(
            login=case['login'],
            password=password_data,
            base_url="https://vegazone.com"
        )
        
        print(f"🔐 Авторизация...")
        auth_success = extractor.authenticate()
        print(f"   Результат: {'✅ Успешно' if auth_success else '❌ Ошибка'}")
        
        if 'mobi' in case['login']:
            print(f"📱 Мобильная эмуляция: ✅ Включена (User-Agent: iPhone)")
        else:
            print(f"🖥️  Десктоп режим")
            
        print(f"💰 Валюта: {extractor.currency}")
        print(f"🏦 Депозитов: {extractor.deposit_count}")
        
        print(f"\n🔍 ПОЛУЧАЕМ МЕТОДЫ ДЛЯ {case['geo']}...")
        
        try:
            # Получаем методы
            (deposit_enriched, wd_titles, dep_names, wd_names, 
             currency, deposit_count, recommended_methods) = extractor.get_payment_and_withdraw_systems(case['geo'])
            
            print(f"📊 РЕЗУЛЬТАТЫ:")
            print(f"   • Всего депозитных методов: {len(deposit_enriched)}")
            print(f"   • Всего withdraw методов: {len(wd_titles)}")
            print(f"   • Валюта: {currency}")
            print(f"   • Рекомендованных: {len(recommended_methods)}")
            
            print(f"\n📋 ДЕПОЗИТНЫЕ МЕТОДЫ:")
            found_methods = []
            for i, method in enumerate(deposit_enriched, 1):
                title = method['title']
                name = method['name']
                min_dep = method.get('min_deposit', 'N/A')
                cur = method.get('currency', 'N/A')
                
                print(f"   {i:2d}. {title} → {name} | {min_dep} {cur}")
                found_methods.append(name)
            
            print(f"\n🔍 АНАЛИЗ ОЖИДАЕМЫХ МЕТОДОВ:")
            for expected in case['expected_methods']:
                if expected in found_methods:
                    print(f"   ✅ {expected} - НАЙДЕН")
                else:
                    print(f"   ❌ {expected} - ОТСУТСТВУЕТ!")
            
            print(f"\n🔍 ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ:")
            for found in found_methods:
                if found not in case['expected_methods']:
                    print(f"   ➕ {found} - дополнительный")
                    
        except Exception as e:
            print(f"❌ ОШИБКА при получении методов: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n" + "="*70)
    print("🎯 ВЫВОДЫ:")
    print("1. Проверьте логи выше на предмет различий в API ответах")
    print("2. Обратите внимание на User-Agent заголовки")
    print("3. Сравните количество методов между DE и IT")
    print("4. Ищите потерянный метод M_Directcorefy_Cards_0DEP//mob//noaff в IT")

def main():
    """Основная функция"""
    test_vegazone_mobile_auth()
    return True

if __name__ == "__main__":
    main()
