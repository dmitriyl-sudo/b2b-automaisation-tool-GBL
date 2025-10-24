#!/usr/bin/env python3
"""
Детальный анализ данных для 0depnoaffiteurmobi
Сравниваем что получает экстрактор с реальными данными фронта
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extractors.vegazone_extractor import VegazoneExtractor
from main import password_data
import logging
import base64

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def decode_alias(alias):
    """Декодирует base64 alias"""
    try:
        return base64.b64decode(alias).decode('utf-8')
    except:
        return alias

def test_vegazone_it_detailed():
    """Детальный анализ IT данных"""
    print('🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ДАННЫХ ДЛЯ 0depnoaffiteurmobi')
    print('='*70)
    
    # Реальные данные с фронта (первые несколько методов)
    expected_methods = [
        {
            "name": "V/M_Directcorefy_Cards_0DEP//mob//noaff",
            "title": "Visa/Mastercard", 
            "alias": "dm0tZGlyZWN0Y29yZWZ5LWNhcmRzLTBkZXBtb2Jub2FmZg==",
            "display_type": "out"
        },
        {
            "name": "Nodapay_nodapay_Banks_IT",
            "title": "Pay via Bank",
            "alias": "bm9kYXBheS1ub2RhcGF5LWJhbmtzLWl0",
            "display_type": "out"
        }
    ]
    
    print("📋 ОЖИДАЕМЫЕ МЕТОДЫ С ФРОНТА:")
    for i, method in enumerate(expected_methods, 1):
        decoded_alias = decode_alias(method['alias'])
        print(f"   {i}. {method['title']} → {method['name']}")
        print(f"      alias: {method['alias']} → {decoded_alias}")
        print(f"      display_type: {method['display_type']}")
        print()
    
    # Создаем экстрактор
    print("🔧 СОЗДАЕМ ЭКСТРАКТОР...")
    extractor = VegazoneExtractor(
        login="0depnoaffiteurmobi",
        password=password_data,
        base_url="https://vegazone.com"
    )
    
    print("🔐 АВТОРИЗАЦИЯ...")
    auth_success = extractor.authenticate()
    print(f"   Результат: {'✅ Успешно' if auth_success else '❌ Ошибка'}")
    
    print(f"📱 User-Agent: {extractor.headers.get('User-Agent', 'N/A')}")
    print(f"💰 Валюта: {extractor.currency}")
    
    print("\n🔍 ПОЛУЧАЕМ МЕТОДЫ...")
    
    try:
        # Получаем методы с raw данными
        (deposit_enriched, wd_titles, dep_names, wd_names, 
         currency, deposit_count, recommended_methods) = extractor.get_payment_and_withdraw_systems("IT")
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ЭКСТРАКТОРА:")
        print(f"   • Всего методов: {len(deposit_enriched)}")
        print(f"   • Валюта: {currency}")
        
        print(f"\n📋 МЕТОДЫ ИЗ ЭКСТРАКТОРА:")
        found_methods = {}
        for i, method in enumerate(deposit_enriched, 1):
            title = method['title']
            name = method['name']
            min_dep = method.get('min_deposit', 'N/A')
            cur = method.get('currency', 'N/A')
            
            print(f"   {i:2d}. {title} → {name} | {min_dep} {cur}")
            found_methods[name] = title
        
        print(f"\n🔍 СРАВНЕНИЕ С ОЖИДАЕМЫМИ:")
        for expected in expected_methods:
            expected_name = expected['name']
            expected_title = expected['title']
            
            if expected_name in found_methods:
                print(f"   ✅ {expected_title} ({expected_name}) - НАЙДЕН")
            else:
                print(f"   ❌ {expected_title} ({expected_name}) - ОТСУТСТВУЕТ!")
                
                # Ищем похожие методы
                similar = []
                for found_name, found_title in found_methods.items():
                    if expected_title.lower() in found_title.lower() or found_title.lower() in expected_title.lower():
                        similar.append((found_title, found_name))
                
                if similar:
                    print(f"      🔍 Похожие методы:")
                    for sim_title, sim_name in similar:
                        print(f"         • {sim_title} ({sim_name})")
        
        print(f"\n🔍 АНАЛИЗ ПОТЕРЯННОГО МЕТОДА:")
        target_method = "V/M_Directcorefy_Cards_0DEP//mob//noaff"
        
        # Проверяем есть ли методы с Directcorefy
        directcorefy_methods = []
        for name, title in found_methods.items():
            if 'directcorefy' in name.lower() or 'corefy' in name.lower():
                directcorefy_methods.append((title, name))
        
        if directcorefy_methods:
            print(f"   ✅ Найдены методы с Directcorefy/Corefy:")
            for title, name in directcorefy_methods:
                print(f"      • {title} ({name})")
        else:
            print(f"   ❌ НЕТ методов с Directcorefy/Corefy!")
        
        # Проверяем есть ли методы с mob//noaff
        mobile_noaff_methods = []
        for name, title in found_methods.items():
            if 'mob' in name.lower() and 'noaff' in name.lower():
                mobile_noaff_methods.append((title, name))
        
        if mobile_noaff_methods:
            print(f"   ✅ Найдены методы с mob//noaff:")
            for title, name in mobile_noaff_methods:
                print(f"      • {title} ({name})")
        else:
            print(f"   ❌ НЕТ методов с mob//noaff!")
            
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "="*70)
    print("🎯 ВЫВОДЫ:")
    print("1. Проверьте есть ли метод V/M_Directcorefy_Cards_0DEP//mob//noaff в логах")
    print("2. Возможно проблема в фильтрации по display_type или operation_type")
    print("3. Проверьте что экстрактор правильно парсит поле 'name'")

def main():
    """Основная функция"""
    test_vegazone_it_detailed()
    return True

if __name__ == "__main__":
    main()
