# 🤖 Настройка Telegram Бота для уведомлений о Google Sheets

## 📋 Описание

Telegram бот автоматически отправляет уведомления в чат/канал при создании новых Google Sheets файлов через систему экспорта.

## 🚀 Быстрая настройка

### 1. Создание бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Выберите имя для бота (например: "B2B Sheets Notifier")
4. Выберите username (например: "b2b_sheets_bot")
5. Скопируйте **токен бота** (например: `1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ`)

### 2. Получение Chat ID

#### Для личных сообщений:
1. Напишите боту любое сообщение
2. Откройте в браузере: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Найдите `"chat":{"id": ВАШЕ_ID}` (например: `123456789`)

#### Для группы/канала:
1. Добавьте бота в группу/канал
2. Дайте боту права администратора (для каналов)
3. Отправьте любое сообщение в группу/канал
4. Откройте: `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. Найдите `"chat":{"id": CHAT_ID}` (например: `-1001234567890`)

### 3. Установка зависимостей

```bash
# В виртуальном окружении
source myvenv/bin/activate
pip install -r requirements_telegram.txt
```

### 4. Настройка переменных окружения

```bash
# Добавьте в ~/.bashrc или ~/.zshrc
export TELEGRAM_BOT_TOKEN='1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ'
export TELEGRAM_CHAT_ID='-1001234567890'

# Или установите для текущей сессии
export TELEGRAM_BOT_TOKEN='ваш_токен'
export TELEGRAM_CHAT_ID='ваш_chat_id'
```

### 5. Тестирование

```bash
# Тест подключения
python telegram_bot.py

# Тест конфигурации
python telegram_config.py
```

## 🔧 Альтернативная настройка (в коде)

Если не хотите использовать переменные окружения:

```python
# В начале api_fastapi_backend.py добавьте:
from telegram_config import TelegramConfig

# Установите учетные данные
TelegramConfig.set_credentials(
    bot_token='1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    chat_id='-1001234567890'
)
```

## 📊 Типы уведомлений

Бот отправляет уведомления для всех типов экспорта:

### 1. Одиночный GEO экспорт
```
🚀 Новый Google Sheets файл создан!

📋 Детали:
• Проект: Rolling
• Тип: Single Export
• Окружение: PROD
• GEO: DE
• Время: 2025-10-20 13:45:30

🔗 Ссылка: Открыть Google Sheets
✅ Файл готов к использованию!
```

### 2. Multi-GEO экспорт
```
🚀 Новый Google Sheets файл создан!

📋 Детали:
• Проект: SpinEmpire
• Тип: Multi Export
• Окружение: PROD
• Время: 2025-10-20 13:45:30

🔗 Ссылка: Открыть Google Sheets
✅ Файл готов к использованию!
```

### 3. Full Project экспорт
```
🚀 Новый Google Sheets файл создан!

📋 Детали:
• Проект: Ritzo
• Тип: Full Export
• Окружение: STAGE
• Время: 2025-10-20 13:45:30

🔗 Ссылка: Открыть Google Sheets
✅ Файл готов к использованию!
```

## 🔒 Безопасность

- Токен бота держите в секрете
- Используйте переменные окружения вместо хардкода
- Ограничьте доступ к боту только нужным пользователям
- Для каналов используйте приватные каналы

## 🐛 Устранение неполадок

### Бот не отправляет сообщения
1. Проверьте токен бота
2. Проверьте Chat ID
3. Убедитесь что бот добавлен в группу/канал
4. Проверьте права администратора (для каналов)

### Ошибки в логах
```bash
# Проверьте логи FastAPI
tail -f logs/api.log

# Или в консоли при запуске uvicorn
```

### Тестирование подключения
```bash
python -c "
from telegram_config import TelegramConfig
print('Настроен:', TelegramConfig.is_configured())
print('Token:', TelegramConfig.get_bot_token()[:10] + '...' if TelegramConfig.get_bot_token() else 'НЕТ')
print('Chat ID:', TelegramConfig.get_chat_id())
"
```

## ✨ Готово!

После настройки бот будет автоматически отправлять уведомления при каждом создании Google Sheets файла через систему экспорта.
