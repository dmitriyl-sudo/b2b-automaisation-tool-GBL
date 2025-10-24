#!/usr/bin/env python3
"""
Тест специальных CH_CHF аккаунтов для проекта Vegazone
Проверяем что Vegazone использует правильные аккаунты для Швейцарии
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import geo_groups, VEGASZONE_EXTRA_GEOS
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_vegazone_ch_chf_accounts():
    """Тестирует специальные CH_CHF аккаунты для Vegazone"""
    print('🧪 ТЕСТ CH_CHF АККАУНТОВ ДЛЯ VEGAZONE')
    print('='*60)
    
    # Ожидаемые аккаунты для Vegazone CH_CHF
    expected_vegazone_accounts = [
        "0depnoaffchchfdesk1",
        "0depaffilchchfmobi1", 
        "0depnoaffchchfmobi1",
        "0depaffilchchfdesk1",
        "4depaffilchchfmobi2"
    ]
    
    # Базовые аккаунты CH_CHF (для других проектов)
    base_accounts = geo_groups.get("CH_CHF", [])
    
    # Специальные аккаунты Vegazone CH_CHF
    vegazone_accounts = VEGASZONE_EXTRA_GEOS.get("CH_CHF", [])
    
    print("📋 БАЗОВЫЕ CH_CHF АККАУНТЫ (для других проектов):")
    for i, account in enumerate(base_accounts, 1):
        print(f"   {i}. {account}")
    
    print(f"\n📋 VEGAZONE CH_CHF АККАУНТЫ (специальные):")
    for i, account in enumerate(vegazone_accounts, 1):
        print(f"   {i}. {account}")
    
    print(f"\n🔍 ПРОВЕРКА СООТВЕТСТВИЯ:")
    all_correct = True
    
    for expected in expected_vegazone_accounts:
        if expected in vegazone_accounts:
            print(f"   ✅ {expected} - НАЙДЕН")
        else:
            print(f"   ❌ {expected} - ОТСУТСТВУЕТ!")
            all_correct = False
    
    # Проверяем что нет лишних аккаунтов
    for actual in vegazone_accounts:
        if actual not in expected_vegazone_accounts:
            print(f"   ⚠️  {actual} - ЛИШНИЙ АККАУНТ")
            all_correct = False
    
    print(f"\n🔍 РАЗЛИЧИЯ С БАЗОВЫМИ АККАУНТАМИ:")
    base_set = set(base_accounts)
    vegazone_set = set(vegazone_accounts)
    
    only_in_base = base_set - vegazone_set
    only_in_vegazone = vegazone_set - base_set
    
    if only_in_base:
        print(f"   📊 Только в базовых:")
        for account in only_in_base:
            print(f"      • {account}")
    
    if only_in_vegazone:
        print(f"   📊 Только в Vegazone:")
        for account in only_in_vegazone:
            print(f"      • {account}")
    
    if not only_in_base and not only_in_vegazone:
        print(f"   ⚠️  Аккаунты одинаковые! Возможно нужно проверить логику.")
    
    print(f"\n🎯 ЛОГИКА ВЫБОРА АККАУНТОВ:")
    print(f"   • Для проектов кроме Vegazone: используются базовые CH_CHF")
    print(f"   • Для Vegazone: используются специальные CH_CHF из VEGASZONE_EXTRA_GEOS")
    print(f"   • Логика объединения: {{**geo_groups, **VEGASZONE_EXTRA_GEOS}}")
    print(f"   • Специальные аккаунты перезаписывают базовые")
    
    print(f"\n" + "="*60)
    if all_correct:
        print("✅ ВСЕ CH_CHF АККАУНТЫ ДЛЯ VEGAZONE НАСТРОЕНЫ ПРАВИЛЬНО!")
    else:
        print("❌ НАЙДЕНЫ ПРОБЛЕМЫ В НАСТРОЙКЕ CH_CHF АККАУНТОВ!")
    
    return all_correct

def test_api_logic():
    """Тестирует логику API для выбора аккаунтов"""
    print(f"\n🔧 ТЕСТ ЛОГИКИ API:")
    print("-" * 40)
    
    # Эмулируем логику из api_fastapi_backend.py
    # Для Vegazone
    effective_geo_groups_vegazone = {**geo_groups, **VEGASZONE_EXTRA_GEOS}
    vegazone_ch_accounts = effective_geo_groups_vegazone.get("CH_CHF", [])
    
    # Для других проектов
    other_ch_accounts = geo_groups.get("CH_CHF", [])
    
    print(f"📊 Vegazone CH_CHF аккаунты: {len(vegazone_ch_accounts)} шт.")
    for account in vegazone_ch_accounts:
        print(f"   • {account}")
    
    print(f"\n📊 Другие проекты CH_CHF аккаунты: {len(other_ch_accounts)} шт.")
    for account in other_ch_accounts:
        print(f"   • {account}")
    
    # Проверяем что аккаунты разные
    if set(vegazone_ch_accounts) != set(other_ch_accounts):
        print(f"\n✅ ЛОГИКА РАБОТАЕТ: Vegazone использует специальные аккаунты!")
    else:
        print(f"\n❌ ПРОБЛЕМА: Vegazone использует те же аккаунты что и другие проекты!")

def main():
    """Основная функция"""
    success = test_vegazone_ch_chf_accounts()
    test_api_logic()
    
    print(f"\n🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    if success:
        print("✅ CH_CHF аккаунты для Vegazone настроены корректно!")
        print("🚀 Можно тестировать на фронтенде!")
    else:
        print("❌ Требуются исправления в настройке аккаунтов!")
    
    return success

if __name__ == "__main__":
    main()
