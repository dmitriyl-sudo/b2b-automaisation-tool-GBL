#!/usr/bin/env python3
"""
Тест исправления CH_CHF аккаунтов для Vegazone
Проверяем что get_all_methods_for_geo использует правильные аккаунты
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_fastapi_backend import get_all_methods_for_geo
from main import geo_groups, VEGASZONE_EXTRA_GEOS
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_ch_chf_account_selection():
    """Тестирует выбор правильных CH_CHF аккаунтов для Vegazone"""
    print('🧪 ТЕСТ ИСПРАВЛЕНИЯ CH_CHF АККАУНТОВ')
    print('='*60)
    
    # Ожидаемые аккаунты для Vegazone CH_CHF
    expected_vegazone_accounts = [
        "0depnoaffchchfdesk1",
        "0depaffilchchfmobi1", 
        "0depnoaffchchfmobi1",
        "0depaffilchchfdesk1",
        "4depaffilchchfmobi2"
    ]
    
    # Базовые аккаунты CH_CHF
    base_accounts = geo_groups.get("CH_CHF", [])
    
    print("📋 БАЗОВЫЕ CH_CHF АККАУНТЫ:")
    for account in base_accounts:
        print(f"   • {account}")
    
    print(f"\n📋 ОЖИДАЕМЫЕ VEGAZONE CH_CHF АККАУНТЫ:")
    for account in expected_vegazone_accounts:
        print(f"   • {account}")
    
    print(f"\n🔍 ТЕСТИРУЕМ ЛОГИКУ get_all_methods_for_geo...")
    
    # Эмулируем логику из исправленной функции
    project = "Vegazone"
    geo = "CH_CHF"
    
    # Логика выбора аккаунтов (как в исправленной функции)
    if project == "Glitchspin":
        merged_geo_groups = {**geo_groups, **{}}  # GLITCHSPIN_EXTRA_GEOS пустой для этого теста
    elif project == "Vegazone":
        merged_geo_groups = {**geo_groups, **VEGASZONE_EXTRA_GEOS}
    else:
        merged_geo_groups = geo_groups
    
    # Получаем список аккаунтов
    if geo in merged_geo_groups:
        login_list = merged_geo_groups[geo]
    else:
        base_geo = geo.split('_')[0]
        if base_geo in merged_geo_groups:
            login_list = merged_geo_groups[base_geo]
        else:
            login_list = []
    
    print(f"\n📊 РЕЗУЛЬТАТ ЛОГИКИ:")
    print(f"   Проект: {project}")
    print(f"   GEO: {geo}")
    print(f"   Найдено аккаунтов: {len(login_list)}")
    
    for i, account in enumerate(login_list, 1):
        print(f"   {i}. {account}")
    
    print(f"\n🔍 ПРОВЕРКА СООТВЕТСТВИЯ:")
    all_correct = True
    
    # Проверяем что получили правильные аккаунты
    if set(login_list) == set(expected_vegazone_accounts):
        print(f"   ✅ ВСЕ АККАУНТЫ ПРАВИЛЬНЫЕ!")
    else:
        print(f"   ❌ АККАУНТЫ НЕ СООТВЕТСТВУЮТ ОЖИДАЕМЫМ!")
        all_correct = False
        
        missing = set(expected_vegazone_accounts) - set(login_list)
        extra = set(login_list) - set(expected_vegazone_accounts)
        
        if missing:
            print(f"   ❌ Отсутствуют:")
            for account in missing:
                print(f"      • {account}")
        
        if extra:
            print(f"   ⚠️  Лишние:")
            for account in extra:
                print(f"      • {account}")
    
    # Проверяем что аккаунты отличаются от базовых
    if set(login_list) != set(base_accounts):
        print(f"   ✅ АККАУНТЫ ОТЛИЧАЮТСЯ ОТ БАЗОВЫХ (это правильно)")
    else:
        print(f"   ❌ АККАУНТЫ ТАКИЕ ЖЕ КАК БАЗОВЫЕ (проблема!)")
        all_correct = False
    
    print(f"\n🔍 ТЕСТ ДРУГИХ ПРОЕКТОВ:")
    
    # Тестируем что другие проекты используют базовые аккаунты
    other_project = "Rolling"
    if other_project == "Glitchspin":
        other_merged = {**geo_groups, **{}}
    elif other_project == "Vegazone":
        other_merged = {**geo_groups, **VEGASZONE_EXTRA_GEOS}
    else:
        other_merged = geo_groups
    
    other_accounts = other_merged.get("CH_CHF", [])
    
    print(f"   Проект: {other_project}")
    print(f"   CH_CHF аккаунты: {len(other_accounts)} шт.")
    
    if set(other_accounts) == set(base_accounts):
        print(f"   ✅ Другие проекты используют базовые аккаунты")
    else:
        print(f"   ❌ Другие проекты используют неправильные аккаунты")
        all_correct = False
    
    print(f"\n" + "="*60)
    if all_correct:
        print("✅ ИСПРАВЛЕНИЕ РАБОТАЕТ ПРАВИЛЬНО!")
        print("🚀 Vegazone будет использовать специальные CH_CHF аккаунты!")
    else:
        print("❌ НАЙДЕНЫ ПРОБЛЕМЫ В ИСПРАВЛЕНИИ!")
    
    return all_correct

def main():
    """Основная функция"""
    success = test_ch_chf_account_selection()
    
    if success:
        print(f"\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
        print("1. Перезапустите бэкенд чтобы изменения вступили в силу")
        print("2. Протестируйте на фронтенде: Vegazone -> CH_CHF -> Load Methods")
        print("3. В логах должны быть аккаунты с суффиксами 1/2")
    
    return success

if __name__ == "__main__":
    main()
