#!/usr/bin/env python3
"""
Тест наличия звездочек в Google Sheets данных
"""

import requests
import json
from datetime import datetime

# Конфигурация
BASE_URL = "http://localhost:8000"
TEST_CASES = [
    {"project": "Rolling", "geo": "DE", "env": "prod"},
    {"project": "Rolling", "geo": "FI", "env": "prod"},
    {"project": "SpinEmpire", "geo": "DE", "env": "prod"}
]

def test_stars_in_sheets_data():
    """Тестирует наличие звездочек в данных для Google Sheets"""
    print("🔍 ТЕСТ: Наличие звездочек (⭐) в Google Sheets данных")
    print("=" * 70)
    
    for i, test_case in enumerate(TEST_CASES):
        project = test_case["project"]
        geo = test_case["geo"]
        env = test_case["env"]
        
        print(f"\n📊 ТЕСТ {i+1}: {project} - {geo} - {env}")
        print("-" * 50)
        
        try:
            # Получаем данные для Google Sheets
            response = requests.post(f"{BASE_URL}/get-sheets-data-fixed", json={
                "project": project,
                "geo": geo,
                "env": env
            })
            
            if response.status_code != 200:
                print(f"❌ Ошибка получения данных: HTTP {response.status_code}")
                continue
                
            data = response.json()
            
            if not data.get('success'):
                print(f"❌ Ошибка: {data.get('error', 'Unknown')}")
                continue
                
            rows = data.get('data', [])
            if len(rows) == 0:
                print(f"⚠️  Нет данных для анализа")
                continue
                
            print(f"✅ Данные получены: {len(rows)} строк")
            
            # Анализируем наличие звездочек
            recommended_count = 0
            total_count = len(rows)
            recommended_methods = []
            
            for row in rows:
                recommended_field = row.get('Recommended', '')
                paymethod = row.get('Paymethod', 'Unknown')
                
                if '⭐' in recommended_field:
                    recommended_count += 1
                    recommended_methods.append(paymethod)
            
            print(f"📊 Анализ рекомендованных методов:")
            print(f"   • Всего методов: {total_count}")
            print(f"   • Рекомендованных: {recommended_count}")
            print(f"   • Процент: {(recommended_count/total_count*100):.1f}%")
            
            if recommended_methods:
                print(f"✅ Методы со звездочками:")
                for method in recommended_methods[:5]:  # Показываем первые 5
                    print(f"   ⭐ {method}")
                if len(recommended_methods) > 5:
                    print(f"   ... и еще {len(recommended_methods) - 5}")
            else:
                print(f"❌ НЕТ МЕТОДОВ СО ЗВЕЗДОЧКАМИ!")
            
            # Проверяем формат поля Recommended
            sample_recommended = [row.get('Recommended', '') for row in rows[:3]]
            print(f"🔍 Примеры поля 'Recommended': {sample_recommended}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def main():
    """Основная функция тестирования"""
    print(f"🧪 ТЕСТ ЗВЕЗДОЧЕК В GOOGLE SHEETS ДАННЫХ")
    print(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    test_stars_in_sheets_data()
    
    print(f"\n📊 ИТОГИ ПРОВЕРКИ")
    print("=" * 70)
    
    print(f"🔍 ЧТО ПРОВЕРЯЛИ:")
    print("   1. Эндпоинт /get-sheets-data-fixed")
    print("   2. Поле 'Recommended' в каждой строке")
    print("   3. Наличие символа ⭐ в рекомендованных методах")
    print()
    print(f"💡 ВОЗМОЖНЫЕ ПРИЧИНЫ ОТСУТСТВИЯ ЗВЕЗДОЧЕК:")
    print("   1. Проблема в логике определения isRecommended")
    print("   2. Неправильная обработка рекомендаций в экстракторах")
    print("   3. Потеря данных при формировании sheets_data")
    print("   4. Кодировка символов при экспорте в Google Sheets")
    print()
    print(f"🔧 ГДЕ ДОЛЖНЫ БЫТЬ ЗВЕЗДОЧКИ:")
    print("   • api_fastapi_backend.py строка 978:")
    print("     'Recommended': '⭐' if group_data['isRecommended'] else ''")
    print("   • frontend/src/panels/GeoMethodsPanel.jsx строка 462:")
    print("     'Recommended': row.isRecommended ? '⭐\\u200B' : ''")
    print()
    print(f"✨ СЛЕДУЮЩИЕ ШАГИ:")
    print("   Если звездочки отсутствуют - проверить логику isRecommended")
    
    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
