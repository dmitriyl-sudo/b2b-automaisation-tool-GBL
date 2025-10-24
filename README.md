# 🚀 B2B Automation Tool

**Комплексный инструмент для автоматизации работы с платежными системами и экспорта данных в Google Sheets**

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![React](https://img.shields.io/badge/React-18+-blue.svg)
![Status](https://img.shields.io/badge/Status-Production-brightgreen.svg)

## 📋 Описание

B2B Automation Tool - это мощная система для автоматизации работы с различными платежными проектами (Ritzo, Rolling, Vegazone, Glitchspin и др.). Инструмент позволяет:

- 🔍 **Извлекать данные** о платежных методах из различных проектов
- 📊 **Экспортировать данные** в Excel и Google Sheets
- 🤖 **Автоматизировать процессы** через Telegram бота
- 🌍 **Поддерживать множественные GEO** и валюты
- 🔄 **Синхронизировать данные** между различными окружениями

## 🏗️ Архитектура

```
├── 🖥️  Backend (FastAPI)     - API сервер и бизнес-логика
├── 🌐 Frontend (React)       - Веб-интерфейс пользователя  
├── 🤖 Telegram Bot          - Автоматизация и уведомления
├── 📊 Google Sheets API     - Экспорт и синхронизация данных
└── 🔧 Utilities             - Вспомогательные инструменты
```

## ⚡ Быстрый старт

### 1️⃣ Клонирование репозитория

```bash
git clone https://github.com/dmitriyl-sudo/b2b-automaisation-tool-GBL.git
cd b2b-automaisation-tool-GBL
```

### 2️⃣ Установка зависимостей Backend

```bash
# Создание виртуального окружения
python3 -m venv myvenv
source myvenv/bin/activate  # Linux/Mac
# или
myvenv\Scripts\activate     # Windows

# Установка Python зависимостей
pip install -r requirements.txt

# Дополнительные зависимости (если нужны)
pip install nest-asyncio python-telegram-bot google-api-python-client
```

### 3️⃣ Установка зависимостей Frontend

```bash
cd frontend
npm install
cd ..
```

### 4️⃣ Настройка конфигурации

Создайте необходимые конфигурационные файлы:

```bash
# Скопируйте примеры конфигураций
cp telegram_config.py.example telegram_config.py
cp credentials.json.example credentials.json

# Отредактируйте конфигурации под ваши нужды
```

## 🚀 Запуск системы

### Backend API Server

```bash
# Активация виртуального окружения
source myvenv/bin/activate

# Запуск FastAPI сервера
python api_fastapi_backend.py

# Сервер будет доступен на http://localhost:8000
```

### Frontend React App

```bash
cd frontend

# Development режим
npm start
# Приложение будет доступно на http://localhost:3000

# Production сборка
npm run build
```

### Telegram Bot

```bash
# Активация виртуального окружения
source myvenv/bin/activate

# Запуск бота
python telegram_bot_fixed.py

# Или через скрипт
chmod +x launch_telegram_bot.sh
./launch_telegram_bot.sh
```

## 📚 Использование

### 🌐 Веб-интерфейс

1. **Откройте браузер** → `http://localhost:3000`
2. **Выберите проект** (Ritzo, Rolling, Vegazone, etc.)
3. **Выберите GEO** (DE, IT, NZ, CH_CHF, etc.)
4. **Выберите окружение** (prod/stage)
5. **Нажмите "Load GEO Methods"** для получения данных
6. **Экспортируйте** в Excel или Google Sheets

### 🤖 Telegram Bot

Доступные команды:

```
/start    - Приветствие и список команд
/today    - Статистика экспортов за сегодня  
/projects - Все проекты с последними ссылками
/help     - Справка по командам
```

### 🔧 API Endpoints

```bash
# Получение списка GEO групп
GET http://localhost:8000/geo-groups

# Получение методов для конкретного GEO
POST http://localhost:8000/get-methods-only
{
  "project": "Ritzo",
  "geo": "DE", 
  "env": "prod"
}

# Экспорт в Google Sheets
POST http://localhost:8000/export-to-sheets
{
  "project": "Rolling",
  "geo": "IT",
  "env": "prod",
  "export_type": "single"
}
```

## 🗂️ Структура проекта

```
b2b-automaisation-tool-GBL/
├── 📁 frontend/                 # React приложение
│   ├── src/
│   │   ├── components/         # React компоненты
│   │   ├── panels/            # Панели интерфейса
│   │   └── App.js             # Главный компонент
│   ├── public/                # Статические файлы
│   └── package.json           # NPM зависимости
├── 📁 extractors/              # Экстракторы данных
│   ├── base_extractor.py      # Базовый класс
│   ├── ritzo_extractor.py     # Ritzo проект
│   ├── rolling_extractor.py   # Rolling проект
│   └── vegazone_extractor.py  # Vegazone проект
├── 📁 utils/                   # Утилиты
│   ├── excel_utils.py         # Работа с Excel
│   ├── google_drive.py        # Google Sheets API
│   └── export_logger.py       # Логирование экспортов
├── 📁 archive/                 # Архив и тесты
│   ├── tests/                 # Тестовые файлы
│   └── scripts/               # Вспомогательные скрипты
├── 📄 api_fastapi_backend.py   # FastAPI сервер
├── 📄 main.py                  # Основная конфигурация
├── 📄 telegram_bot_fixed.py    # Telegram бот
├── 📄 delete_column.py         # Утилита удаления колонок
├── 📄 requirements.txt         # Python зависимости
└── 📄 .gitignore              # Git исключения
```

## ⚙️ Конфигурация

### Основные настройки (main.py)

```python
# Группы аккаунтов по GEO
geo_groups = {
    "DE": ["account1", "account2", ...],
    "IT": ["account3", "account4", ...],
    # ...
}

# Специальные аккаунты для проектов
VEGASZONE_EXTRA_GEOS = {
    "CH_CHF": ["special_account1", "special_account2", ...]
}

# Список проектов
site_list = [
    {
        "name": "Ritzo",
        "stage_url": "https://stage.ritzo.com",
        "prod_url": "https://ritzo.com"
    }
    # ...
]
```

### Telegram конфигурация

```python
# telegram_config.py
class TelegramConfig:
    BOT_TOKEN = "YOUR_BOT_TOKEN"
    CHAT_ID = "YOUR_CHAT_ID"
```

### Google Sheets API

1. **Создайте проект** в Google Cloud Console
2. **Включите Google Sheets API**
3. **Создайте Service Account**
4. **Скачайте credentials.json**
5. **Поместите файл** в корень проекта

## 🔧 Дополнительные утилиты

### Удаление колонок из Google Sheets

```bash
# Отредактируйте ID таблицы в файле
nano delete_column.py

# Запустите скрипт
python delete_column.py
```

### Тестирование системы

```bash
# Запуск тестов из архива
python archive/tests/test_full_extractors.py
```

## 🐛 Решение проблем

### Backend не запускается

```bash
# Проверьте виртуальное окружение
source myvenv/bin/activate
pip install -r requirements.txt

# Проверьте порт 8000
lsof -ti:8000
kill -9 [PID]
```

### Frontend не загружается

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

### Telegram бот не отвечает

```bash
# Проверьте процесс
ps aux | grep telegram_bot_fixed

# Перезапустите бота
kill -9 [PID]
python telegram_bot_fixed.py
```

### Google Sheets ошибки

1. **Проверьте credentials.json**
2. **Убедитесь что Service Account имеет доступ**
3. **Проверьте квоты API**

## 📊 Поддерживаемые проекты

| Проект | Stage URL | Prod URL | Статус |
|--------|-----------|----------|--------|
| 🎰 Ritzo | stage.ritzo.com | ritzo.com | ✅ |
| 🎲 Rolling | stage.rolling.com | rolling.com | ✅ |
| 🎯 Vegazone | stage.vegazone.com | vegazone.com | ✅ |
| ⚡ Glitchspin | stage.glitchspin.com | glitchspin.com | ✅ |
| 🎪 Spinempire | stage.spinempire.com | spinempire.com | ✅ |

## 🌍 Поддерживаемые GEO

- 🇩🇪 **DE** - Германия (EUR)
- 🇮🇹 **IT** - Италия (EUR)  
- 🇳🇿 **NZ** - Новая Зеландия (NZD)
- 🇨🇭 **CH_CHF** - Швейцария (CHF)
- 🇨🇭 **CH_EUR** - Швейцария (EUR)
- 🇳🇴 **NO_NOK** - Норвегия (NOK)
- 🇭🇺 **HU_HUF** - Венгрия (HUF)
- 🇦🇺 **AU_AUD** - Австралия (AUD)
- 🇨🇦 **CA_CAD** - Канада (CAD)

## 🔐 Безопасность

- ✅ **Credentials файлы** исключены из git
- ✅ **API ключи** хранятся в конфигурациях
- ✅ **.pem файлы** игнорируются
- ✅ **Логи** не содержат чувствительных данных

## 📈 Мониторинг

### Логи системы

```bash
# Backend логи
tail -f bot_updated.log

# Export логи  
cat exports_log.json | jq

# Telegram бот логи
tail -f bot.log
```

### Статистика использования

- 📊 **Экспорты отслеживаются** в `exports_log.json`
- 📈 **Telegram команды** логируются
- 🔍 **API вызовы** записываются в логи

## 🤝 Поддержка

При возникновении проблем:

1. **Проверьте логи** системы
2. **Убедитесь в правильности** конфигурации  
3. **Проверьте доступность** внешних API
4. **Создайте issue** в репозитории

## 📝 Changelog

### v2.0.0 (2024-10-24)
- ✅ Исправлена логика CH_CHF аккаунтов для Vegazone
- ✅ Улучшены команды Telegram бота (/projects, /today)
- ✅ Перемещены тесты в archive/tests/
- ✅ Добавлен .gitignore для .pem файлов
- ✅ Создан подробный README

### v1.0.0 (2024-10-20)
- 🚀 Первый релиз системы
- ✅ Базовая функциональность экспорта
- ✅ Поддержка основных проектов
- ✅ Telegram бот интеграция

## 📄 Лицензия

Этот проект предназначен для внутреннего использования.

---

**🚀 Готово к работе! Следуйте инструкциям выше для развертывания системы.**
