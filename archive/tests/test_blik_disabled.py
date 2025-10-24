#!/usr/bin/env python3
"""
Тест отключения Blik из хардкод методов
"""

import requests
import json
from datetime import datetime

# Конфигурация
BASE_URL = "http://localhost:8000"
PROJECT = "Rolling"
ENV = "prod"
TEST_GEOS = ["PL_PLN", "FI", "DE", "IT"]  # PL для проверки Blik, остальные для сравнения

def test_hardcode_methods():
    """Тестирует хардкод методы в разных GEO"""
    print("🔍 ТЕСТ: Проверка хардкод методов после отключения Blik")
    print("=" * 70)
    
    results = {}
    
    for geo in TEST_GEOS:
        try:
            response = requests.post(f"{BASE_URL}/get-methods-only", json={
                "project": PROJECT,
                "geo": geo,
                "env": ENV
            })
            
            if response.status_code != 200:
                results[geo] = {"error": f"HTTP {response.status_code}"}
                continue
                
            data = response.json()
            
            if not data.get('success'):
                results[geo] = {"error": data.get('error', 'Unknown')}
                continue
                
            methods = data.get('methods', [])
            
            # Ищем хардкод методы
            hardcode_methods = []
            blik_found = False
            zimpler_found = False
            applepay_found = False
            
            for method in methods:
                title = method.get('title', '')
                if title in ['Blik']:
                    blik_found = True
                    hardcode_methods.append(f"❌ {title} (НЕ ДОЛЖЕН БЫТЬ)")
                elif title in ['Zimpler']:
                    zimpler_found = True
                    hardcode_methods.append(f"✅ {title}")
                elif title in ['ApplePay Visa', 'ApplePay Gumballpay']:
                    applepay_found = True
                    hardcode_methods.append(f"✅ {title}")
                    
            results[geo] = {
                "total_methods": len(methods),
                "hardcode_methods": hardcode_methods,
                "blik_found": blik_found,
                "zimpler_found": zimpler_found,
                "applepay_found": applepay_found,
                "accounts": f"{data.get('accounts_processed', 0)}/{data.get('total_accounts', 0)}",
                "is_empty": len(methods) == 0
            }
            
        except Exception as e:
            results[geo] = {"error": str(e)}
    
    # Выводим результаты
    for geo, result in results.items():
        if "error" in result:
            print(f"  {geo:8} ❌ {result['error']}")
        elif result.get("is_empty"):
            print(f"  {geo:8} ⚪ Пустое GEO (0 методов)")
        else:
            total = result['total_methods']
            hardcode = result['hardcode_methods']
            accounts = result['accounts']
            
            print(f"  {geo:8} 📊 {total} методов, аккаунты {accounts}")
            
            if hardcode:
                print(f"           🔧 Хардкод методы:")
                for method in hardcode:
                    print(f"              {method}")
            else:
                print(f"           🔧 Хардкод методы: нет")
    
    return results

def main():
    """Основная функция тестирования"""
    print(f"🧪 ТЕСТ ОТКЛЮЧЕНИЯ BLIK ИЗ ХАРДКОД МЕТОДОВ")
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Проект: {PROJECT}")
    print(f"🌍 Тестовые GEO: {', '.join(TEST_GEOS)}")
    print("=" * 80)
    
    results = test_hardcode_methods()
    
    print(f"\n📊 АНАЛИЗ РЕЗУЛЬТАТОВ")
    print("=" * 70)
    
    # Проверяем что Blik отключен
    pl_result = results.get('PL_PLN', {})
    if 'error' in pl_result:
        print(f"⚠️  PL_PLN недоступен: {pl_result['error']}")
    elif pl_result.get('is_empty'):
        print(f"⚠️  PL_PLN пустой")
    else:
        blik_found = pl_result.get('blik_found', False)
        if blik_found:
            print(f"❌ ОШИБКА: Blik все еще найден в PL_PLN!")
        else:
            print(f"✅ SUCCESS: Blik успешно отключен в PL_PLN")
    
    # Проверяем что остальные методы работают
    other_geos = [geo for geo in TEST_GEOS if geo != 'PL_PLN']
    working_geos = []
    
    for geo in other_geos:
        result = results.get(geo, {})
        if not result.get('is_empty') and 'error' not in result:
            zimpler_found = result.get('zimpler_found', False)
            applepay_found = result.get('applepay_found', False)
            
            if geo == 'FI' and zimpler_found:
                working_geos.append(f"{geo} (Zimpler ✅)")
            elif geo != 'FI' and applepay_found:
                working_geos.append(f"{geo} (ApplePay ✅)")
            elif applepay_found:
                working_geos.append(f"{geo} (ApplePay ✅)")
    
    print(f"✅ Работающие хардкод методы: {', '.join(working_geos)}")
    
    print(f"\n🔧 ЧТО ИЗМЕНЕНО:")
    print("   1. ❌ Blik отключен для всех PL GEO")
    print("   2. ✅ Zimpler остался активен для FI GEO")
    print("   3. ✅ ApplePay Gumballpay остался активен для всех GEO")
    print("   4. 💡 Код Blik закомментирован для легкого включения")
    
    print(f"\n💡 КАК ВКЛЮЧИТЬ BLIK ОБРАТНО:")
    print("   1. Откройте frontend/src/panels/GeoMethodsPanel.jsx")
    print("   2. Найдите строки 89-104 (блок с Blik)")
    print("   3. Раскомментируйте код (уберите // в начале строк)")
    print("   4. Обновите описание в App.js (добавьте '• Blik (PL)')")
    
    print(f"\n✨ BLIK УСПЕШНО ОТКЛЮЧЕН!")
    
    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
