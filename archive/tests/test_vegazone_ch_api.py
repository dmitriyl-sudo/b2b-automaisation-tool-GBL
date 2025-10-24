#!/usr/bin/env python3
"""
Тест API для CH_CHF аккаунтов Vegazone
Проверяем что API правильно возвращает специальные аккаунты для CH_CHF
"""

import requests
import json

def test_vegazone_ch_chf_api():
    """Тестирует API для CH_CHF аккаунтов Vegazone"""
    print('🧪 ТЕСТ API ДЛЯ CH_CHF АККАУНТОВ VEGAZONE')
    print('='*60)
    
    base_url = "http://localhost:8000"
    
    # Ожидаемые аккаунты для Vegazone CH_CHF
    expected_accounts = [
        "0depnoaffchchfdesk1",
        "0depaffilchchfmobi1", 
        "0depnoaffchchfmobi1",
        "0depaffilchchfdesk1",
        "4depaffilchchfmobi2"
    ]
    
    print("🔍 ТЕСТИРУЕМ /geo-groups ENDPOINT...")
    
    try:
        # Получаем geo-groups
        response = requests.get(f"{base_url}/geo-groups")
        
        if response.status_code == 200:
            geo_groups = response.json()
            ch_chf_accounts = geo_groups.get("CH_CHF", [])
            
            print(f"✅ API ответил успешно")
            print(f"📊 CH_CHF аккаунты из API: {len(ch_chf_accounts)} шт.")
            
            for i, account in enumerate(ch_chf_accounts, 1):
                print(f"   {i}. {account}")
            
            print(f"\n🔍 ПРОВЕРКА СООТВЕТСТВИЯ:")
            all_correct = True
            
            for expected in expected_accounts:
                if expected in ch_chf_accounts:
                    print(f"   ✅ {expected} - НАЙДЕН")
                else:
                    print(f"   ❌ {expected} - ОТСУТСТВУЕТ!")
                    all_correct = False
            
            # Проверяем что нет лишних аккаунтов
            for actual in ch_chf_accounts:
                if actual not in expected_accounts:
                    print(f"   ⚠️  {actual} - ЛИШНИЙ АККАУНТ")
            
            if all_correct and len(ch_chf_accounts) == len(expected_accounts):
                print(f"\n✅ API ВОЗВРАЩАЕТ ПРАВИЛЬНЫЕ CH_CHF АККАУНТЫ!")
            else:
                print(f"\n❌ ПРОБЛЕМА В API ОТВЕТЕ!")
                
        else:
            print(f"❌ API ошибка: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ ОШИБКА ПОДКЛЮЧЕНИЯ К API: {e}")
        print(f"   Убедитесь что бэкенд запущен на {base_url}")
    
    print(f"\n🔍 ТЕСТИРУЕМ /get-methods-only ENDPOINT...")
    
    try:
        # Тестируем получение методов для CH_CHF
        payload = {
            "project": "Vegazone",
            "geo": "CH_CHF",
            "env": "prod"
        }
        
        response = requests.post(f"{base_url}/get-methods-only", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                methods_count = len(result.get("deposit_methods", []))
                currency = result.get("currency", "N/A")
                
                print(f"✅ Методы получены успешно")
                print(f"📊 Количество методов: {methods_count}")
                print(f"💰 Валюта: {currency}")
                
                if currency == "CHF":
                    print(f"✅ ВАЛЮТА ПРАВИЛЬНАЯ: CHF")
                else:
                    print(f"⚠️  ВАЛЮТА: {currency} (ожидалась CHF)")
                    
            else:
                print(f"❌ API вернул ошибку: {result.get('message', 'Unknown error')}")
                
        else:
            print(f"❌ API ошибка: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ ОШИБКА ПОДКЛЮЧЕНИЯ К API: {e}")
    
    print(f"\n" + "="*60)
    print("🎯 ВЫВОДЫ:")
    print("1. Проверьте что бэкенд запущен на localhost:8000")
    print("2. CH_CHF должен возвращать специальные аккаунты для Vegazone")
    print("3. Валюта должна быть CHF")
    print("4. Методы должны загружаться без ошибок")

def main():
    """Основная функция"""
    test_vegazone_ch_chf_api()
    return True

if __name__ == "__main__":
    main()
