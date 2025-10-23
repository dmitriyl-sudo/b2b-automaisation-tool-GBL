#!/usr/bin/env python3
"""
Диагностический скрипт для проверки функционала GeoMethodsPanel
"""

import requests
import json
import sys
import os
from pathlib import Path

def check_api_server():
    """Проверка работы API сервера"""
    try:
        # Проверяем, запущен ли FastAPI сервер
        response = requests.get('http://localhost:8000/docs', timeout=5)
        print("✅ FastAPI сервер запущен на порту 8000")
        return True
    except requests.exceptions.ConnectionError:
        try:
            # Проверяем альтернативный порт
            response = requests.get('http://localhost:5000/docs', timeout=5)
            print("✅ FastAPI сервер запущен на порту 5000")
            return True
        except requests.exceptions.ConnectionError:
            print("❌ FastAPI сервер не запущен")
            return False
    except Exception as e:
        print(f"❌ Ошибка при проверке API сервера: {e}")
        return False

def check_frontend_files():
    """Проверка наличия фронтенд файлов"""
    files_to_check = [
        'frontend/src/panels/GeoMethodsPanel.jsx',
        'frontend/src/App.js',
        'api_fastapi_backend.py'
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} найден")
        else:
            print(f"❌ {file_path} не найден")
            all_exist = False
    
    return all_exist

def check_api_endpoints():
    """Проверка API эндпоинтов для экспорта"""
    endpoints = [
        '/export-table-to-sheets',
        '/export-table-to-sheets-multi'
    ]
    
    base_urls = ['http://localhost:8000', 'http://localhost:5000']
    
    for base_url in base_urls:
        print(f"\n🔍 Проверка эндпоинтов на {base_url}:")
        for endpoint in endpoints:
            try:
                # Пробуем POST запрос с пустыми данными
                response = requests.post(f'{base_url}{endpoint}', 
                                       json={'data': []}, 
                                       timeout=5)
                if response.status_code in [200, 422]:  # 422 - validation error, но эндпоинт существует
                    print(f"  ✅ {endpoint} доступен")
                else:
                    print(f"  ⚠️  {endpoint} вернул статус {response.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"  ❌ {endpoint} недоступен (сервер не отвечает)")
            except Exception as e:
                print(f"  ❌ {endpoint} ошибка: {e}")

def check_google_sheets_config():
    """Проверка конфигурации Google Sheets"""
    config_files = [
        'client_secret.json',
        'token.pickle'
    ]
    
    print("\n🔍 Проверка конфигурации Google Sheets:")
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"  ✅ {config_file} найден")
        else:
            print(f"  ❌ {config_file} не найден")

def check_dependencies():
    """Проверка зависимостей Python"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'requests',
        'gspread',
        'google-auth',
        'openpyxl'
    ]
    
    print("\n🔍 Проверка Python зависимостей:")
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} не установлен")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 Для установки недостающих пакетов выполните:")
        print(f"pip install {' '.join(missing_packages)}")

def check_frontend_build():
    """Проверка сборки фронтенда"""
    frontend_dir = Path('frontend')
    
    if not frontend_dir.exists():
        print("❌ Папка frontend не найдена")
        return False
    
    package_json = frontend_dir / 'package.json'
    node_modules = frontend_dir / 'node_modules'
    
    if package_json.exists():
        print("✅ package.json найден")
    else:
        print("❌ package.json не найден")
        return False
    
    if node_modules.exists():
        print("✅ node_modules найден")
    else:
        print("❌ node_modules не найден - выполните 'npm install' в папке frontend")
        return False
    
    return True

def main():
    print("🔧 Диагностика функционала GeoMethodsPanel\n")
    
    # Проверка файлов
    print("1. Проверка файлов:")
    check_frontend_files()
    
    # Проверка зависимостей
    check_dependencies()
    
    # Проверка API сервера
    print("\n2. Проверка API сервера:")
    api_running = check_api_server()
    
    if api_running:
        # Проверка эндпоинтов
        check_api_endpoints()
    
    # Проверка Google Sheets
    check_google_sheets_config()
    
    # Проверка фронтенда
    print("\n3. Проверка фронтенда:")
    check_frontend_build()
    
    print("\n" + "="*50)
    print("📋 РЕКОМЕНДАЦИИ ПО УСТРАНЕНИЮ ПРОБЛЕМ:")
    print("="*50)
    
    if not api_running:
        print("🚀 Запустите API сервер:")
        print("   cd /Users/dimalogin/Downloads/b2b-automaisation-tool-mvp")
        print("   python3 api_fastapi_backend.py")
    
    print("\n🌐 Запустите фронтенд (в отдельном терминале):")
    print("   cd /Users/dimalogin/Downloads/b2b-automaisation-tool-mvp/frontend")
    print("   npm install  # если node_modules отсутствует")
    print("   npm start")
    
    print("\n🔑 Для работы экспорта в Google Sheets убедитесь что:")
    print("   - client_secret.json содержит корректные данные API")
    print("   - token.pickle создан после первой авторизации")
    
    print("\n🐛 Если проблемы остаются, проверьте:")
    print("   - Консоль браузера (F12) на наличие JavaScript ошибок")
    print("   - Network вкладку для проверки HTTP запросов")
    print("   - Логи API сервера в терминале")

if __name__ == "__main__":
    main()
